import json
import os
import sys
from xml.etree import ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from numguard import Fact, FactSet, evaluate, load_case  # noqa: E402
from numguard.export import (  # noqa: E402
    record_ok,
    reports_to_dict,
    reports_to_json,
    reports_to_junit,
)


def _records():
    case = load_case(os.path.join(BASE, "cases", "ae_overview.json"))
    recs = []
    for c in case["candidates"]:
        rep = evaluate(c["text"], case["factset"], case["banned_phrases"], case["required_names"])
        recs.append({
            "name": c["label"], "classname": case["name"],
            "expected": c["expected"], "report": rep,
        })
    return recs


def test_json_export_roundtrips():
    data = json.loads(reports_to_json(_records()))
    assert data["total"] == 2
    assert data["all_ok"] is True  # both candidates behave as specified
    labels = {c["name"] for c in data["cases"]}
    assert labels == {"grounded_draft", "hallucinated_draft"}


def test_junit_export_is_valid_xml():
    root = ET.fromstring(reports_to_junit(_records()))
    suite = root.find("testsuite")
    assert suite is not None
    assert len(suite.findall("testcase")) == 2
    # both behave as expected -> no <failure> elements in regression mode
    assert suite.findall(".//failure") == []


def test_junit_flags_unexpected_verdict():
    fs = FactSet(facts=[Fact("x", 1.0)])
    rep = evaluate("The value 999 appeared.", fs)  # 999 untraceable -> fails gate
    recs = [{"name": "t", "classname": "c", "expected": "pass", "report": rep}]
    root = ET.fromstring(reports_to_junit(recs))
    failure = root.find(".//testcase/failure")
    assert failure is not None
    assert "expected pass" in failure.get("message")


def test_validation_mode_without_expected():
    fs = FactSet(facts=[Fact("x", 1.0)])
    good = {"name": "g", "report": evaluate("Only 1 here.", fs)}
    bad = {"name": "b", "report": evaluate("A rogue 42 here.", fs)}
    summary = reports_to_dict([good, bad])
    assert summary["not_ok"] == 1  # the rogue-number draft is non-compliant
    assert record_ok(good["report"], None) is True
    assert record_ok(bad["report"], None) is False
