from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Fact:
    """A single allowed ground-truth value a draft may reference.

    ``value`` is the numeric value (or ``None`` for a purely qualitative fact).
    """

    name: str
    value: Optional[float] = None
    unit: str = ""


@dataclass
class FactSet:
    """The complete set of values a draft is allowed to contain.

    Any number found in a draft that does not match a fact value (within
    tolerance) or an explicit context value is treated as *untraceable* -- a
    guardrail breach. This is the mechanism behind "the model never sources a
    number": a draft may only restate numbers that already exist here.

    ``context_values`` are numbers allowed to appear but not required (e.g. a
    phase number or a study-design constant) so they do not false-positive.
    """

    facts: List[Fact] = field(default_factory=list)
    context_values: Tuple[float, ...] = ()
    abs_tol: float = 0.05
    rel_tol: float = 0.001

    def numeric_values(self) -> List[float]:
        vals = [f.value for f in self.facts if f.value is not None]
        vals.extend(self.context_values)
        return vals

    def _tol_for(self, v: float) -> float:
        return max(self.abs_tol, self.rel_tol * abs(v))

    def matches(self, x: float) -> Optional[float]:
        """Return the allowed value that x corresponds to, or None if untraceable."""
        for v in self.numeric_values():
            if abs(x - v) <= self._tol_for(v):
                return v
        return None

    def by_name(self, name: str) -> Optional[Fact]:
        for f in self.facts:
            if f.name == name:
                return f
        return None
