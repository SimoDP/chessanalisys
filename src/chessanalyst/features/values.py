"""Piece values and board conventions (§5.1). The values are the only numeric
constants allowed in the code (instructions point 5)."""

from __future__ import annotations

import chess

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
MINORS = (chess.KNIGHT, chess.BISHOP)
COLOR_CODE = {chess.WHITE: "w", chess.BLACK: "b"}


def piece_value(piece_type: int | None) -> int:
    return VALUES.get(piece_type, 0) if piece_type else 0


def rr(side: chess.Color, square: chess.Square) -> int:
    """Relative rank of ``square`` seen from ``side`` (1 = own first rank)."""
    r = chess.square_rank(square) + 1
    return r if side == chess.WHITE else 9 - r


def code(side: chess.Color | None) -> str | None:
    return None if side is None else COLOR_CODE[side]


def names(squares) -> list[str]:
    return sorted(chess.square_name(s) for s in squares)


def material(board: chess.Board, side: chess.Color) -> int:
    return sum(piece_value(p.piece_type) for p in board.piece_map().values() if p.color == side)


def nonpawn_material(board: chess.Board, side: chess.Color) -> int:
    return sum(piece_value(p.piece_type) for p in board.piece_map().values()
               if p.color == side and p.piece_type not in (chess.PAWN, chess.KING))
