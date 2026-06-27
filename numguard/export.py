"""Suite-level exports: JSON and JUnit XML, for CI dashboards.

A *record* is a dict::

    {"name": <str>, "report": <Report>, "expected": <"pass"|"fail"|None>,
     "classname": <str optional>}

If ``expected`` is given, a record is "ok" when the guardrail verdict matches it
(regression mode: did the harness behave as specified?). If ``expected`` is
omitted, a record is "ok" when the draft passes the gate (validation mode: which
drafts are non-compliant?). Non-ok records become JUnit ``<failure>`` entries.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from xml.dom import minidom
from xml.etree import ElementTree as ET

from .report import Report


def record_ok(report: Report, expected: Any) -> bool:
    if expected is not None:
        verdict = "pass" if report.passed else "fail"
        return verdict == expected
    return report.passed


def reports_to_dict(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    cases = []
    not_ok = 0
    for r in records:
        report: Report = r["report"]
        ok = record_ok(report, r.get("expected"))
        if not ok:
            not_ok += 1
        entry = {
            "name": r.get("name", "candidate"),
            "classname": r.get("classname", ""),
            "expected": r.get("expected"),
            "verdict": "pass" if report.passed else "fail",
            "ok": ok,
        }
        entry.update(report.to_dict())
        cases.append(entry)
    return {
        "total": len(records),
        "not_ok": not_ok,
        "all_ok": not_ok == 0,
        "cases": cases,
    }


def reports_to_json(records: List[Dict[str, Any]], indent: int = 2) -> str:
    return json.dumps(reports_to_dict(records), indent=indent)


def reports_to_junit(records: List[Dict[str, Any]], suite_name: str = "numguard") -> str:
    failures = sum(0 if record_ok(r["report"], r.get("expected")) else 1 for r in records)
    suites = ET.Element("testsuites", name=suite_name,
                        tests=str(len(records)), failures=str(failures))
    suite = ET.SubElement(suites, "testsuite", name=suite_name,
                          tests=str(len(records)), failures=str(failures))
    for r in records:
        report: Report = r["report"]
        ok = record_ok(report, r.get("expected"))
        tc = ET.SubElement(
            suite, "testcase",
            name=str(r.get("name", "candidate")),
            classname=str(r.get("classname", suite_name)),
        )
        if not ok:
            verdict = "pass" if report.passed else "fail"
            expected = r.get("expected")
            if expected is not None:
                msg = f"expected {expected}, got {verdict}"
            else:
                msg = f"{len(report.errors)} guardrail error(s)"
            failure = ET.SubElement(tc, "failure", message=msg, type="GuardrailFailure")
            failure.text = "\n".join(
                f"[{f.severity}] {f.check}: {f.message}" for f in report.findings
            ) or msg
    raw = ET.tostring(suites, encoding="unicode")
    return minidom.parseString(raw).toprettyxml(indent="  ")
