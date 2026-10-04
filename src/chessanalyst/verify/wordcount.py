"""Word count of §9-bis.8 (D-45), shared by V07(d), V08 and the golden measurement."""

from __future__ import annotations

import re

from chessanalyst.verify.tokens import TOKEN_RE


def count_words(text: str, word_re: str) -> int:
    """Each token is one placeholder word; ``*`` removed; the apostrophe separates."""
    text = TOKEN_RE.sub(" tok ", text).replace("*", "")
    return len(re.findall(word_re, text))


def tolerance(budget: int, tol: dict) -> float:
    return max(tol["relative"] * budget, tol["absolute"])
