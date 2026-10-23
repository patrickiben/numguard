"""Command-line entry point: ``python -m numguard <case.json> [--json ...] [--junit ...]``.

Evaluates every candidate draft in a case and (optionally) writes JSON / JUnit
results for CI. Exit code is 0 when every verdict matches expectations and 1 otherwise.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from .evaluator import evaluate
from .export import record_ok, reports_to_json, reports_to_junit
from .loader import load_case


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="numguard",
        description="Evaluate LLM drafts against a fact set; export results for CI.",
    )
    parser.add_argument("case", help="path to a JSON case file")
    parser.add_argument("--json", dest="json_out", help="write JSON results here")
    parser.add_argument("--junit", dest="junit_out", help="write JUnit XML results here")
    parser.add_argument("--quiet", action="store_true", help="suppress scorecards")
    args = parser.parse_args(argv)

    case = load_case(args.case)
    classname = case["name"] or os.path.basename(args.case)

    records = []
    for cand in case["candidates"]:
        report = evaluate(
            cand["text"], case["factset"],
            case["banned_phrases"], case["required_names"],
        )
        records.append({
            "name": cand.get("label", "candidate"),
            "classname": classname,
            "expected": cand.get("expected"),
            "report": report,
        })
        if not args.quiet:
            verdict = "pass" if report.passed else "fail"
            print(f"[{cand.get('label', 'candidate')}] verdict={verdict}")
            print(report.scorecard())
            print("-" * 60)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(reports_to_json(records))
        print(f"wrote {args.json_out}")
    if args.junit_out:
        with open(args.junit_out, "w", encoding="utf-8") as fh:
            fh.write(reports_to_junit(records))
        print(f"wrote {args.junit_out}")

    not_ok = sum(0 if record_ok(r["report"], r.get("expected")) else 1 for r in records)
    if not_ok:
        print(f"{not_ok} record(s) did not match expectations.", file=sys.stderr)
    return 1 if not_ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
