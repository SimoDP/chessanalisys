"""Cards extracted from chess books (data plan: the books replace the IM's positions).

Each book thread wrote ``schede.jsonl`` (one card per game: key position, verdict of the book, key moves…).
This module checks the cards without engines (legal FEN, side to move, legal key moves) and compares the
book's verdict with an evaluation; ``scripts/books_check.py`` adds Stockfish and writes the merged catalogue.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable, Iterator
from pathlib import Path

import chess
import yaml

SIDE = {"Bianco": chess.WHITE, "Nero": chess.BLACK}


def load_settings(root: Path) -> dict:
    return yaml.safe_load((root / "config" / "books.yaml").read_text(encoding="utf-8"))


def read_cards(books_dir: Path) -> Iterator[tuple[str, dict | None, str]]:
    """(book, card or None when the line is not JSON, raw line) for every ``<book>/schede.jsonl``."""
    for f in sorted(Path(books_dir).glob("*/schede.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                yield f.parent.name, json.loads(line), line
            except json.JSONDecodeError:
                yield f.parent.name, None, line


def check_card(card: dict) -> dict:
    """Engine-free checks: ``fen_ok``, ``side_ok``, ``bad_moves`` (key moves not legal in the FEN)."""
    out: dict = {"fen_ok": False, "side_ok": False, "bad_moves": []}
    try:
        board = chess.Board(card["fen"])
    except (KeyError, ValueError):
        return out
    out["fen_ok"] = board.is_valid()
    out["side_ok"] = SIDE.get(card.get("lato")) == board.turn
    for m in card.get("mosse_chiave") or []:
        try:
            board.parse_san(m["san"])
        except (KeyError, ValueError):
            out["bad_moves"].append(m.get("san"))
    return out


def eval_class(cp_white: int | None, mate_white: int | None, s: dict) -> int:
    if mate_white is not None:
        return 2 if mate_white > 0 else -2
    c = s["eval_classes_cp"]
    a = abs(cp_white)
    k = 2 if a >= c["decisive"] else 1 if a >= c["edge"] else 0
    return k if cp_white >= 0 else -k


def agreement(verdict: str | None, cls: int, s: dict) -> str:
    """``ok``, ``diverso`` (classes far apart), ``contrario`` (opposite sides) or ``n/a``."""
    book = s["verdicts"].get(verdict)
    if book is None:
        return "n/a"
    if book * cls < 0:
        return "contrario"
    return "diverso" if abs(book - cls) >= s["disagree_distance"] else "ok"


def sample(cards: Iterable[dict], s: dict) -> list[dict]:
    """The cards for simo's spot check: a fixed random choice, so it can be rebuilt."""
    pool = sorted(cards, key=lambda c: c["id"])
    k = min(s["sample"]["size"], len(pool))
    return random.Random(s["sample"]["seed"]).sample(pool, k)
