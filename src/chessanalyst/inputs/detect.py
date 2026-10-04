"""``detect_format`` (§2-bis.2)."""

from __future__ import annotations

import re

from chessanalyst.errors import InputError

_FEN_PREFIX = re.compile(r"^\s*fen\s*:\s*", re.IGNORECASE)


def clean(text: str) -> str:
    text = text.lstrip("﻿").strip()
    return _FEN_PREFIX.sub("", text, count=1).strip()


def detect_format(text: str, messages: dict[str, str]) -> str:
    t = clean(text)
    lines = [ln for ln in t.splitlines() if ln.strip()]
    if len(lines) == 1:
        fields = lines[0].split()
        if fields and fields[0].count("/") == 7 and 4 <= len(fields) <= 6:
            return "fen"
    if any(ln.strip().startswith("[") and ln.strip().endswith("]") for ln in lines) or re.search(r"\b1\.", t):
        return "pgn"
    raise InputError(messages["unknown_format"])
