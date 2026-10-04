"""Syzygy tablebases: downloaded and checked from M0, used from M2 (D-17, D-62)."""

from __future__ import annotations

import re
from pathlib import Path

_TB_NAME = re.compile(r"^([KQRBNP]+)v([KQRBNP]+)\.(rtbw|rtbz)$")


def pieces_of(filename: str) -> int | None:
    m = _TB_NAME.match(filename)
    if not m:
        return None
    return len(m.group(1)) + len(m.group(2))


def available(path: Path | None) -> dict[int, dict[str, int]]:
    """Number of WDL/DTZ files by piece count found in ``path``."""
    out: dict[int, dict[str, int]] = {}
    if path is None or not Path(path).is_dir():
        return out
    for f in Path(path).iterdir():
        n = pieces_of(f.name)
        if n is None:
            continue
        kind = "wdl" if f.suffix == ".rtbw" else "dtz"
        out.setdefault(n, {"wdl": 0, "dtz": 0})[kind] += 1
    return out


# Expected file counts of the complete sets (one .rtbw and one .rtbz per table).
EXPECTED_TABLES = {3: 5, 4: 30, 5: 110}


def complete_up_to(path: Path | None) -> int:
    """Largest ``n`` such that all tables with 3..n pieces are present (0 if none)."""
    found = available(path)
    best = 0
    for n in sorted(EXPECTED_TABLES):
        c = found.get(n)
        if c and c["wdl"] >= EXPECTED_TABLES[n] and c["dtz"] >= EXPECTED_TABLES[n]:
            best = n
        else:
            break
    return best
