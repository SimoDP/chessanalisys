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


# --- probing (M2) ----------------------------------------------------------------

# WDL of python-chess from the side to move: 2 win, 1 cursed win (draw with the
# 50-move rule), 0 draw, -1 blessed loss, -2 loss.
RESULT_KEYS = {2: "win", 1: "cursed_win", 0: "draw", -1: "blessed_loss", -2: "loss"}


class Tablebase:
    """Direct probe of the Syzygy tables (§3.3, D-62): WDL and DTZ for the side to move.

    Only positions with at most ``max_pieces`` pieces (kings included) whose tables
    are present are covered; ``probe`` returns None otherwise.
    """

    def __init__(self, path: Path, max_pieces: int) -> None:
        import chess.syzygy

        self.path = Path(path)
        self.max_pieces = max_pieces
        self._tb = chess.syzygy.open_tablebase(str(self.path))
        self.records: dict[str, dict] = {}         # epd → probe, for the recorded fixtures

    def close(self) -> None:
        self._tb.close()

    def probe(self, board) -> dict | None:
        if chess_popcount(board) > self.max_pieces:
            return None
        epd = board.epd(en_passant="legal")
        try:
            res = {"wdl": self._tb.probe_wdl(board), "dtz": self._tb.probe_dtz(board)}
        except (KeyError, ValueError):            # missing table or position not probeable (castling rights)
            res = None
        self.records[epd] = res
        return res


class RecordedTablebase:
    """Tablebase answers read from ``fixtures/recorded/syzygy`` (tests without the tables)."""

    def __init__(self, records: dict[str, dict | None], max_pieces: int) -> None:
        self.records = records
        self.max_pieces = max_pieces

    def probe(self, board) -> dict | None:
        if chess_popcount(board) > self.max_pieces:
            return None
        return self.records.get(board.epd(en_passant="legal"))


def recorded_tablebase(cfg) -> RecordedTablebase:
    """All the probes in ``fixtures/recorded/syzygy/*.json``."""
    import json

    records: dict[str, dict | None] = {}
    for f in sorted((cfg.project_root / "fixtures" / "recorded" / "syzygy").glob("*.json")):
        records.update(json.loads(f.read_text(encoding="utf-8")))
    return RecordedTablebase(records, cfg.default.engines.syzygy.max_pieces)


def chess_popcount(board) -> int:
    return bin(board.occupied).count("1")


def tablebase_entry(probe: dict, side_to_move_is_user: bool) -> dict:
    """``pack.tablebase``: WDL and DTZ from the user's point of view and the key of the result text."""
    sign = 1 if side_to_move_is_user else -1
    wdl = sign * probe["wdl"]
    return {"wdl": wdl, "dtz": sign * probe["dtz"], "result_text_key": RESULT_KEYS[wdl]}
