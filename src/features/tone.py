from __future__ import annotations

import re


UNCERTAINTY_TERMS = [
    "uncertain",
    "uncertainty",
    "may",
    "might",
    "could",
    "headwind",
    "risk",
    "risks",
    "materially",
    "adversely",
    "expects",
    "expect",
    "believe",
    "anticipate",
]


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text.lower()))


def uncertainty_per_1k_words(text: str) -> float:
    low = text.lower()
    wc = word_count(low)
    if wc == 0:
        return 0.0
    hits = 0
    for t in UNCERTAINTY_TERMS:
        hits += len(re.findall(rf"\b{re.escape(t)}\b", low))
    return (hits / wc) * 1000.0
