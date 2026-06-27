from __future__ import annotations

import re
from typing import List, Tuple

# Match standalone numbers: integers, decimals, and thousands-separated values.
# The lookbehind keeps us from matching digits embedded in identifiers
# (e.g. "CP101" or "v2"), which would otherwise create false guardrail hits.
_NUM_RE = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)")


def extract_numbers(text: str) -> List[Tuple[float, str, int]]:
    """Return ``(value, raw_string, position)`` for every standalone number.

    Percent signs and surrounding punctuation are ignored -- only the numeric
    magnitude is returned, since 79.2 and "79.2%" reference the same fact.
    """
    out: List[Tuple[float, str, int]] = []
    for m in _NUM_RE.finditer(text):
        raw = m.group(1)
        try:
            val = float(raw.replace(",", ""))
        except ValueError:  # pragma: no cover - regex guarantees a number
            continue
        out.append((val, raw, m.start()))
    return out
