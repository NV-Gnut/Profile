from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    severity: str
    languages: tuple[str, ...]
    sources: tuple[str, ...] = ()
    sinks: tuple[str, ...] = ()
    sanitizers: tuple[str, ...] = ()
    direct_patterns: tuple[str, ...] = ()
    message: str = ""
    recommendation: str = ""
    confidence: str = "MEDIUM"
    cwe: str = ""
    dataset_source: str = "CodeTrace Core"

    @classmethod
    def from_dict(cls, value: dict) -> "Rule":
        required = ("id", "name", "severity", "languages")
        missing = [key for key in required if not value.get(key)]
        if missing:
            raise ValueError(f"Thiếu trường bắt buộc: {', '.join(missing)}")
        severity = str(value["severity"]).upper()
        if severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}:
            raise ValueError("severity phải là CRITICAL, HIGH, MEDIUM, LOW hoặc INFO")
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            severity=severity,
            languages=tuple(value["languages"]),
            sources=tuple(value.get("sources", ())),
            sinks=tuple(value.get("sinks", ())),
            sanitizers=tuple(value.get("sanitizers", ())),
            direct_patterns=tuple(value.get("direct_patterns", ())),
            message=str(value.get("message", "")),
            recommendation=str(value.get("recommendation", "")),
            confidence=str(value.get("confidence", "MEDIUM")).upper(),
            cwe=str(value.get("cwe", "")),
            dataset_source=str(value.get("dataset_source", "User dataset")),
        )


@dataclass(frozen=True)
class TraceStep:
    line: int
    kind: str
    code: str
    detail: str


@dataclass
class Finding:
    rule_id: str
    rule_name: str
    severity: str
    file: Path
    line: int
    column: int
    code: str
    message: str
    recommendation: str
    confidence: str = "MEDIUM"
    cwe: str = ""
    dataset_source: str = ""
    trace: list[TraceStep] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = asdict(self)
        result["file"] = str(self.file)
        return result
