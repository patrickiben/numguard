from __future__ import annotations

import json
from typing import Any, Dict

from .facts import Fact, FactSet


def load_case(path: str) -> Dict[str, Any]:
    """Load a declarative test case (JSON) into ready-to-use objects.

    Returns a dict with: ``name``, ``factset`` (a :class:`FactSet`),
    ``banned_phrases``, ``required_names``, and ``candidates``.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    facts = [
        Fact(name=f["name"], value=f.get("value"), unit=f.get("unit", ""))
        for f in data.get("facts", [])
    ]
    factset = FactSet(
        facts=facts,
        context_values=tuple(data.get("context_values", [])),
        abs_tol=data.get("abs_tol", 0.05),
        rel_tol=data.get("rel_tol", 0.001),
    )
    factset.validate(data.get("required_names", []))
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("At least one candidate is required")
    return {
        "name": data.get("name", ""),
        "factset": factset,
        "banned_phrases": data.get("banned_phrases", []),
        "required_names": data.get("required_names", []),
        "candidates": data.get("candidates", []),
    }
