from __future__ import annotations

import re


GUIDANCE_VERBS = [
    "expect",
    "expects",
    "expected",
    "anticipate",
    "anticipates",
    "anticipating",
    "forecast",
    "forecasts",
    "project",
    "projects",
    "guidance",
    "outlook",
]


def guidance_verbs_per_1k_words(text: str) -> float:
    low = (text or "").lower()
    words = len(re.findall(r"\b\w+\b", low))
    if words == 0:
        return 0.0

    hits = 0
    for v in GUIDANCE_VERBS:
        hits += len(re.findall(rf"\b{re.escape(v)}\b", low))

    return (hits / words) * 1000.0
