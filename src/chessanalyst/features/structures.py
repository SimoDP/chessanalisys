"""D-79: pawn structures of the books' catalogue (``config/structures.yaml``), recognised from the pawns.

Each structure is written for its owner as White; a position is also matched with the colours swapped
(``board.mirror()``), and then the squares of its texts are mirrored too. The first structure of the catalogue
that matches wins.
"""

from __future__ import annotations

import re
from typing import Any

import chess

SQUARE_RE = re.compile(r"\{([a-h])([1-8])?\}")


def _side_ok(board: chess.Board, side: chess.Color, rule: dict[str, Any]) -> bool:
    own = board.pieces(chess.PAWN, side)
    if any(chess.parse_square(s) not in own for s in rule.get("pawns", [])):
        return False
    if any(not any(chess.parse_square(s) in own for s in group) for group in rule.get("any_of", [])):
        return False
    if any(chess.parse_square(s) in own for s in rule.get("absent", [])):
        return False
    return not any(own & chess.BB_FILES[chess.FILE_NAMES.index(f)] for f in rule.get("no_files", []))


def match(board: chess.Board, rule: dict[str, Any]) -> bool:
    """``rule`` (``owner_pawns``, ``other_pawns``) matches with White as the owner."""
    return _side_ok(board, chess.WHITE, rule["owner_pawns"]) and _side_ok(board, chess.BLACK, rule["other_pawns"])


def find_structure(board: chess.Board, catalogue: dict[str, dict]) -> tuple[str, chess.Color] | None:
    """(id, colour of the owner) of the first structure of ``catalogue`` that ``board`` has, or None."""
    mirrored = board.mirror()
    for sid, rule in catalogue.items():
        if match(board, rule):
            return sid, chess.WHITE
        if match(mirrored, rule):
            return sid, chess.BLACK
    return None


def place(text: str, owner: chess.Color) -> str:
    """The squares ``{d5}`` and files ``{c}`` of a catalogue text, for an owner of colour ``owner``."""
    def sub(m: re.Match) -> str:
        f, r = m.group(1), m.group(2)
        if r is None:
            return f
        return f + (r if owner == chess.WHITE else str(9 - int(r)))
    return SQUARE_RE.sub(sub, text)
