"""Deterministic numeric-membership, banned-phrase and required-value checks.

Passing the implemented checks does not certify units, claim semantics, upstream
truth or completeness. See NUMERIC_CONTRACT.md for the numeric grammar and
configuration validation. No third-party runtime dependencies.
"""
from .facts import Fact, FactSet
from .report import Finding, Report
from .evaluator import evaluate
from .loader import load_case

__all__ = ["Fact", "FactSet", "Finding", "Report", "evaluate", "load_case"]
__version__ = "0.1.0"
