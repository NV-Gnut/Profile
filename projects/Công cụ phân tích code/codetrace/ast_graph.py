from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GraphNode:
    id: str
    file: Path
    line: int
    column: int
    symbol: str
    kind: str
    scope: str
    code: str
    detail: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    kind: str
    detail: str


@dataclass
class SymbolGraph:
    symbol: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    parser: str = "Python AST"

    @property
    def definitions(self) -> list[GraphNode]:
        return [node for node in self.nodes if node.symbol == self.symbol and node.kind in {
            "ASSIGNMENT", "PARAMETER", "FUNCTION", "IMPORT",
        }]

    @property
    def usages(self) -> list[GraphNode]:
        return [node for node in self.nodes if node.symbol == self.symbol and node.kind in {
            "READ", "CALL",
        }]


class PythonProgramDependencyGraph:
    """Builds a lightweight inter-procedural data/call dependency graph from Python AST."""

    SOURCE_CALLS = {
        "input", "os.getenv", "os.environ.get", "request.args.get", "request.form.get",
        "request.get_json", "sys.stdin.read", "sys.stdin.readline",
    }

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.definitions: dict[tuple[Path, str, str], list[str]] = {}
        self.functions: dict[str, str] = {}
        self.parameters: dict[str, list[str]] = {}
        self.returns: dict[str, list[str]] = {}
        self.pending_reads: list[tuple[str, Path, str, str, int]] = []
        self.pending_calls: list[tuple[str, str]] = []
        self.pending_imports: list[tuple[str, str, str]] = []

    def build(self, files: list[Path]) -> "PythonProgramDependencyGraph":
        parsed: list[tuple[Path, str, ast.Module]] = []
        for path in files:
            if path.suffix.lower() != ".py":
                continue
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
                parsed.append((path, source, ast.parse(source, filename=str(path))))
            except (OSError, SyntaxError):
                continue
        for path, source, tree in parsed:
            _FunctionCollector(self, path, source).visit(tree)
        for path, source, tree in parsed:
            _DependencyVisitor(self, path, source).visit(tree)
        self._link_pending()
        return self

    def query(self, symbol: str, upstream_depth: int = 7, downstream_depth: int = 7) -> SymbolGraph:
        starts = {node.id for node in self.nodes.values() if node.symbol == symbol}
        if not starts:
            return SymbolGraph(symbol=symbol)
        incoming: dict[str, list[GraphEdge]] = {}
        outgoing: dict[str, list[GraphEdge]] = {}
        for edge in self.edges:
            incoming.setdefault(edge.target, []).append(edge)
            outgoing.setdefault(edge.source, []).append(edge)

        included = set(starts)
        frontier = set(starts)
        # Walk both directions together. This includes a callee definition discovered
        # from a downstream call as well as the upstream value returned by that callee.
        for _ in range(max(upstream_depth, downstream_depth)):
            frontier = (
                {edge.source for node_id in frontier for edge in incoming.get(node_id, [])}
                | {edge.target for node_id in frontier for edge in outgoing.get(node_id, [])}
            ) - included
            included.update(frontier)
            if not frontier:
                break
        nodes = sorted(
            (self.nodes[node_id] for node_id in included),
            key=lambda node: (str(node.file), node.line, node.column, node.kind),
        )
        edges = [edge for edge in self.edges if edge.source in included and edge.target in included]
        return SymbolGraph(symbol=symbol, nodes=nodes[:300], edges=edges[:600])

    def add_node(self, path: Path, ast_node: ast.AST, symbol: str, kind: str,
                 scope: str, source: str, detail: str) -> str:
        line = getattr(ast_node, "lineno", 1)
        column = getattr(ast_node, "col_offset", 0) + 1
        node_id = f"{path}:{line}:{column}:{kind}:{symbol}:{len(self.nodes)}"
        code = ast.get_source_segment(source, ast_node) or source.splitlines()[line - 1].strip()
        self.nodes[node_id] = GraphNode(
            node_id, path, line, column, symbol, kind, scope, code.strip(), detail,
        )
        return node_id

    def add_edge(self, source: str, target: str, kind: str, detail: str) -> None:
        edge = GraphEdge(source, target, kind, detail)
        if source != target and edge not in self.edges:
            self.edges.append(edge)

    def register_definition(self, path: Path, scope: str, symbol: str, node_id: str) -> None:
        self.definitions.setdefault((path, scope, symbol), []).append(node_id)

    def resolve_definition(self, path: Path, scope: str, symbol: str, line: int) -> str | None:
        scopes = [scope]
        while "." in scopes[-1]:
            scopes.append(scopes[-1].rsplit(".", 1)[0])
        if "<module>" not in scopes:
            scopes.append("<module>")
        for candidate_scope in scopes:
            ids = self.definitions.get((path, candidate_scope, symbol), [])
            preceding = [node_id for node_id in ids if self.nodes[node_id].line <= line]
            if preceding:
                return max(preceding, key=lambda node_id: self.nodes[node_id].line)
        return None

    def _link_pending(self) -> None:
        for read_id, path, scope, symbol, line in self.pending_reads:
            definition = self.resolve_definition(path, scope, symbol, line)
            if definition:
                self.add_edge(definition, read_id, "READS", f"Đọc giá trị của '{symbol}'")
        for call_id, function_name in self.pending_calls:
            function_id = self.functions.get(function_name)
            if function_id:
                self.add_edge(function_id, call_id, "CALLS", f"Gọi hàm '{function_name}'")
                for return_id in self.returns.get(function_name, []):
                    self.add_edge(return_id, call_id, "RETURNS_TO", f"Giá trị trả về từ '{function_name}'")
        for import_id, module, original_name in self.pending_imports:
            candidates = []
            module_path = module.replace(".", "/")
            for (path, scope, symbol), ids in self.definitions.items():
                normalized = path.with_suffix("").as_posix()
                if (scope == "<module>" and symbol == original_name
                        and (normalized.endswith(module_path) or path.stem == module.split(".")[-1])):
                    candidates.extend(ids)
            if candidates:
                origin = max(candidates, key=lambda node_id: self.nodes[node_id].line)
                self.add_edge(origin, import_id, "IMPORTS", f"Import '{original_name}' từ module '{module}'")


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self, graph: PythonProgramDependencyGraph, path: Path, source: str) -> None:
        self.graph, self.path, self.source = graph, path, source
        self.scope = "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old = self.scope
        self.scope = f"{old}.{node.name}"
        self.generic_visit(node)
        self.scope = old

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        function_id = self.graph.add_node(
            self.path, node, node.name, "FUNCTION", self.scope, self.source,
            f"Định nghĩa hàm '{node.name}' trong scope {self.scope}",
        )
        self.graph.functions.setdefault(node.name, function_id)
        for decorator in node.decorator_list:
            endpoint = self._decorator_endpoint(decorator)
            if endpoint:
                method, route = endpoint
                endpoint_id = self.graph.add_node(
                    self.path, decorator, f"{method} {route}", "ENDPOINT", self.scope, self.source,
                    f"Endpoint {method} {route} được xử lý bởi hàm '{node.name}'",
                )
                self.graph.add_edge(endpoint_id, function_id, "HANDLES",
                                    f"{method} {route} gọi handler '{node.name}'")
        function_scope = f"{self.scope}.{node.name}"
        parameter_ids = []
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            parameter_id = self.graph.add_node(
                self.path, argument, argument.arg, "PARAMETER", function_scope, self.source,
                f"Tham số '{argument.arg}' của hàm '{node.name}'",
            )
            self.graph.register_definition(self.path, function_scope, argument.arg, parameter_id)
            self.graph.add_edge(function_id, parameter_id, "DECLARES",
                                f"Hàm '{node.name}' khai báo tham số '{argument.arg}'")
            parameter_ids.append(parameter_id)
        self.graph.parameters[node.name] = parameter_ids
        old = self.scope
        self.scope = function_scope
        for child in node.body:
            self.visit(child)
        self.scope = old

    visit_AsyncFunctionDef = visit_FunctionDef

    @staticmethod
    def _decorator_endpoint(node: ast.AST) -> tuple[str, str] | None:
        if not isinstance(node, ast.Call):
            return None
        action = _DependencyVisitor._call_name(node.func).split(".")[-1].lower()
        supported = {"route", "get", "post", "put", "patch", "delete", "options", "head", "websocket"}
        if action not in supported or not node.args:
            return None
        route_node = node.args[0]
        if not isinstance(route_node, ast.Constant) or not isinstance(route_node.value, str):
            return None
        if action == "route":
            methods = []
            for keyword in node.keywords:
                if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                    methods = [
                        str(item.value).upper() for item in keyword.value.elts
                        if isinstance(item, ast.Constant)
                    ]
            method = "|".join(methods) if methods else "ANY"
        else:
            method = action.upper()
        return method, route_node.value


class _DependencyVisitor(ast.NodeVisitor):
    def __init__(self, graph: PythonProgramDependencyGraph, path: Path, source: str) -> None:
        self.graph, self.path, self.source = graph, path, source
        self.scope = "<module>"
        self.function = ""
        self.function_id: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old = self.scope
        self.scope = f"{old}.{node.name}"
        for child in node.body:
            self.visit(child)
        self.scope = old

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_scope, old_function, old_function_id = self.scope, self.function, self.function_id
        self.scope = f"{self.scope}.{node.name}"
        self.function = node.name
        self.function_id = self.graph.functions.get(node.name)
        for child in node.body:
            self.visit(child)
        self.scope, self.function, self.function_id = old_scope, old_function, old_function_id

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            local_name = alias.asname or alias.name
            import_id = self.graph.add_node(
                self.path, node, local_name, "IMPORT", self.scope, self.source,
                f"Import '{alias.name}' từ module '{module}'",
            )
            self.graph.register_definition(self.path, self.scope, local_name, import_id)
            self._connect_scope(import_id, local_name)
            self.graph.pending_imports.append((import_id, module, alias.name))

    def visit_If(self, node: ast.If) -> None:
        self.expression_origins(node.test)
        for child in (*node.body, *node.orelse):
            self.visit(child)

    def visit_While(self, node: ast.While) -> None:
        self.expression_origins(node.test)
        for child in (*node.body, *node.orelse):
            self.visit(child)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.expression_origins(node.test)
        if node.msg:
            self.expression_origins(node.msg)

    def visit_For(self, node: ast.For) -> None:
        origins = self.expression_origins(node.iter)
        for name_node in self._target_names(node.target):
            definition = self.graph.add_node(
                self.path, name_node, name_node.id, "ASSIGNMENT", self.scope, self.source,
                f"'{name_node.id}' nhận từng giá trị từ vòng lặp",
            )
            self.graph.register_definition(self.path, self.scope, name_node.id, definition)
            self._connect_scope(definition, name_node.id)
            for origin in origins:
                self.graph.add_edge(origin, definition, "ITERATES_TO", f"Giá trị lặp vào '{name_node.id}'")
        for child in (*node.body, *node.orelse):
            self.visit(child)

    visit_AsyncFor = visit_For

    def visit_Assign(self, node: ast.Assign) -> None:
        origins = self.expression_origins(node.value)
        for target in node.targets:
            for name_node in self._target_names(target):
                definition = self.graph.add_node(
                    self.path, name_node, name_node.id, "ASSIGNMENT", self.scope, self.source,
                    f"'{name_node.id}' được tạo/cập nhật từ biểu thức: {ast.unparse(node.value)}",
                )
                self.graph.register_definition(self.path, self.scope, name_node.id, definition)
                self._connect_scope(definition, name_node.id)
                for origin in origins:
                    self.graph.add_edge(origin, definition, "FLOWS_TO",
                                        f"Dữ liệu truyền vào '{name_node.id}'")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and isinstance(node.target, ast.Name):
            origins = self.expression_origins(node.value)
            definition = self.graph.add_node(
                self.path, node.target, node.target.id, "ASSIGNMENT", self.scope, self.source,
                f"'{node.target.id}' được khai báo và gán từ: {ast.unparse(node.value)}",
            )
            self.graph.register_definition(self.path, self.scope, node.target.id, definition)
            self._connect_scope(definition, node.target.id)
            for origin in origins:
                self.graph.add_edge(origin, definition, "FLOWS_TO", f"Dữ liệu truyền vào '{node.target.id}'")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Name):
            origins = self.expression_origins(node.value)
            previous = self.graph.resolve_definition(self.path, self.scope, node.target.id, node.lineno)
            definition = self.graph.add_node(
                self.path, node.target, node.target.id, "ASSIGNMENT", self.scope, self.source,
                f"'{node.target.id}' được cập nhật bằng {type(node.op).__name__}",
            )
            self.graph.register_definition(self.path, self.scope, node.target.id, definition)
            self._connect_scope(definition, node.target.id)
            if previous:
                origins.append(previous)
            for origin in origins:
                self.graph.add_edge(origin, definition, "FLOWS_TO", f"Cập nhật '{node.target.id}'")

    def visit_Expr(self, node: ast.Expr) -> None:
        self.expression_origins(node.value)

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is None:
            return
        origins = self.expression_origins(node.value)
        return_id = self.graph.add_node(
            self.path, node, self.function or "<module>", "RETURN", self.scope, self.source,
            f"Giá trị trả về của hàm '{self.function}'",
        )
        self._connect_scope(return_id, self.function or "<module>")
        for origin in origins:
            self.graph.add_edge(origin, return_id, "RETURNS", "Dữ liệu đi vào giá trị trả về")
        if self.function:
            self.graph.returns.setdefault(self.function, []).append(return_id)

    def expression_origins(self, node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):
            read_id = self.graph.add_node(
                self.path, node, node.id, "READ", self.scope, self.source,
                f"Đọc biến '{node.id}' trong scope {self.scope}",
            )
            self._connect_scope(read_id, node.id)
            definition = self.graph.resolve_definition(self.path, self.scope, node.id, node.lineno)
            if definition:
                self.graph.add_edge(definition, read_id, "READS", f"Đọc giá trị của '{node.id}'")
            else:
                self.graph.pending_reads.append((read_id, self.path, self.scope, node.id, node.lineno))
            return [read_id]
        if isinstance(node, ast.Constant):
            literal = repr(node.value)
            return [self.graph.add_node(
                self.path, node, literal, "LITERAL", self.scope, self.source,
                f"Giá trị cố định {literal}",
            )]
        if isinstance(node, ast.Call):
            function_name = self._call_name(node.func)
            django_endpoint = (
                function_name in {"path", "re_path"}
                and bool(node.args)
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            )
            kind = (
                "ENDPOINT" if django_endpoint else
                "SOURCE" if function_name in self.graph.SOURCE_CALLS else "CALL"
            )
            display_symbol = (
                f"ROUTE /{str(node.args[0].value).lstrip('/')}" if django_endpoint
                else function_name
            )
            call_id = self.graph.add_node(
                self.path, node, display_symbol, kind, self.scope, self.source,
                (f"Django URL route '{node.args[0].value}'" if django_endpoint
                 else f"Nguồn dữ liệu bên ngoài: {function_name}" if kind == "SOURCE"
                 else f"Lời gọi hàm '{function_name}'"),
            )
            self._connect_scope(call_id, display_symbol)
            if django_endpoint and len(node.args) > 1 and isinstance(node.args[1], ast.Name):
                handler_id = self.graph.functions.get(node.args[1].id)
                if handler_id:
                    self.graph.add_edge(call_id, handler_id, "HANDLES",
                                        f"Route gọi handler '{node.args[1].id}'")
            self.graph.pending_calls.append((call_id, function_name.split(".")[-1]))
            positional_origins = [self.expression_origins(argument) for argument in node.args]
            keyword_origins = [self.expression_origins(keyword.value) for keyword in node.keywords]
            argument_origins = [
                origin for origins in (*positional_origins, *keyword_origins) for origin in origins
            ]
            for origin in argument_origins:
                self.graph.add_edge(origin, call_id, "ARGUMENT", f"Truyền dữ liệu vào '{function_name}'")
            parameters = self.graph.parameters.get(function_name.split(".")[-1], [])
            for origins, parameter in zip(positional_origins, parameters):
                for origin in origins:
                    self.graph.add_edge(origin, parameter, "PASSES_TO",
                                        f"Đối số truyền vào tham số '{self.graph.nodes[parameter].symbol}'")
            return [call_id]
        origins: list[str] = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.Load, ast.Store, ast.Del, ast.operator, ast.unaryop, ast.cmpop)):
                continue
            origins.extend(self.expression_origins(child))
        return list(dict.fromkeys(origins))

    @staticmethod
    def _target_names(node: ast.AST) -> list[ast.Name]:
        if isinstance(node, ast.Name):
            return [node]
        if isinstance(node, (ast.Tuple, ast.List)):
            return [name for item in node.elts for name in _DependencyVisitor._target_names(item)]
        return []

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = _DependencyVisitor._call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ast.unparse(node)

    def _connect_scope(self, node_id: str, symbol: str) -> None:
        if self.function_id:
            self.graph.add_edge(
                self.function_id, node_id, "CONTAINS",
                f"Handler/hàm '{self.function}' chứa thao tác với '{symbol}'",
            )
