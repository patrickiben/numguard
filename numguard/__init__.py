"""numguard -- evaluation harness & guardrail for LLM output in regulated domains.

Core thesis: *the model never sources a number.* A deterministic validator
checks that every number in a generated draft is traceable to an allowed fact,
that no banned qualitative claims appear, and that all required facts are
present. The language model (if any) only produces prose; numguard judges it.

No third-party dependencies. See README.md and run ``python selftest.py``.
"""
from .facts import Fact, FactSet
from .report import Finding, Report
from .evaluator import evaluate
from .loader import load_case

__all__ = ["Fact", "FactSet", "Finding", "Report", "evaluate", "load_case"]
__version__ = "0.1.0"
