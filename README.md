# numguard

**A zero-dependency checker for numeric value membership in generated drafts, with banned-phrase and required-fact checks.**

![ci](https://github.com/patrickiben/numguard/actions/workflows/ci.yml/badge.svg)
&nbsp;·&nbsp; Python ≥ 3.9 &nbsp;·&nbsp; zero runtime dependencies &nbsp;·&nbsp; MIT

`numguard` deterministically checks recognized numeric tokens in a draft against an explicit fact set, flags listed banned phrases, and verifies required fact values. The model writes prose; the checker provides a review signal, and a qualified human signs the output.

> **Scope:** numeric membership is not factual correctness. Units, sentence attribution, spelled-out numbers, completeness, and qualitative meaning remain unverified. For example, a count of 19 can still be misused as `19%`. Signed decimals, leading decimals and scientific notation are supported; malformed formats fail. See [the numeric contract](NUMERIC_CONTRACT.md) and the executable known-gap tests before using the verdict.

> This is the generalized, open core of a clinical TLF auto-narrative tool I built, where a local model drafts text but is architecturally forbidden from owning a single figure.

---

## The idea in one picture

```
   allowed facts  ──►  model draft  ──►  numeric / phrase checks  ──►  human review
   (values + units)     (untrusted)       (declared formats and         (meaning, units,
                                          configured tolerances)      completeness)
```

Each recognized numeric value must match an allowed value within the configured tolerance. This is a value-membership check; it does not bind a value to a particular statement or unit.

---

## Quickstart (no install, no dependencies)

```bash
python selftest.py
```

Real output:

```
case: Adverse-event overview narrative (synthetic CP-101)

========================================================================
[OK] candidate 'grounded_draft'  expected=pass  got=pass
  draft: In the safety population (N=24), 19 participants (79.2%) experienced ...
  verdict: PASS  (0 error(s), 0 warning(s))
   - no findings: recognized numeric values match allowed facts; no listed banned phrases.
========================================================================
[OK] candidate 'hallucinated_draft'  expected=fail  got=fail
  draft: In the safety population (N=24), 18 participants (75.0%) experienced ...
  verdict: FAIL  (4 error(s), 0 warning(s))
   - [ERROR] numbers_grounded: Untraceable number '18' is not supported by any fact.
   - [ERROR] numbers_grounded: Untraceable number '75.0' is not supported by any fact.
   - [ERROR] unsupported_claims: Unsupported qualitative claim: 'well tolerated'.
   - [ERROR] required_facts: Required fact 'pct_any_ae' (79.2 %) is missing from the text.
========================================================================
SELFTEST PASSED -- guard behaves as specified (hallucinated numbers and banned claims rejected).
```

The grounded draft passes; the draft with two fabricated numbers (`18`, `75.0`) and an unsupported claim (`well tolerated`) is rejected — and the missing required figure is caught too.

---

## Programmatic use

```python
from numguard import Fact, FactSet, evaluate

facts = FactSet(facts=[
    Fact("n_treated", 24, "participants"),
    Fact("pct_any_ae", 79.2, "%"),
])

report = evaluate(
    "Of 24 participants, 83.0% reported an adverse event; the drug was well tolerated.",
    facts,
    banned_phrases=["well tolerated"],
    required_names=["pct_any_ae"],
)

print(report.passed)        # False
print(report.scorecard())   # itemized findings
```

---

## How it works

`evaluate()` runs three deterministic checks and returns a `Report` (it `passed` only if there are zero `ERROR` findings):

| Check | What it enforces | Severity |
|-------|------------------|----------|
| `numbers_grounded` | Each recognized numeric value matches an allowed fact value within tolerance. | ERROR |
| `unsupported_claims` | No banned qualitative phrasing (e.g. `well tolerated`, `safe and effective`). | ERROR |
| `required_facts` | Every required fact's value actually appears in the text. | ERROR |

The **`FactSet`** is the contract: the facts (named values + units), optional `context_values` (numbers allowed but not required, e.g. a phase number, so they don't false-positive), and match tolerances (`abs_tol`, `rel_tol`). The shared [numeric contract](NUMERIC_CONTRACT.md) supports signs, leading decimals and exponents, and deliberately ignores letter-led identifiers such as `CP101` and `CP-101`. Unknown/nonnumeric required names, duplicate facts, non-finite values and invalid tolerances raise `ValueError`; malformed draft numeric tokens produce a failing `numeric_format` finding.

---

## Declarative test cases

Cases are plain JSON — facts, banned phrases, required facts, and labeled candidate drafts with an `expected` verdict, so a whole narrative type can be regression-tested in CI:

```json
{
  "name": "Adverse-event overview narrative (synthetic CP-101)",
  "facts": [
    {"name": "n_treated", "value": 24, "unit": "participants"},
    {"name": "pct_any_ae", "value": 79.2, "unit": "%"}
  ],
  "banned_phrases": ["well tolerated"],
  "required_names": ["n_treated", "pct_any_ae"],
  "candidates": [
    {"label": "grounded_draft", "expected": "pass", "text": "..."},
    {"label": "hallucinated_draft", "expected": "fail", "text": "..."}
  ]
}
```

See [`cases/ae_overview.json`](cases/ae_overview.json).

---

## CI integration & exports

Run a whole case from the command line and emit machine-readable results:

```bash
python -m numguard cases/ae_overview.json --json results.json --junit results.xml
```

- **JUnit XML** (`--junit`) drops straight into GitHub Actions, GitLab, or Jenkins test dashboards. In **regression mode** (each candidate has an `expected` verdict) a `<failure>` appears when the guard misbehaves; in **validation mode** (no `expected`) a `<failure>` appears for any draft that fails the gate — so you can wire real generated drafts through CI and fail the build on any ungrounded number.
- **JSON** (`--json`) gives a structured summary (`total`, `all_ok`, per-case findings) for custom dashboards.

The CLI exits 0 when every record matches its expected verdict, and 1 otherwise.

## Design principles

- **The validator is deterministic.** Numeric membership and phrase checks live in code that can be read, tested, and audited.
- **Reject invalid contracts.** A draft passes only the implemented checks; invalid configuration raises an error. A passing report does not approve the draft for release.
- **Human-in-the-loop by design.** `numguard` gates a draft; it never approves one for release.
- **Zero dependencies, everything runs.** Pure standard library; `python selftest.py` works on a clean machine. Every file parses; the suite is green in CI.
- **Synthetic data only.** The bundled example is a synthetic CP-101 study — no real or proprietary data.

---

## Project layout

```
numguard/
├── numguard/            # the package
│   ├── facts.py         # Fact, FactSet (the allowed values + tolerances)
│   ├── extract.py       # deterministic number extraction
│   ├── checks.py        # the three guardrail checks
│   ├── evaluator.py     # evaluate() -> Report
│   ├── report.py        # Finding, Report, scorecard
│   └── loader.py        # load declarative JSON cases
├── cases/ae_overview.json
├── tests/test_selftest.py
├── examples/demo.py
├── selftest.py          # zero-dependency runnable proof
└── .github/workflows/ci.yml
```

Run the tests with `python -m pytest -q` (or just `python selftest.py`). CI checks Python 3.9, 3.12 and 3.14, plus an isolated wheel import.

---

## Roadmap

This is the working core of a larger evaluation track:

- [x] **Scorecard export** (JSON / JUnit) for CI dashboards
- [x] **Companion lexical RAG screening**: [`grounded-rag`](https://github.com/patrickiben/grounded-rag), with explicit semantic limitations
- [ ] **Pluggable checks** (units consistency, date grounding, directional-claim checks)
- [ ] **`promptfoo` / `inspect` adapters** so it drops into existing eval pipelines
- [ ] **A thin LLM-drafting demo** wired to a local model, end to end

---

## Status & honesty note

`numguard` is a **working proof-of-concept**, not validated software for production regulatory use. The core checks run and are tested; the bundled data is synthetic. It demonstrates a safety *pattern* — deterministic grounding of LLM output — that I believe regulated AI needs. Use it as a starting point, not a finished compliance tool.

## License

MIT — see [LICENSE](LICENSE). Built by Patrick Iben (`p.iben@saeny.net`).
