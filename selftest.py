#!/usr/bin/env python3
"""Zero-dependency self-test.

Proves the guardrail behaves as specified: a grounded draft passes, and a
draft containing fabricated numbers and a banned claim is rejected. Run with::

    python selftest.py

Exits 0 if every candidate's verdict matches its declared expectation, 1 if not.
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from numguard.evaluator import evaluate  # noqa: E402
from numguard.loader import load_case  # noqa: E402


def main() -> int:
    case = load_case(os.path.join(BASE, "cases", "ae_overview.json"))
    print(f"case: {case['name']}\n")

    all_ok = True
    for cand in case["candidates"]:
        report = evaluate(
            cand["text"],
            case["factset"],
            banned_phrases=case["banned_phrases"],
            required_names=case["required_names"],
        )
        verdict = "pass" if report.passed else "fail"
        ok = verdict == cand["expected"]
        all_ok = all_ok and ok
        status = "OK" if ok else "UNEXPECTED"

        print("=" * 72)
        print(
            f"[{status}] candidate '{cand['label']}'  "
            f"expected={cand['expected']}  got={verdict}"
        )
        print(f"  draft: {cand['text']}")
        print(report.scorecard())

    print("=" * 72)
    if all_ok:
        print("SELFTEST PASSED -- guard behaves as specified "
              "(hallucinated numbers and banned claims rejected).")
        return 0
    print("SELFTEST FAILED -- guard did not behave as specified.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
