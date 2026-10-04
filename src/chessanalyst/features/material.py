"""Material features (§5.1)."""

from __future__ import annotations

import chess

from chessanalyst.features.model import Feature
from chessanalyst.features.values import MINORS, code, material, names


def _bishops(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    return list(board.pieces(chess.BISHOP, side))


def _square_color(sq: chess.Square) -> int:
    return (chess.square_file(sq) + chess.square_rank(sq)) % 2


def material_features(board: chess.Board) -> list[Feature]:
    out = [Feature("material_balance", None, [], material(board, chess.WHITE) - material(board, chess.BLACK))]
    for side in (chess.WHITE, chess.BLACK):
        mine, theirs = _bishops(board, side), _bishops(board, not side)
        if len({_square_color(s) for s in mine}) == 2 and len({_square_color(s) for s in theirs}) < 2:
            out.append(Feature("bishop_pair", code(side), names(mine)))
    wb, bb = _bishops(board, chess.WHITE), _bishops(board, chess.BLACK)
    if len(wb) == 1 and len(bb) == 1 and _square_color(wb[0]) != _square_color(bb[0]):
        out.append(Feature("opposite_bishops", None, names(wb + bb)))
    for side in (chess.WHITE, chess.BLACK):
        rooks = len(board.pieces(chess.ROOK, side)) - len(board.pieces(chess.ROOK, not side))
        minors_s = sum(len(board.pieces(t, side)) for t in MINORS)
        minors_o = sum(len(board.pieces(t, not side)) for t in MINORS)
        if rooks == 1 and minors_o - minors_s == 1:
            out.append(Feature("exchange_up", code(side)))
    return out
