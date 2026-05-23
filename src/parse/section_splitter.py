from __future__ import annotations

import re
from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # remove script/style
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text


def extract_section(text: str, start_patterns: list[str], end_patterns: list[str], max_chars: int = 350_000) -> str:
    """Best-effort section extractor using regex anchors.

    Filings are inconsistent. This is an MVP heuristic.
    """

    low = text.lower()

    def _find_any(patterns: list[str]) -> int:
        best = -1
        for p in patterns:
            m = re.search(p, low, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                best = m.start() if best == -1 else min(best, m.start())
        return best

    start = _find_any(start_patterns)
    if start == -1:
        return ""

    # cut off to max window to keep regex fast
    window = low[start : start + max_chars]

    end = -1
    for p in end_patterns:
        m = re.search(p, window, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            end = m.start()
            break

    if end == -1:
        section = text[start : start + max_chars]
    else:
        section = text[start : start + end]

    # cleanup excessive whitespace
    section = re.sub(r"\n{3,}", "\n\n", section)
    return section.strip()


def extract_risk_factors(text: str) -> str:
    return extract_section(
        text,
        start_patterns=[r"item\s*1a\.?\s*risk\s*factors"],
        end_patterns=[r"item\s*1b", r"item\s*2"],
    )


def extract_mdna(text: str) -> str:
    return extract_section(
        text,
        start_patterns=[r"item\s*7\.?\s*management.?s\s*discussion", r"item\s*7\.?\s*md&a"],
        end_patterns=[r"item\s*7a", r"item\s*8"],
    )
