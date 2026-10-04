"""Piece activity and development features (§5.1, M1 subset)."""

from __future__ import annotations

import chess

from chessanalyst.features.model import Feature
from chessanalyst.features.values import MINORS, code, names, rr

START_SQUARES = {
    chess.WHITE: {chess.B1: chess.KNIGHT, chess.G1: chess.KNIGHT, chess.C1: chess.BISHOP, chess.F1: chess.BISHOP},
    chess.BLACK: {chess.B8: chess.KNIGHT, chess.G8: chess.KNIGHT, chess.C8: chess.BISHOP, chess.F8: chess.BISHOP},
}
CENTER = (chess.D4, chess.E4, chess.D5, chess.E5)


def _undeveloped(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    return [sq for sq, pt in START_SQUARES[side].items()
            if (p := board.piece_at(sq)) is not None and p.color == side and p.piece_type == pt]


def development(board: chess.Board, side: chess.Color, castled: bool) -> int:
    minors = sum(len(board.pieces(t, side)) for t in MINORS)
    return minors - len(_undeveloped(board, side)) + (1 if castled else 0)


def activity_features(board: chess.Board, castling: dict[str, str]) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        for sq in sorted(board.pieces(chess.ROOK, side)):
            f = chess.square_file(sq)
            file_pawns = [p for p in board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
                          if chess.square_file(p) == f]
            if not file_pawns:
                out.append(Feature("rook_open_file", s, names([sq]), "open"))
            elif not any(board.color_at(p) == side for p in file_pawns):
                out.append(Feature("rook_open_file", s, names([sq]), "semi_open"))
            if rr(side, sq) == 7:
                out.append(Feature("rook_seventh", s, names([sq])))
        und = _undeveloped(board, side)
        if und:
            out.append(Feature("undeveloped_pieces", s, names(und)))
    dev = {side: development(board, side, castling[code(side)].startswith("castled"))
           for side in (chess.WHITE, chess.BLACK)}
    for side in (chess.WHITE, chess.BLACK):
        diff = dev[side] - dev[not side]
        if diff >= 2:
            out.append(Feature("development_lead", code(side), [], diff))
    control = {code(side): sum(len(board.attackers(side, sq)) for sq in CENTER) for side in (chess.WHITE, chess.BLACK)}
    out.append(Feature("central_control", None, [], control))
    return out
