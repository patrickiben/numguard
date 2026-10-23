from __future__ import annotations

from typing import Iterable

from .checks import (
    check_no_unsupported_claims,
    check_numbers_grounded,
    check_required_facts,
)
from .facts import FactSet
from .report import Finding, Report


def evaluate(
    text: str,
    factset: FactSet,
    banned_phrases: Iterable[str] = (),
    required_names: Iterable[str] = (),
) -> Report:
    """Run the full guardrail suite against a candidate draft.

    The evaluation is fully deterministic and runs no model: a model (if any)
    produces ``text``; numguard only judges it against ``factset``.
    """
    required_names = tuple(required_names)
    factset.validate(required_names)
    try:
        return _evaluate(text, factset, banned_phrases, required_names)
    except ValueError as error:
        return Report([Finding("numeric_format", "ERROR", str(error))])


def _evaluate(text, factset, banned_phrases, required_names):
    findings = []
    findings += check_numbers_grounded(text, factset)
    findings += check_no_unsupported_claims(text, banned_phrases)
    findings += check_required_facts(text, factset, required_names)
    return Report(findings)
