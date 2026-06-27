"""Minimal usage example: build a fact set, evaluate two drafts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from numguard import Fact, FactSet, evaluate  # noqa: E402

facts = FactSet(facts=[
    Fact("n_treated", 24, "participants"),
    Fact("pct_any_ae", 79.2, "%"),
])
banned = ["well tolerated"]

good = "Of 24 participants, 79.2% reported an adverse event."
bad = "Of 24 participants, 83.0% reported an adverse event; the drug was well tolerated."

for label, text in [("good", good), ("bad", bad)]:
    report = evaluate(text, facts, banned_phrases=banned, required_names=["pct_any_ae"])
    print(f"\n[{label}] {text}")
    print(report.scorecard())
