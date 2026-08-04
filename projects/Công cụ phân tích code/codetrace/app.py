from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .engine import Analyzer
from .models import Finding, Rule
from .rules import BUILTIN_RULES, load_custom_rules, save_custom_rules


BG = "#10151d"
PANEL = "#171e29"
PANEL_2 = "#202938"
TEXT = "#dfe7f1"
MUTED = "#8d9bad"
ACCENT = "#39c5bb"
ACCENT_2 = "#7c6cff"
SEVERITY = {
    "CRITICAL": "#ff5c75", "HIGH": "#ff8c66", "MEDIUM": "#f5c451",
    "LOW": "#61afef", "INFO": "#8d9bad",
}


class CodeTraceApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("CodeTrace — Source Code Security Analyzer")
        self.root.geometry("1360x820")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)
        self.rule_file = Path.home() / ".codetrace" / "rules.json"
        self.bundled_dataset_file = Path(__file__).parent.parent / "datasets" / "security_rules.json"
        self.dataset_rules = self._load_dataset(self.bundled_dataset_file)
        self.custom_rules = self._load_rules()
        self.analyzer = Analyzer((*BUILTIN_RULES, *self.dataset_rules, *self.custom_rules))
        self.target: Path | None = None
        self.findings: list[Finding] = []
        self.visible_findings: list[Finding] = []
        self.current_file: Path | None = None
        self._setup_style()
        self._build_menu()
        self._build_ui()

    def run(self) -> None:
        self.root.mainloop()

    def _load_rules(self) -> list[Rule]:
        try:
            return load_custom_rules(self.rule_file)
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    @staticmethod
    def _load_dataset(path: Path) -> list[Rule]:
        try:
            return load_custom_rules(path)
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL, bordercolor=PANEL_2)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 18), foreground=TEXT)
        style.configure("Hero.TLabel", font=("Segoe UI Semibold", 21), foreground="#f5f8fc")
        style.configure("TButton", background=PANEL_2, foreground=TEXT, padding=(12, 7), borderwidth=0)
        style.map("TButton", background=[("active", "#2b3749")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#071312")
        style.map("Accent.TButton", background=[("active", "#55d8cf")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=29, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL_2, foreground=TEXT,
                        relief="flat", font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#235a60")])
        style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT)
        style.configure("TPanedwindow", background=BG)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Mở file…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Mở thư mục…", command=self.open_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Xuất báo cáo JSON…", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.destroy)
        rule_menu = tk.Menu(menu, tearoff=False)
        rule_menu.add_command(label="Thêm rule JSON…", command=self.add_rule)
        rule_menu.add_command(label="Nhập dataset rule JSON…", command=self.import_rule_dataset)
        rule_menu.add_command(label="Mở thư mục rule", command=self.show_rule_location)
        menu.add_cascade(label="Tệp", menu=file_menu)
        menu.add_cascade(label="Quản lý rule", menu=rule_menu)
        self.root.config(menu=menu)
        self.root.bind("<Control-o>", lambda _e: self.open_file())
        self.root.bind("<Control-Shift-O>", lambda _e: self.open_folder())
        self.root.bind("<F5>", lambda _e: self.scan())

    def _build_ui(self) -> None:
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(14, 10))
        logo = tk.Label(header, text="  C  ", bg=ACCENT, fg="#071312",
                        font=("Segoe UI Black", 15), padx=4, pady=2)
        logo.pack(side="left", padx=(0, 10))
        ttk.Label(header, text="CodeTrace", style="Hero.TLabel").pack(side="left")
        ttk.Label(header, text="  SECURITY WORKBENCH", style="Muted.TLabel").pack(side="left", pady=(8, 0))
        ttk.Button(header, text="Mở file", command=self.open_file).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Mở thư mục", command=self.open_folder).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="▶  Quét mã nguồn", style="Accent.TButton", command=self.scan).pack(side="right")

        filter_bar = ttk.Frame(self.root, style="Panel.TFrame")
        filter_bar.pack(fill="x", padx=18, pady=(0, 10))
        ttk.Label(filter_bar, text="  TARGET", background=PANEL, foreground=MUTED).pack(side="left", padx=(8, 4))
        self.target_label = ttk.Label(filter_bar, text="Chưa chọn file hoặc thư mục", background=PANEL)
        self.target_label.pack(side="left", padx=6, pady=9)
        self.status_label = ttk.Label(filter_bar, text="Sẵn sàng", background=PANEL, foreground=ACCENT)
        self.status_label.pack(side="right", padx=12)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filter())
        search = tk.Entry(filter_bar, textvariable=self.search_var, bg=PANEL_2, fg=TEXT,
                          insertbackground=TEXT, relief="flat", width=27)
        search.pack(side="right", padx=5, ipady=5)
        ttk.Label(filter_bar, text="Tìm:", background=PANEL).pack(side="right")
        self.severity_var = tk.StringVar(value="Tất cả")
        severity = ttk.Combobox(filter_bar, textvariable=self.severity_var, state="readonly",
                                values=("Tất cả", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"), width=11)
        severity.pack(side="right", padx=10)
        severity.bind("<<ComboboxSelected>>", lambda _e: self.apply_filter())

        symbol_bar = tk.Frame(self.root, bg="#131b26", highlightbackground="#253247",
                              highlightthickness=1)
        symbol_bar.pack(fill="x", padx=18, pady=(0, 10))
        tk.Label(symbol_bar, text="⌁  REVERSE TRACE", bg="#131b26", fg=ACCENT_2,
                 font=("Segoe UI Semibold", 9)).pack(side="left", padx=(12, 10), pady=9)
        self.symbol_var = tk.StringVar()
        symbol_entry = tk.Entry(
            symbol_bar, textvariable=self.symbol_var, bg=PANEL_2, fg=TEXT,
            insertbackground=TEXT, relief="flat", width=30, font=("Cascadia Mono", 10),
        )
        symbol_entry.pack(side="left", padx=(0, 8), ipady=5)
        symbol_entry.bind("<Return>", lambda _e: self.trace_symbol())
        tk.Button(
            symbol_bar, text="Trace ngược hàm / biến", command=self.trace_symbol,
            bg=ACCENT_2, fg="white", activebackground="#9488ff", activeforeground="white",
            relief="flat", cursor="hand2", font=("Segoe UI Semibold", 9), padx=14, pady=5,
        ).pack(side="left")
        tk.Label(
            symbol_bar, text="Chọn một từ trong code hoặc nhập tên symbol rồi nhấn Enter",
            bg="#131b26", fg=MUTED, font=("Segoe UI", 9),
        ).pack(side="left", padx=14)
        self.summary_label = tk.Label(
            symbol_bar, text="0 CRITICAL   0 HIGH   0 MEDIUM", bg="#131b26",
            fg=MUTED, font=("Segoe UI Semibold", 9),
        )
        self.summary_label.pack(side="right", padx=14)

        vertical = ttk.Panedwindow(self.root, orient="vertical")
        vertical.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        upper = ttk.Panedwindow(vertical, orient="horizontal")
        vertical.add(upper, weight=3)

        file_frame = ttk.Frame(upper, style="Panel.TFrame")
        upper.add(file_frame, weight=1)
        ttk.Label(file_frame, text="  SOURCE FILES", background=PANEL, foreground=MUTED).pack(fill="x", pady=7)
        self.file_tree = ttk.Treeview(file_frame, show="tree", selectmode="browse")
        self.file_tree.pack(fill="both", expand=True)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_selected)

        code_frame = ttk.Frame(upper, style="Panel.TFrame")
        upper.add(code_frame, weight=4)
        self.code_title = ttk.Label(code_frame, text="  CODE VIEWER", background=PANEL, foreground=MUTED)
        self.code_title.pack(fill="x", pady=7)
        code_wrap = tk.Frame(code_frame, bg=PANEL)
        code_wrap.pack(fill="both", expand=True)
        self.code = tk.Text(code_wrap, bg="#0d1219", fg=TEXT, insertbackground=TEXT,
                            selectbackground="#235a60", relief="flat", font=("Cascadia Mono", 10),
                            wrap="none", padx=10, pady=8, undo=False)
        y_scroll = ttk.Scrollbar(code_wrap, command=self.code.yview)
        x_scroll = ttk.Scrollbar(code_wrap, orient="horizontal", command=self.code.xview)
        self.code.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.code.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.code.tag_configure("line_no", foreground="#536174")
        self.code.tag_configure("hit", background="#593343")
        self.code.tag_configure("keyword", foreground="#c792ea")
        self.code.tag_configure("string", foreground="#c3e88d")
        self.code.tag_configure("comment", foreground="#637777", font=("Cascadia Mono", 10, "italic"))
        self.code.tag_configure("number", foreground="#f78c6c")
        self.code.tag_configure("function", foreground="#82aaff")
        self.code.tag_configure("operator", foreground="#89ddff")

        lower = ttk.Panedwindow(vertical, orient="horizontal")
        vertical.add(lower, weight=2)
        finding_frame = ttk.Frame(lower, style="Panel.TFrame")
        lower.add(finding_frame, weight=3)
        columns = ("severity", "confidence", "type", "file", "line")
        self.finding_tree = ttk.Treeview(finding_frame, columns=columns, show="headings")
        for col, title, width in (
            ("severity", "Mức độ", 85), ("confidence", "Tin cậy", 75), ("type", "Lỗ hổng", 190),
            ("file", "File", 360), ("line", "Dòng", 55),
        ):
            self.finding_tree.heading(col, text=title)
            self.finding_tree.column(col, width=width, anchor="w" if col != "line" else "center")
        self.finding_tree.pack(fill="both", expand=True)
        self.finding_tree.bind("<<TreeviewSelect>>", self.on_finding_selected)
        for level, color in SEVERITY.items():
            self.finding_tree.tag_configure(level, foreground=color)

        detail_frame = ttk.Frame(lower, style="Panel.TFrame")
        lower.add(detail_frame, weight=2)
        ttk.Label(detail_frame, text="  VULNERABILITY TRACE", background=PANEL, foreground=MUTED).pack(fill="x", pady=7)
        self.detail = tk.Text(detail_frame, bg=PANEL, fg=TEXT, relief="flat",
                              font=("Segoe UI", 10), wrap="word", padx=12, pady=8)
        self.detail.pack(fill="both", expand=True)
        self.detail.tag_configure("title", font=("Segoe UI Semibold", 12), foreground=ACCENT)
        self.detail.tag_configure("critical", foreground=SEVERITY["CRITICAL"])
        self.detail.tag_configure("source", foreground="#61afef")
        self.detail.tag_configure("propagation", foreground="#f5c451")
        self.detail.tag_configure("sink", foreground="#ff6b81")
        self.detail.insert("1.0", "Chọn một finding để xem trace từ SOURCE → PROPAGATION → SINK.")
        self.detail.configure(state="disabled")

    def open_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Chọn source code",
            filetypes=[("Source code", "*.py *.js *.jsx *.ts *.tsx *.php *.java"), ("Tất cả", "*.*")],
        )
        if selected:
            self.set_target(Path(selected))

    def open_folder(self) -> None:
        selected = filedialog.askdirectory(title="Chọn thư mục source code")
        if selected:
            self.set_target(Path(selected))

    def set_target(self, target: Path) -> None:
        self.target = target
        self.target_label.configure(text=str(target))
        self.populate_files()
        if target.is_file():
            self.show_file(target)
        self.scan()

    def populate_files(self) -> None:
        self.file_tree.delete(*self.file_tree.get_children())
        if not self.target:
            return
        files = self.analyzer.collect_files(self.target)
        base = self.target.parent if self.target.is_file() else self.target
        nodes: dict[Path, str] = {base: ""}
        for path in files:
            parent_id = ""
            relative_parts = path.relative_to(base).parts
            current = base
            for index, part in enumerate(relative_parts):
                current /= part
                if current not in nodes:
                    node = self.file_tree.insert(parent_id, "end", text=part, open=index < 1,
                                                 values=(str(current),))
                    nodes[current] = node
                parent_id = nodes[current]

    def scan(self) -> None:
        if not self.target:
            messagebox.showinfo("CodeTrace", "Hãy chọn file hoặc thư mục source code trước.")
            return
        self.status_label.configure(text="Đang phân tích…")
        self.root.update_idletasks()
        try:
            self.findings = self.analyzer.scan(self.target)
            self.apply_filter()
            file_count = len(self.analyzer.collect_files(self.target))
            self.status_label.configure(text=f"{len(self.findings)} finding • {file_count} file")
            counts = {level: sum(f.severity == level for f in self.findings)
                      for level in ("CRITICAL", "HIGH", "MEDIUM")}
            self.summary_label.configure(
                text=f"{counts['CRITICAL']} CRITICAL   {counts['HIGH']} HIGH   {counts['MEDIUM']} MEDIUM"
            )
        except Exception as exc:
            self.status_label.configure(text="Phân tích thất bại")
            messagebox.showerror("Lỗi phân tích", str(exc))

    def apply_filter(self) -> None:
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        severity = self.severity_var.get() if hasattr(self, "severity_var") else "Tất cả"
        self.visible_findings = [
            finding for finding in self.findings
            if (severity == "Tất cả" or finding.severity == severity)
            and (not query or query in finding.rule_name.lower() or query in str(finding.file).lower()
                 or query in finding.code.lower())
        ]
        self.finding_tree.delete(*self.finding_tree.get_children())
        base = self.target.parent if self.target and self.target.is_file() else self.target
        for index, finding in enumerate(self.visible_findings):
            try:
                display_file = str(finding.file.relative_to(base)) if base else str(finding.file)
            except ValueError:
                display_file = str(finding.file)
            self.finding_tree.insert("", "end", iid=str(index), tags=(finding.severity,),
                                     values=(finding.severity, finding.confidence,
                                             finding.rule_name, display_file, finding.line))

    def on_file_selected(self, _event=None) -> None:
        selection = self.file_tree.selection()
        if not selection:
            return
        values = self.file_tree.item(selection[0], "values")
        if values:
            path = Path(values[0])
            if path.is_file():
                self.show_file(path)

    def show_file(self, path: Path, highlight: int | None = None) -> None:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            messagebox.showerror("Không thể mở file", str(exc))
            return
        self.current_file = path
        self.code_title.configure(text=f"  CODE VIEWER  •  {path}")
        self.code.configure(state="normal")
        self.code.delete("1.0", "end")
        width = max(3, len(str(len(lines))))
        for number, line in enumerate(lines, 1):
            prefix = f"{number:>{width}}  "
            self.code.insert("end", prefix, "line_no")
            start = self.code.index("end-1c")
            self.code.insert("end", line + "\n")
            if number == highlight:
                self.code.tag_add("hit", start, f"{number}.end")
            self._highlight_line(number, line, len(prefix))
        self.code.configure(state="disabled")
        if highlight:
            self.code.see(f"{highlight}.0")

    def _highlight_line(self, row: int, line: str, offset: int) -> None:
        patterns = (
            ("keyword", r"\b(?:def|class|return|if|else|elif|for|while|try|except|finally|"
                        r"import|from|as|with|lambda|yield|async|await|function|const|let|"
                        r"var|new|this|public|private|protected|static|final|void|throw|"
                        r"interface|extends|implements|package|echo|include|require)\b"),
            ("number", r"\b(?:0x[\da-fA-F]+|\d+(?:\.\d+)?)\b"),
            ("function", r"\b[A-Za-z_$][\w$]*(?=\s*\()"),
            ("operator", r"(?:=>|==={0,1}|!==?|<=|>=|\+\+|--|&&|\|\||[+\-*/%])"),
            ("string", r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"),
            ("comment", r"(?:#|//).*$"),
        )
        for tag, pattern in patterns:
            for match in __import__("re").finditer(pattern, line):
                self.code.tag_add(tag, f"{row}.{offset + match.start()}",
                                  f"{row}.{offset + match.end()}")
        self.code.tag_raise("string")
        self.code.tag_raise("comment")

    def trace_symbol(self) -> None:
        if not self.target:
            messagebox.showinfo("Reverse trace", "Hãy mở file hoặc thư mục source code trước.")
            return
        symbol = self.symbol_var.get().strip()
        try:
            selected = self.code.get("sel.first", "sel.last").strip()
            if selected and __import__("re").fullmatch(r"[A-Za-z_$][\w$]*", selected):
                symbol = selected
                self.symbol_var.set(symbol)
        except tk.TclError:
            pass
        if not symbol:
            messagebox.showinfo("Reverse trace", "Nhập tên hàm/biến hoặc bôi đen symbol trong code.")
            return
        try:
            graph = self.analyzer.trace_symbol_graph(self.target, symbol)
        except ValueError as exc:
            messagebox.showerror("Tên symbol không hợp lệ", str(exc))
            return
        self._show_symbol_graph(graph)

    def _show_symbol_graph(self, graph) -> None:
        window = tk.Toplevel(self.root)
        window.title(f"Reverse Trace — {graph.symbol}")
        window.geometry("1050x650")
        window.configure(bg=BG)
        window.transient(self.root)

        top = tk.Frame(window, bg=BG)
        top.pack(fill="x", padx=18, pady=(16, 10))
        tk.Label(top, text=f"Reverse Trace: {graph.symbol}", bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 18)).pack(side="left")
        tk.Label(top, text="  ↓  đọc luồng dữ liệu từ trên xuống", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", pady=(8, 0))
        tk.Label(top, text=graph.parser, bg="#283047", fg="#b9afff",
                 font=("Segoe UI Semibold", 9), padx=10, pady=5).pack(side="right", pady=4)
        tk.Button(
            top, text="←  Quay lại code", command=lambda: self._close_graph_to_code(window),
            bg=PANEL_2, fg=TEXT, activebackground="#334158", activeforeground="white",
            relief="flat", cursor="hand2", font=("Segoe UI Semibold", 9), padx=12, pady=5,
        ).pack(side="right", padx=(0, 8), pady=4)

        simple_nodes = self._simple_trace_nodes(graph)
        simple_ids = {node.id for node in simple_nodes}
        source_nodes = [node for node in graph.nodes if node.kind == "SOURCE"]
        endpoints = [node for node in graph.nodes if node.kind == "ENDPOINT"]
        endpoint_names = ", ".join(dict.fromkeys(node.symbol for node in endpoints)) or "Không có"
        source_names = ", ".join(dict.fromkeys(node.symbol for node in source_nodes)) or "Không xác định"
        definition_location = (
            f"{graph.definitions[0].file.name}:{graph.definitions[0].line}"
            if graph.definitions else "Không tìm thấy"
        )
        summary = (
            f"{graph.symbol}  •  Tạo tại {definition_location}  •  Nguồn: {source_names}"
            f"  •  Dùng {len(graph.usages)} nơi  •  Endpoint: {endpoint_names}"
        )
        tk.Label(
            window, text=summary, bg="#17242a", fg="#a9e6de", anchor="w",
            padx=12, pady=10, font=("Segoe UI Semibold", 9),
        ).pack(fill="x", padx=18, pady=(0, 10))

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        graph_tab = tk.Frame(notebook, bg="#0d1219")
        detail_tab = tk.Frame(notebook, bg=BG)
        notebook.add(graph_tab, text="  Trace ngắn gọn  ")
        notebook.add(detail_tab, text="  Danh sách  ")

        canvas = tk.Canvas(
            graph_tab, bg="#0d1219", highlightthickness=0,
            xscrollincrement=20, yscrollincrement=20,
        )
        canvas_x = ttk.Scrollbar(graph_tab, orient="horizontal", command=canvas.xview)
        canvas_y = ttk.Scrollbar(graph_tab, command=canvas.yview)
        canvas.configure(xscrollcommand=canvas_x.set, yscrollcommand=canvas_y.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas_y.grid(row=0, column=1, sticky="ns")
        canvas_x.grid(row=1, column=0, sticky="ew")
        graph_tab.rowconfigure(0, weight=1)
        graph_tab.columnconfigure(0, weight=1)

        columns = ("kind", "symbol", "scope", "file", "line", "detail")
        tree = ttk.Treeview(detail_tab, columns=columns, show="headings")
        for column, title, width in (
            ("kind", "Loại node", 95), ("symbol", "Symbol", 120), ("scope", "Scope", 160),
            ("file", "File", 220), ("line", "Dòng", 50), ("detail", "Ý nghĩa", 390),
        ):
            tree.heading(column, text=title)
            tree.column(column, width=width, anchor="w" if column != "line" else "center")
        tree.pack(fill="both", expand=True)

        colors = {
            "SOURCE": "#ff6b81", "LITERAL": "#f78c6c", "PARAMETER": "#f5c451",
            "ASSIGNMENT": "#82aaff", "FUNCTION": "#c792ea", "READ": "#39c5bb",
            "CALL": "#89ddff", "RETURN": "#b2ccd6", "IMPORT": "#d4a5ff",
            "ENDPOINT": "#ff6b9d",
        }
        base = self.target.parent if self.target and self.target.is_file() else self.target
        for kind, color in colors.items():
            tree.tag_configure(kind, foreground=color)
        node_by_iid = {}
        for index, node in enumerate(simple_nodes):
            try:
                file_name = str(node.file.relative_to(base))
            except ValueError:
                file_name = str(node.file)
            iid = str(index)
            node_by_iid[iid] = node
            tree.insert("", "end", iid=iid, tags=(node.kind,), values=(
                node.kind, node.symbol, node.scope, file_name, node.line, node.detail,
            ))

        def open_node(node):
            self.show_file(node.file, node.line)
            self._close_graph_to_code(window)

        def select_row(_event=None):
            selection = tree.selection()
            if selection:
                open_node(node_by_iid[selection[0]])

        tree.bind("<Double-1>", select_row)
        self._draw_dependency_graph(canvas, graph, open_node, simple_ids)

        if not graph.nodes:
            canvas.create_text(
                60, 60, anchor="nw", fill=MUTED, font=("Segoe UI", 12),
                text=(f"Không tìm thấy symbol '{graph.symbol}' trong AST Python.\n"
                      "Tên biến phân biệt chữ hoa/chữ thường và phải khớp chính xác."),
            )

    @staticmethod
    def _simple_trace_nodes(graph):
        """Keep strict data paths to/from the searched symbol, never sibling calls in a handler."""
        node_map = {node.id: node for node in graph.nodes}
        visible = {node.id for node in graph.nodes if node.symbol == graph.symbol}

        # Walk backwards only through real value-definition edges. Do not follow
        # CONTAINS here: that would pull unrelated calls from the same handler.
        upstream_edges = {"FLOWS_TO", "READS", "IMPORTS", "ITERATES_TO", "RETURNS_TO"}
        frontier = set(visible)
        for _ in range(6):
            added = {
                edge.source for edge in graph.edges
                if edge.target in frontier and edge.kind in upstream_edges
            } - visible
            visible.update(added)
            frontier = added
            if not frontier:
                break

        # Keep only calls that directly receive the searched value.
        direct_reads = {node_id for node_id in visible if node_map[node_id].symbol == graph.symbol}
        for edge in graph.edges:
            if (edge.source in direct_reads and edge.kind == "ARGUMENT"
                    and node_map.get(edge.target) and node_map[edge.target].kind == "CALL"):
                visible.add(edge.target)

        # Add the containing handler of an exact read, then only endpoints mapped
        # to that handler. Sibling operations inside the handler remain hidden.
        handlers = {
            edge.source for edge in graph.edges
            if edge.target in direct_reads and edge.kind == "CONTAINS"
            and node_map.get(edge.source) and node_map[edge.source].kind == "FUNCTION"
        }
        visible.update(handlers)
        visible.update(
            edge.source for edge in graph.edges
            if edge.target in handlers and edge.kind == "HANDLES"
            and node_map.get(edge.source) and node_map[edge.source].kind == "ENDPOINT"
        )
        return [node for node in graph.nodes if node.id in visible]

    def _draw_dependency_graph(self, canvas: tk.Canvas, graph, open_node,
                               visible_ids: set[str] | None = None) -> None:
        if not graph.nodes:
            return
        node_map = {
            node.id: node for node in graph.nodes
            if visible_ids is None or node.id in visible_ids
        }
        edges = [edge for edge in graph.edges if edge.source in node_map and edge.target in node_map]
        incoming = {node_id: [] for node_id in node_map}
        outgoing = {node_id: [] for node_id in node_map}
        # RETURNS_TO closes an inter-procedural loop (call → parameter → return → call).
        # Keep it visible, but exclude it from rank calculation so the diagram stays layered.
        layout_edges = [edge for edge in edges if edge.kind != "RETURNS_TO"]
        for edge in layout_edges:
            incoming[edge.target].append(edge)
            outgoing[edge.source].append(edge)

        indegree = {node_id: len(incoming[node_id]) for node_id in node_map}
        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        layers = {node_id: 0 for node_id in queue}
        processed = set()
        while queue:
            node_id = queue.pop(0)
            processed.add(node_id)
            for edge in outgoing[node_id]:
                layers[edge.target] = max(layers.get(edge.target, 0), layers[node_id] + 1)
                indegree[edge.target] -= 1
                if indegree[edge.target] == 0:
                    queue.append(edge.target)
        for node_id in node_map:
            if node_id not in processed:
                layers[node_id] = min(layers.get(node_id, 0), 7)

        grouped: dict[int, list[str]] = {}
        for node_id, layer in layers.items():
            grouped.setdefault(min(layer, 9), []).append(node_id)
        positions = {}
        node_width, node_height = 210, 76
        x_gap, y_gap = 34, 78
        for layer, node_ids in sorted(grouped.items()):
            node_ids.sort(key=lambda node_id: (str(node_map[node_id].file), node_map[node_id].line))
            layer_width = len(node_ids) * node_width + max(0, len(node_ids) - 1) * x_gap
            start_x = max(35, (1100 - layer_width) / 2)
            for column, node_id in enumerate(node_ids):
                positions[node_id] = (
                    start_x + column * (node_width + x_gap),
                    45 + layer * (node_height + y_gap),
                )

        for edge in edges:
            if edge.source not in positions or edge.target not in positions:
                continue
            sx, sy = positions[edge.source]
            tx, ty = positions[edge.target]
            source_x, source_y = sx + node_width / 2, sy + node_height
            target_x, target_y = tx + node_width / 2, ty
            is_back_edge = target_y <= source_y
            edge_color = "#725a82" if edge.kind == "RETURNS_TO" else "#46566f"
            line_points = (
                (source_x, source_y, source_x + node_width * 0.7, source_y + 30,
                 target_x + node_width * 0.7, target_y - 30, target_x, target_y)
                if is_back_edge else
                (source_x, source_y, target_x, target_y)
            )
            canvas.create_line(
                *line_points,
                fill=edge_color, width=2, arrow="last", arrowshape=(8, 10, 4),
                smooth=is_back_edge,
            )
            middle_x, middle_y = (source_x + target_x) / 2, (source_y + target_y) / 2
            canvas.create_text(
                middle_x + 5, middle_y, anchor="w", text=edge.kind,
                fill="#9a78ad" if is_back_edge else "#65758d",
                font=("Segoe UI Semibold", 7),
            )

        colors = {
            "SOURCE": "#b9455b", "LITERAL": "#9b5746", "PARAMETER": "#8b7131",
            "ASSIGNMENT": "#345d91", "FUNCTION": "#6b4d8d", "READ": "#286f6a",
            "CALL": "#2f6877", "RETURN": "#4d5c68", "IMPORT": "#725488",
            "ENDPOINT": "#8f365f",
        }
        for index, (node_id, (x, y)) in enumerate(positions.items()):
            node = node_map[node_id]
            tag = f"graph_node_{index}"
            border = "#d9e2ef" if node.symbol == graph.symbol else "#627088"
            canvas.create_rectangle(
                x, y, x + node_width, y + node_height, fill=colors.get(node.kind, PANEL),
                outline=border, width=2 if node.symbol == graph.symbol else 1,
                tags=(tag, "graph_node"),
            )
            canvas.create_text(
                x + 10, y + 9, anchor="nw", text=node.kind, fill="#dce5f0",
                font=("Segoe UI Semibold", 8), tags=(tag,),
            )
            canvas.create_text(
                x + 10, y + 28, anchor="nw", text=node.symbol[:28], fill="white",
                font=("Cascadia Mono", 10, "bold"), tags=(tag,),
            )
            canvas.create_text(
                x + 10, y + 53, anchor="nw",
                text=f"{node.file.name}:{node.line}  •  {node.scope[-24:]}",
                fill="#b2c0d0", font=("Segoe UI", 8), tags=(tag,),
            )
            canvas.tag_bind(tag, "<Button-1>", lambda _event, selected=node: open_node(selected))
            canvas.tag_bind(tag, "<Enter>", lambda _event: canvas.configure(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda _event: canvas.configure(cursor=""))

        canvas.configure(scrollregion=canvas.bbox("all"))

    def _close_graph_to_code(self, window: tk.Toplevel) -> None:
        if window.winfo_exists():
            window.destroy()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_finding_selected(self, _event=None) -> None:
        selection = self.finding_tree.selection()
        if not selection:
            return
        finding = self.visible_findings[int(selection[0])]
        self.show_file(finding.file, finding.line)
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", f"{finding.rule_name}\n", "title")
        metadata = "  •  ".join(filter(None, (
            finding.severity, f"Tin cậy {finding.confidence}", finding.cwe,
            finding.dataset_source, finding.rule_id,
        )))
        self.detail.insert("end", metadata + "\n\n", "critical")
        self.detail.insert("end", finding.message + "\n\n")
        for index, step in enumerate(finding.trace, 1):
            tag = step.kind.lower()
            self.detail.insert("end", f"{index}. {step.kind}  dòng {step.line}\n", tag)
            self.detail.insert("end", f"   {step.detail}\n   {step.code}\n\n")
        self.detail.insert("end", "Khuyến nghị\n", "title")
        self.detail.insert("end", finding.recommendation)
        self.detail.configure(state="disabled")

    def export_report(self) -> None:
        if not self.findings:
            messagebox.showinfo("CodeTrace", "Chưa có finding để xuất.")
            return
        selected = filedialog.asksaveasfilename(
            title="Xuất báo cáo", defaultextension=".json",
            filetypes=[("JSON", "*.json")], initialfile="codetrace-report.json",
        )
        if selected:
            report = {
                "tool": "CodeTrace", "target": str(self.target),
                "summary": {level: sum(f.severity == level for f in self.findings) for level in SEVERITY},
                "findings": [finding.to_dict() for finding in self.findings],
            }
            Path(selected).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("CodeTrace", f"Đã xuất báo cáo:\n{selected}")

    def add_rule(self) -> None:
        template = (
            '{"id":"CUSTOM-001","name":"Custom vulnerability","severity":"HIGH",'
            '"languages":["python"],"sources":["request\\\\.args"],'
            '"sinks":["dangerous\\\\s*\\\\("],"sanitizers":[],'
            '"message":"Mô tả finding","recommendation":"Cách khắc phục"}'
        )
        raw = simpledialog.askstring("Thêm rule JSON", "Nhập rule (regex cần escape theo JSON):",
                                     initialvalue=template, parent=self.root)
        if not raw:
            return
        try:
            rule = Rule.from_dict(json.loads(raw))
            if any(existing.id == rule.id for existing in (
                *BUILTIN_RULES, *self.dataset_rules, *self.custom_rules
            )):
                raise ValueError(f"Rule ID '{rule.id}' đã tồn tại")
            for pattern in (*rule.sources, *rule.sinks, *rule.sanitizers, *rule.direct_patterns):
                __import__("re").compile(pattern)
            self.custom_rules.append(rule)
            save_custom_rules(self.rule_file, self.custom_rules)
            self.analyzer = Analyzer((*BUILTIN_RULES, *self.dataset_rules, *self.custom_rules))
            messagebox.showinfo("CodeTrace", f"Đã thêm rule {rule.id}.")
        except (ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Rule không hợp lệ", str(exc))

    def import_rule_dataset(self) -> None:
        selected = filedialog.askopenfilename(
            title="Chọn dataset rule", filetypes=[("JSON dataset", "*.json"), ("Tất cả", "*.*")],
        )
        if not selected:
            return
        try:
            imported = load_custom_rules(Path(selected))
            known = {rule.id for rule in (*BUILTIN_RULES, *self.dataset_rules, *self.custom_rules)}
            added = []
            for rule in imported:
                if rule.id in known:
                    continue
                for pattern in (*rule.sources, *rule.sinks, *rule.sanitizers, *rule.direct_patterns):
                    __import__("re").compile(pattern)
                added.append(rule)
                known.add(rule.id)
            self.custom_rules.extend(added)
            save_custom_rules(self.rule_file, self.custom_rules)
            self.analyzer = Analyzer((*BUILTIN_RULES, *self.dataset_rules, *self.custom_rules))
            messagebox.showinfo(
                "Dataset rule",
                f"Đã nạp {len(added)}/{len(imported)} rule mới.\n"
                f"Rule trùng ID được bỏ qua để tránh phát hiện lặp.",
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Dataset không hợp lệ", str(exc))

    def show_rule_location(self) -> None:
        self.rule_file.parent.mkdir(parents=True, exist_ok=True)
        messagebox.showinfo("Thư mục rule", str(self.rule_file))
