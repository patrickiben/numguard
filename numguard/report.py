from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

SEVERITIES = ("ERROR", "WARN", "INFO")


@dataclass
class Finding:
    """A single issue raised by a check."""

    check: str
    severity: str
    message: str
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """The result of evaluating one draft."""

    findings: List[Finding] = field(default_factory=list)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "WARN"]

    @property
    def passed(self) -> bool:
        """A draft passes the gate only if it has zero ERROR findings."""
        return len(self.errors) == 0

    def scorecard(self) -> str:
        """A human-readable summary block."""
        head = "PASS" if self.passed else "FAIL"
        lines = [
            f"  verdict: {head}  "
            f"({len(self.errors)} error(s), {len(self.warnings)} warning(s))"
        ]
        if not self.findings:
            lines.append("   - no findings: recognized numeric values match allowed facts; no listed banned phrases.")
        for f in self.findings:
            lines.append(f"   - [{f.severity}] {f.check}: {f.message}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """A JSON-serializable view of this report."""
        return {
            "passed": self.passed,
            "n_errors": len(self.errors),
            "n_warnings": len(self.warnings),
            "findings": [
                {
                    "check": f.check,
                    "severity": f.severity,
                    "message": f.message,
                    "detail": f.detail,
                }
                for f in self.findings
            ],
        }
