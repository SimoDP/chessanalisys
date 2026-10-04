"""``read_source`` (§2-bis.2): file path or pasted text."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


def read_source(value: str) -> str:
    """If ``value`` (stripped) is an existing file, read it (UTF-8, BOM tolerated);
    otherwise it is pasted text."""
    candidate = value.strip()
    if candidate and "\n" not in candidate:
        try:
            p = Path(candidate).expanduser()
            if p.is_file():
                return p.read_text(encoding="utf-8-sig")
        except (OSError, ValueError):
            pass
    return value


def read_stdin(stream: TextIO | None = None) -> str:
    return (stream or sys.stdin).read()


def read_interactive(first_line: str, next_line) -> str:
    """Interactive reading: a first line that is an existing path is read as a
    file; otherwise lines are read until a line with only ``.`` or EOF (empty
    lines do not terminate, PGN contains them)."""
    p = Path(first_line.strip()).expanduser() if first_line.strip() else None
    if p is not None:
        try:
            if p.is_file():
                return p.read_text(encoding="utf-8-sig")
        except (OSError, ValueError):
            pass
    lines = [first_line]
    while True:
        try:
            line = next_line()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines)
