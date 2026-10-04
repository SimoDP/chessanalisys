"""Opening index from ``lichess-org/chess-openings`` (CC0, D-59, §3.3).

At setup the TSV files ``a.tsv`` … ``e.tsv`` (columns ``eco``, ``name``,
``pgn``) are replayed and ``data/openings_index.json`` maps
``EPD → {eco, name, plies}``. When several rows reach the same EPD the one
with more plies wins, ties by file order. M1 looks up by exact EPD; lookup by
sequence arrives in M2.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from pathlib import Path

import chess
import chess.pgn

TSV_FILES = ("a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv")


def epd_of(board: chess.Board) -> str:
    return board.epd(en_passant="legal")


def parse_tsv(text: str) -> Iterable[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for row in reader:
        yield row


def build_index(rows: Iterable[dict[str, str]]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for row in rows:
        game = chess.pgn.read_game(io.StringIO(row["pgn"]))
        if game is None or game.errors:
            raise ValueError(f"PGN non valido nell'indice delle aperture: {row}")
        board = game.board()
        plies = 0
        for mv in game.mainline_moves():
            board.push(mv)
            plies += 1
        epd = epd_of(board)
        entry = {"eco": row["eco"], "name": row["name"], "plies": plies}
        old = index.get(epd)
        if old is None or plies > old["plies"]:
            index[epd] = entry
    return index


def build_index_from_dir(directory: Path) -> dict[str, dict]:
    rows: list[dict[str, str]] = []
    for name in TSV_FILES:
        rows.extend(parse_tsv((directory / name).read_text(encoding="utf-8")))
    return build_index(rows)


def write_index(index: dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True, indent=0), encoding="utf-8")


class OpeningIndex:
    def __init__(self, index: dict[str, dict]) -> None:
        self.index = index

    @classmethod
    def load(cls, path: Path) -> "OpeningIndex":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def __len__(self) -> int:
        return len(self.index)

    def lookup_epd(self, board: chess.Board) -> dict | None:
        return self.index.get(epd_of(board))
