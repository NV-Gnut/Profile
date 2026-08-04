from __future__ import annotations

import json
from pathlib import Path

from .models import Rule


BUILTIN_RULES = (
    Rule(
        id="CT-SQLI-001", name="SQL Injection", severity="HIGH",
        languages=("python", "javascript", "typescript", "php", "java"),
        sources=(r"\brequest\.(args|form|json|GET|POST|query|body|params)\b", r"\$_(GET|POST|REQUEST)\b"),
        sinks=(r"\b(execute|executemany|query|rawQuery)\s*\(", r"\b(cursor|statement)\.execute\s*\("),
        sanitizers=(r"\b(escape|quote|parameterize)\s*\(", r"\?"),
        message="Dữ liệu đầu vào có thể đi vào câu truy vấn SQL.",
        recommendation="Dùng prepared statement/query tham số; không nối chuỗi dữ liệu người dùng vào SQL.",
    ),
    Rule(
        id="CT-CMD-001", name="Command Injection", severity="CRITICAL",
        languages=("python", "javascript", "typescript", "php", "java"),
        sources=(r"\brequest\.(args|form|json|query|body|params)\b", r"\$_(GET|POST|REQUEST)\b", r"\binput\s*\("),
        sinks=(r"\b(os\.system|os\.popen|subprocess\.(run|call|Popen)|exec|spawn|system|Runtime\.getRuntime\(\)\.exec)\s*\(",),
        sanitizers=(r"\b(shlex\.quote|escapeshellarg|allowlist|validate_command)\s*\(",),
        message="Dữ liệu không tin cậy có thể được dùng để thực thi lệnh hệ điều hành.",
        recommendation="Tránh shell; truyền danh sách đối số cố định và kiểm tra allow-list.",
    ),
    Rule(
        id="CT-PATH-001", name="Path Traversal", severity="HIGH",
        languages=("python", "javascript", "typescript", "php", "java"),
        sources=(r"\brequest\.(args|form|json|query|body|params)\b", r"\$_(GET|POST|REQUEST)\b"),
        sinks=(r"\b(open|readFile|readFileSync|send_file|FileInputStream|include|require)\s*\(",),
        sanitizers=(r"\b(realpath|resolve|basename|secure_filename|normalize)\s*\(",),
        message="Đường dẫn do người dùng kiểm soát có thể được dùng để truy cập file.",
        recommendation="Chuẩn hóa đường dẫn và xác minh nó vẫn nằm trong thư mục gốc cho phép.",
    ),
    Rule(
        id="CT-XSS-001", name="Cross-site Scripting", severity="HIGH",
        languages=("python", "javascript", "typescript", "php", "java"),
        sources=(r"\brequest\.(args|form|json|query|body|params)\b", r"\$_(GET|POST|REQUEST)\b"),
        sinks=(r"\b(innerHTML|outerHTML)\s*=", r"\b(document\.write|res\.send|render_template_string|echo|print)\s*\(?"),
        sanitizers=(r"\b(escape|encode|sanitize|DOMPurify\.sanitize|htmlspecialchars)\s*\(",),
        message="Dữ liệu không tin cậy có thể được xuất ra HTML mà chưa encode.",
        recommendation="Encode theo ngữ cảnh output và dùng template auto-escaping.",
    ),
    Rule(
        id="CT-EVAL-001", name="Dynamic Code Execution", severity="CRITICAL",
        languages=("python", "javascript", "typescript", "php", "java"),
        sources=(r"\brequest\.(args|form|json|query|body|params)\b", r"\$_(GET|POST|REQUEST)\b", r"\binput\s*\("),
        sinks=(r"(?<![\w.])(eval|Function|compile)\s*\(",),
        message="Dữ liệu có thể được thực thi như mã nguồn.",
        recommendation="Loại bỏ eval/Function; ánh xạ giá trị đầu vào vào hành vi được định nghĩa trước.",
    ),
    Rule(
        id="CT-CRYPTO-001", name="Weak Cryptographic Hash", severity="MEDIUM",
        languages=("python", "javascript", "typescript", "php", "java"),
        direct_patterns=(r"\b(md5|sha1|MD5|SHA-1)\s*\(", r"hashlib\.(md5|sha1)\s*\("),
        message="Thuật toán băm yếu được sử dụng.",
        recommendation="Dùng SHA-256+ cho integrity; dùng Argon2/bcrypt/scrypt cho mật khẩu.",
    ),
    Rule(
        id="CT-SECRET-001", name="Hard-coded Secret", severity="HIGH",
        languages=("python", "javascript", "typescript", "php", "java"),
        direct_patterns=(r"(?i)\b(password|passwd|api[_-]?key|secret|token)\b\s*[:=]\s*[\"'][^\"']{6,}[\"']",),
        message="Thông tin bí mật có vẻ được ghi trực tiếp trong source code.",
        recommendation="Đưa secret vào secret manager hoặc biến môi trường và rotate giá trị đã lộ.",
    ),
)


def load_custom_rules(path: Path) -> list[Rule]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("File rule phải chứa một mảng JSON")
    return [Rule.from_dict(item) for item in data]


def save_custom_rules(path: Path, rules: list[Rule]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "id": r.id, "name": r.name, "severity": r.severity,
            "languages": list(r.languages), "sources": list(r.sources),
            "sinks": list(r.sinks), "sanitizers": list(r.sanitizers),
            "direct_patterns": list(r.direct_patterns), "message": r.message,
            "recommendation": r.recommendation, "confidence": r.confidence,
            "cwe": r.cwe, "dataset_source": r.dataset_source,
        }
        for r in rules
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
