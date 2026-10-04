"""V09: terms of other openings (``examples/golden/fewshot/_terms.txt``, D-52)."""

from __future__ import annotations

import re
from pathlib import Path

from chessanalyst.verify.tokens import TOKEN_RE


def load_terms(path: Path) -> list[list[str]]:
    """One group of aliases per line (``attacco inglese|English Attack``); ``#`` comments."""
    groups = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            groups.append([a.strip() for a in line.split("|") if a.strip()])
    return groups


def _has(term: str, text: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE) is not None


class Contamination:
    def __init__(self, groups: list[list[str]], opening_name: str | None) -> None:
        name = opening_name or ""
        self.forbidden = [g for g in groups if not any(_has(a, name) for a in g)]

    def hits(self, text: str) -> list[str]:
        free = TOKEN_RE.sub(" ", text)
        return [a for g in self.forbidden for a in g if _has(a, free)]
