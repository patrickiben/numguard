from __future__ import annotations

from typing import Iterable, List

from .extract import extract_numbers
from .facts import FactSet
from .report import Finding


def check_numbers_grounded(text: str, factset: FactSet) -> List[Finding]:
    """ERROR for any number in ``text`` not traceable to an allowed fact value.

    This is the core guardrail. An LLM draft may only restate numbers that
    already exist in the fact set; anything else was, by definition, produced
    by the model and is rejected.
    """
    findings: List[Finding] = []
    for val, raw, pos in extract_numbers(text):
        if factset.matches(val) is None:
            findings.append(
                Finding(
                    check="numbers_grounded",
                    severity="ERROR",
                    message=f"Untraceable number '{raw}' is not supported by any fact.",
                    detail={"value": val, "position": pos},
                )
            )
    return findings


def check_no_unsupported_claims(text: str, banned_phrases: Iterable[str]) -> List[Finding]:
    """ERROR for banned qualitative claims (e.g. 'well tolerated', 'safe and effective')."""
    findings: List[Finding] = []
    low = text.lower()
    for phrase in banned_phrases:
        idx = low.find(phrase.lower())
        if idx != -1:
            findings.append(
                Finding(
                    check="unsupported_claims",
                    severity="ERROR",
                    message=f"Unsupported qualitative claim: '{phrase}'.",
                    detail={"position": idx},
                )
            )
    return findings


def check_required_facts(
    text: str, factset: FactSet, required_names: Iterable[str]
) -> List[Finding]:
    """ERROR for any required fact whose value never appears in ``text``."""
    findings: List[Finding] = []
    numbers = [v for v, _, _ in extract_numbers(text)]
    for name in required_names:
        fact = factset.by_name(name)
        if fact is None or fact.value is None:
            continue
        tol = max(factset.abs_tol, factset.rel_tol * abs(fact.value))
        present = any(abs(n - fact.value) <= tol for n in numbers)
        if not present:
            unit = f" {fact.unit}" if fact.unit else ""
            findings.append(
                Finding(
                    check="required_facts",
                    severity="ERROR",
                    message=(
                        f"Required fact '{name}' ({fact.value}{unit}) "
                        "is missing from the text."
                    ),
                    detail={"fact": name, "value": fact.value},
                )
            )
    return findings
