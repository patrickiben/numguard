import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from numguard import Fact, FactSet, evaluate, load_case  # noqa: E402


def _case():
    return load_case(os.path.join(BASE, "cases", "ae_overview.json"))


def _candidate(label):
    for c in _case()["candidates"]:
        if c["label"] == label:
            return c
    raise KeyError(label)


def test_grounded_draft_passes():
    case = _case()
    cand = _candidate("grounded_draft")
    rep = evaluate(cand["text"], case["factset"], case["banned_phrases"], case["required_names"])
    assert rep.passed, rep.scorecard()


def test_hallucinated_draft_fails():
    case = _case()
    cand = _candidate("hallucinated_draft")
    rep = evaluate(cand["text"], case["factset"], case["banned_phrases"], case["required_names"])
    assert not rep.passed
    error_text = " ".join(f.message for f in rep.errors)
    # the two fabricated numbers are caught
    assert "18" in error_text
    assert "75.0" in error_text
    # the banned qualitative claim is caught
    assert any("well tolerated" in f.message.lower() for f in rep.errors)


def test_clean_text_has_no_findings():
    fs = FactSet(facts=[Fact("x", 10.0)])
    rep = evaluate("The reported value was 10.", fs)
    assert rep.passed
    assert rep.findings == []


def test_required_fact_missing_is_flagged():
    fs = FactSet(facts=[Fact("k", 42.0)])
    rep = evaluate("No relevant numbers here.", fs, required_names=["k"])
    assert not rep.passed
    assert any(f.check == "required_facts" for f in rep.errors)


def test_identifier_digits_are_not_flagged():
    # "CP101" should not be read as the number 101.
    fs = FactSet(facts=[Fact("n", 5.0)])
    rep = evaluate("Study CP101 enrolled 5 participants.", fs)
    assert rep.passed, rep.scorecard()
