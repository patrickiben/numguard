# numguard

**An evaluation harness and guardrail for LLM output in regulated domains — built on one rule: _the model never sources a number._**

![ci](https://github.com/patrickiben/numguard/actions/workflows/ci.yml/badge.svg)
&nbsp;·&nbsp; Python ≥ 3.9 &nbsp;·&nbsp; zero runtime dependencies &nbsp;·&nbsp; MIT

The single biggest fear about using LLMs near regulated output — clinical reports, safety narratives, financial filings — is a **hallucinated number** slipping into a document a human signs. `numguard` removes that failure mode by construction: a **deterministic validator** checks that every number in a generated draft is traceable to an allowed fact, that no banned qualitative claims appear, and that all required facts are present. The language model only writes prose; `numguard` judges it. Nothing is approved without passing the gate, and a human still signs.

> This is the generalized, open core of a clinical TLF auto-narrative tool I built, where a local model drafts text but is architecturally forbidden from owning a single figure.

---

## The idea in one picture

```
   deterministic facts  ──►  LLM writes prose  ──►  numguard validates  ──►  human signs
   (the only numbers          (no new numbers       (rejects any number      (gate must be
    that may appear)           may be invented)       not traceable to a       PASS first)
                                                      fact + banned claims)
```

The model can phrase, summarize, and arrange — but every number in its output must already exist in the fact set. Anything else was, by definition, sourced by the model, and is rejected.

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
   - no findings: every number is traceable; no banned claims.
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
| `numbers_grounded` | Every number in the text matches an allowed fact value (within tolerance). **This is the core guardrail.** | ERROR |
| `unsupported_claims` | No banned qualitative phrasing (e.g. `well tolerated`, `safe and effective`). | ERROR |
| `required_facts` | Every required fact's value actually appears in the text. | ERROR |

The **`FactSet`** is the contract: the facts (named values + units), optional `context_values` (numbers allowed but not required, e.g. a phase number, so they don't false-positive), and match tolerances (`abs_tol`, `rel_tol`). Number extraction is regex-based and deliberately ignores digits embedded in identifiers (so `CP101` is not read as `101`).

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

The CLI exit code is the count of records that didn't match expectations, so a CI job fails cleanly when the guard is breached.

## Design principles

- **The validator is deterministic; the model is not trusted with numbers.** Safety lives in code that can be read, tested, and audited — not in a prompt.
- **Fail closed.** A draft passes only if it has zero errors. Silence is not approval.
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

Run the tests with `pytest -q` (or just `python selftest.py`).

---

## Roadmap

This is the working core of a larger evaluation track:

- [x] **Scorecard export** (JSON / JUnit) for CI dashboards
- [ ] **Grounding for RAG**: flag answer spans not supported by retrieved sources
- [ ] **Pluggable checks** (units consistency, date grounding, directional-claim checks)
- [ ] **`promptfoo` / `inspect` adapters** so it drops into existing eval pipelines
- [ ] **A thin LLM-drafting demo** wired to a local model, end to end

---

## Status & honesty note

`numguard` is a **working proof-of-concept**, not validated software for production regulatory use. The core checks run and are tested; the bundled data is synthetic. It demonstrates a safety *pattern* — deterministic grounding of LLM output — that I believe regulated AI needs. Use it as a starting point, not a finished compliance tool.

## License

MIT — see [LICENSE](LICENSE). Built by Patrick Iben (`p.iben@saeny.net`).
