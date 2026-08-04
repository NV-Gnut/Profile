from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path

from .models import Finding, Rule, TraceStep
from .rules import BUILTIN_RULES
from .ast_graph import PythonProgramDependencyGraph, SymbolGraph


EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".php": "php", ".java": "java",
}
IGNORED_DIRS = {".git", ".idea", ".vscode", "node_modules", "vendor", "dist", "build", "__pycache__"}
MAX_FILE_SIZE = 2 * 1024 * 1024
ASSIGNMENT = re.compile(
    r"(?:\b(?:var|let|const|String|Object|int|long|final)\s+)?"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*=(?!=)\s*(?P<expr>.+)"
)


class Analyzer:
    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self.rules = list(rules or BUILTIN_RULES)

    @staticmethod
    def language_for(path: Path) -> str | None:
        return EXTENSIONS.get(path.suffix.lower())

    def collect_files(self, target: Path) -> list[Path]:
        if target.is_file():
            return [target] if self.language_for(target) else []
        return sorted(
            path for path in target.rglob("*")
            if path.is_file()
            and self.language_for(path)
            and not any(part in IGNORED_DIRS for part in path.parts)
            and path.stat().st_size <= MAX_FILE_SIZE
        )

    def scan(self, target: Path) -> list[Finding]:
        findings: list[Finding] = []
        for path in self.collect_files(target):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            findings.extend(self.scan_text(path, text))
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        return sorted(findings, key=lambda f: (order.get(f.severity, 9), str(f.file), f.line))

    def trace_symbol_graph(self, target: Path, symbol: str) -> SymbolGraph:
        """Return an AST-derived inter-procedural dependency graph for a Python symbol."""
        symbol = symbol.strip()
        if not re.fullmatch(r"[A-Za-z_][\w]*", symbol):
            raise ValueError("Tên cần trace phải là định danh Python, ví dụ: FLAG hoặc execute_query")
        python_files = [path for path in self.collect_files(target) if path.suffix.lower() == ".py"]
        if not python_files:
            raise ValueError(
                "Reverse trace bằng AST hiện hỗ trợ Python. Target hiện tại không có file .py."
            )
        return PythonProgramDependencyGraph().build(python_files).query(symbol)

    def scan_text(self, path: Path, text: str) -> list[Finding]:
        language = self.language_for(path)
        if not language:
            return []
        lines = text.splitlines()
        findings: list[Finding] = []
        for rule in self.rules:
            if language not in rule.languages:
                continue
            findings.extend(self._scan_direct(path, lines, rule))
            if rule.sources and rule.sinks:
                if language == "python":
                    findings.extend(self._scan_python_ast_flow(path, text, rule))
                else:
                    findings.extend(self._scan_flow(path, lines, rule))
        return self._deduplicate(findings)

    def _scan_python_ast_flow(self, path: Path, text: str, rule: Rule) -> list[Finding]:
        """Scope-aware Python taint analysis. AST boundaries prevent cross-function flows."""
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            return self._scan_flow(path, text.splitlines(), rule)
        source_patterns = [re.compile(pattern) for pattern in rule.sources]
        sink_patterns = [re.compile(pattern) for pattern in rule.sinks]
        sanitizer_patterns = [re.compile(pattern) for pattern in rule.sanitizers]
        results: list[Finding] = []

        def segment(node: ast.AST) -> str:
            return ast.get_source_segment(text, node) or ""

        def loaded_names(node: ast.AST) -> list[str]:
            return [
                child.id for child in ast.walk(node)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
            ]

        def target_names(node: ast.AST) -> list[str]:
            if isinstance(node, ast.Name):
                return [node.id]
            if isinstance(node, (ast.Tuple, ast.List)):
                return [name for item in node.elts for name in target_names(item)]
            return []

        def process(statements: list[ast.stmt], tainted: dict[str, list[TraceStep]]) -> None:
            for statement in statements:
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                analysis_node: ast.AST = statement
                if isinstance(statement, (ast.If, ast.While)):
                    analysis_node = statement.test
                elif isinstance(statement, (ast.For, ast.AsyncFor)):
                    analysis_node = statement.iter
                elif isinstance(statement, ast.Try):
                    analysis_node = ast.Pass()
                code = segment(analysis_node)
                sanitized = any(pattern.search(code) for pattern in sanitizer_patterns)
                sink_match = next((pattern.search(code) for pattern in sink_patterns
                                   if pattern.search(code)), None)
                used = [name for name in loaded_names(analysis_node) if name in tainted]
                source_match = next((pattern.search(code) for pattern in source_patterns
                                     if pattern.search(code)), None)
                if sink_match and not sanitized and (used or source_match):
                    if used:
                        variable = min(used, key=lambda name: len(tainted[name]))
                        trace = tainted[variable] + [
                            TraceStep(statement.lineno, "SINK", code.strip(),
                                      f"'{variable}' đi vào sink trong cùng AST scope")
                        ]
                    else:
                        trace = [
                            TraceStep(statement.lineno, "SOURCE", code.strip(), "Nguồn dữ liệu không tin cậy"),
                            TraceStep(statement.lineno, "SINK", code.strip(), "Nguồn truyền trực tiếp vào sink"),
                        ]
                    results.append(self._finding(
                        rule, path, statement.lineno,
                        getattr(statement, "col_offset", 0) + sink_match.start() + 1, code, trace,
                    ))

                assignments: list[tuple[list[str], ast.AST]] = []
                if isinstance(statement, ast.Assign):
                    assignments = [
                        ([name for target in statement.targets for name in target_names(target)], statement.value)
                    ]
                elif isinstance(statement, ast.AnnAssign) and statement.value:
                    assignments = [(target_names(statement.target), statement.value)]
                elif isinstance(statement, ast.AugAssign):
                    assignments = [(target_names(statement.target), statement.value)]
                for names, value in assignments:
                    expression = segment(value)
                    dependencies = [name for name in loaded_names(value) if name in tainted]
                    expression_source = any(pattern.search(expression) for pattern in source_patterns)
                    expression_safe = any(pattern.search(expression) for pattern in sanitizer_patterns)
                    for name in names:
                        if expression_safe:
                            tainted.pop(name, None)
                        elif expression_source:
                            tainted[name] = [
                                TraceStep(statement.lineno, "SOURCE", code.strip(),
                                          f"Nguồn không tin cậy gán vào '{name}'")
                            ]
                        elif dependencies:
                            parent = min(dependencies, key=lambda item: len(tainted[item]))
                            tainted[name] = tainted[parent] + [
                                TraceStep(statement.lineno, "PROPAGATION", code.strip(),
                                          f"'{parent}' truyền dữ liệu sang '{name}'")
                            ]
                        else:
                            tainted.pop(name, None)

                if isinstance(statement, ast.If):
                    left, right = dict(tainted), dict(tainted)
                    process(statement.body, left)
                    process(statement.orelse, right)
                    tainted.update(left)
                    tainted.update(right)
                elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                    branch = dict(tainted)
                    process(statement.body, branch)
                    process(statement.orelse, branch)
                    tainted.update(branch)
                elif isinstance(statement, ast.Try):
                    branch = dict(tainted)
                    process(statement.body, branch)
                    for handler in statement.handlers:
                        process(handler.body, branch)
                    process(statement.orelse, branch)
                    process(statement.finalbody, branch)
                    tainted.update(branch)

        process([node for node in tree.body if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )], {})
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                process(node.body, {})
        return results

    def _scan_direct(self, path: Path, lines: list[str], rule: Rule) -> list[Finding]:
        results = []
        patterns = [re.compile(pattern) for pattern in rule.direct_patterns]
        for number, line in enumerate(lines, 1):
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    step = TraceStep(number, "SINK", line.strip(), "Mẫu nguy hiểm được phát hiện trực tiếp")
                    results.append(self._finding(rule, path, number, match.start() + 1, line, [step]))
                    break
        return results

    def _scan_flow(self, path: Path, lines: list[str], rule: Rule) -> list[Finding]:
        source_patterns = [re.compile(p) for p in rule.sources]
        sink_patterns = [re.compile(p) for p in rule.sinks]
        sanitizer_patterns = [re.compile(p) for p in rule.sanitizers]
        tainted: dict[str, list[TraceStep]] = {}
        results: list[Finding] = []

        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "*")):
                continue
            source_match = next((p.search(line) for p in source_patterns if p.search(line)), None)
            assignment = ASSIGNMENT.search(line)
            sanitized = any(pattern.search(line) for pattern in sanitizer_patterns)

            if assignment:
                variable, expression = assignment.group("name"), assignment.group("expr")
                if sanitized:
                    tainted.pop(variable, None)
                elif source_match:
                    tainted[variable] = [
                        TraceStep(number, "SOURCE", stripped, f"Dữ liệu không tin cậy gán vào '{variable}'")
                    ]
                else:
                    parents = [name for name in tainted if self._contains_identifier(expression, name)]
                    if parents:
                        parent = min(parents, key=lambda name: len(tainted[name]))
                        tainted[variable] = tainted[parent] + [
                            TraceStep(number, "PROPAGATION", stripped, f"'{parent}' truyền dữ liệu sang '{variable}'")
                        ]

            sink_match = next((p.search(line) for p in sink_patterns if p.search(line)), None)
            if not sink_match or sanitized:
                continue
            used = [name for name in tainted if self._contains_identifier(line, name)]
            if used:
                variable = min(used, key=lambda name: len(tainted[name]))
                trace = tainted[variable] + [
                    TraceStep(number, "SINK", stripped, f"'{variable}' đi vào hàm/biểu thức nguy hiểm")
                ]
                results.append(self._finding(rule, path, number, sink_match.start() + 1, line, trace))
            elif source_match:
                trace = [
                    TraceStep(number, "SOURCE", stripped, "Nguồn dữ liệu không tin cậy"),
                    TraceStep(number, "SINK", stripped, "Nguồn được truyền trực tiếp vào sink"),
                ]
                results.append(self._finding(rule, path, number, sink_match.start() + 1, line, trace))
        return results

    @staticmethod
    def _contains_identifier(text: str, name: str) -> bool:
        return bool(re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", text))

    @staticmethod
    def _finding(rule: Rule, path: Path, line: int, column: int, code: str,
                 trace: list[TraceStep]) -> Finding:
        return Finding(
            rule_id=rule.id, rule_name=rule.name, severity=rule.severity,
            file=path, line=line, column=column, code=code.strip(),
            message=rule.message, recommendation=rule.recommendation,
            confidence=rule.confidence, cwe=rule.cwe,
            dataset_source=rule.dataset_source, trace=trace,
        )

    @staticmethod
    def _deduplicate(findings: list[Finding]) -> list[Finding]:
        unique: dict[tuple[str, Path, int], Finding] = {}
        for finding in findings:
            unique[(finding.rule_id, finding.file, finding.line)] = finding
        return list(unique.values())
