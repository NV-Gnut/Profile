import tempfile
import unittest
from pathlib import Path

from codetrace.engine import Analyzer
from codetrace.app import CodeTraceApp
from codetrace.rules import load_custom_rules


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_python_sql_injection_trace(self):
        code = """\
def search(request, cursor):
    term = request.args.get("q")
    query = "SELECT * FROM users WHERE name = '" + term + "'"
    cursor.execute(query)
"""
        findings = self.analyzer.scan_text(Path("sample.py"), code)
        sqli = next(f for f in findings if f.rule_id == "CT-SQLI-001")
        self.assertEqual(sqli.line, 4)
        self.assertEqual([step.kind for step in sqli.trace], ["SOURCE", "PROPAGATION", "SINK"])

    def test_sanitizer_stops_trace(self):
        code = """\
value = request.args.get("path")
safe = secure_filename(value)
open(safe)
"""
        findings = self.analyzer.scan_text(Path("sample.py"), code)
        self.assertFalse(any(f.rule_id == "CT-PATH-001" for f in findings))

    def test_direct_secret_detection(self):
        findings = self.analyzer.scan_text(Path("config.js"), 'const api_key = "1234567890";')
        self.assertTrue(any(f.rule_id == "CT-SECRET-001" for f in findings))

    def test_collect_files_ignores_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "src").mkdir()
            (root / "node_modules").mkdir()
            (root / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
            (root / "node_modules" / "lib.js").write_text("eval(x)", encoding="utf-8")
            files = self.analyzer.collect_files(root)
            self.assertEqual(files, [root / "src" / "app.py"])

    def test_ast_flag_graph_tracks_origin_reads_and_function_argument(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "challenge.py").write_text(
                "import os\n\n"
                "def reveal(value):\n"
                "    message = 'flag=' + value\n"
                "    return message\n\n"
                "FLAG = os.getenv('CTF_FLAG')\n"
                "copy = FLAG\n"
                "print(reveal(FLAG))\n",
                encoding="utf-8",
            )
            graph = self.analyzer.trace_symbol_graph(root, "FLAG")
            self.assertEqual(graph.parser, "Python AST")
            self.assertTrue(any(node.kind == "ASSIGNMENT" and node.line == 7
                                for node in graph.definitions))
            self.assertEqual(len([node for node in graph.usages if node.kind == "READ"]), 2)
            self.assertTrue(any(node.kind == "SOURCE" and node.symbol == "os.getenv"
                                for node in graph.nodes))
            self.assertTrue(any(edge.kind == "PASSES_TO" for edge in graph.edges))
            self.assertTrue(any(node.symbol == "message" and node.kind == "ASSIGNMENT"
                                for node in graph.nodes))

    def test_ast_graph_tracks_cross_file_import_and_condition_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "config.py").write_text("FLAG = 'demo-secret'\n", encoding="utf-8")
            (root / "app.py").write_text(
                "from config import FLAG\n"
                "if FLAG:\n"
                "    print(FLAG)\n",
                encoding="utf-8",
            )
            graph = self.analyzer.trace_symbol_graph(root, "FLAG")
            self.assertTrue(any(node.kind == "IMPORT" for node in graph.nodes))
            self.assertEqual(len([node for node in graph.nodes
                                  if node.kind == "READ" and node.symbol == "FLAG"]), 2)
            self.assertTrue(any(edge.kind == "IMPORTS" for edge in graph.edges))

    def test_ast_graph_reports_fastapi_endpoint_using_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "api.py").write_text(
                "import os\n"
                "FLAG = os.getenv('FLAG')\n\n"
                "@app.get('/api/flag')\n"
                "def read_flag():\n"
                "    return {'flag': FLAG}\n",
                encoding="utf-8",
            )
            graph = self.analyzer.trace_symbol_graph(root, "FLAG")
            endpoints = [node for node in graph.nodes if node.kind == "ENDPOINT"]
            self.assertEqual([node.symbol for node in endpoints], ["GET /api/flag"])
            self.assertTrue(any(edge.kind == "HANDLES" for edge in graph.edges))
            self.assertTrue(any(edge.kind == "CONTAINS" for edge in graph.edges))

    def test_simple_trace_excludes_unrelated_call_inside_handler(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "app.py").write_text(
                "import os\n"
                "FLAG = os.getenv('FLAG')\n\n"
                "def get_role_from_jwt(token):\n"
                "    return token\n\n"
                "@app.get('/duck')\n"
                "def handler(sid):\n"
                "    role = get_role_from_jwt(sid)\n"
                "    if role:\n"
                "        return FLAG\n",
                encoding="utf-8",
            )
            graph = self.analyzer.trace_symbol_graph(root, "FLAG")
            simple = CodeTraceApp._simple_trace_nodes(graph)
            symbols = {node.symbol for node in simple}
            self.assertIn("GET /duck", symbols)
            self.assertIn("handler", symbols)
            self.assertNotIn("get_role_from_jwt", symbols)

    def test_python_ast_taint_does_not_cross_function_scope(self):
        code = (
            "def collect(request):\n"
            "    command = request.args.get('cmd')\n"
            "    return command\n\n"
            "def unrelated():\n"
            "    os.system(command)\n"
        )
        findings = self.analyzer.scan_text(Path("scope.py"), code)
        self.assertFalse(any(finding.rule_id == "CT-CMD-001" for finding in findings))

    def test_curated_dataset_rule_detects_ssrf_with_metadata(self):
        dataset = load_custom_rules(Path(__file__).parent.parent / "datasets" / "security_rules.json")
        analyzer = Analyzer(dataset)
        code = (
            "def fetch(request):\n"
            "    url = request.query_params.get('url')\n"
            "    return requests.get(url)\n"
        )
        findings = analyzer.scan_text(Path("ssrf.py"), code)
        finding = next(item for item in findings if item.rule_id == "DATA-PY-SSRF-001")
        self.assertEqual(finding.confidence, "HIGH")
        self.assertEqual(finding.cwe, "CWE-918")
        self.assertEqual(finding.dataset_source, "CodeTrace Curated 2026.1")


if __name__ == "__main__":
    unittest.main()
