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


PIECES = (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


def pseudo_moves(board: chess.Board, sq: chess.Square) -> chess.SquareSet:
    """Pseudo-legal destinations of the (non-pawn, non-king) piece on ``sq``."""
    return board.attacks(sq) & ~board.occupied_co[board.color_at(sq)]


def pawn_attacked(board: chess.Board, side: chess.Color) -> chess.SquareSet:
    out = chess.SquareSet()
    for p in board.pieces(chess.PAWN, side):
        out |= board.attacks(p)
    return out


def mobility(board: chess.Board, side: chess.Color) -> dict[str, int]:
    """M3 ``piece_mobility``: per piece, pseudo-legal moves to squares not attacked by O's pawns."""
    bad = pawn_attacked(board, not side)
    return {chess.square_name(sq): len(pseudo_moves(board, sq) & ~bad)
            for t in PIECES for sq in board.pieces(t, side)}


def activity_m3_features(board: chess.Board, geo) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        mob = mobility(board, side)
        if mob:
            out.append(Feature("piece_mobility", s, sorted(mob), dict(sorted(mob.items()))))
        for name, n in sorted(mob.items()):
            if board.piece_type_at(chess.parse_square(name)) in (chess.KNIGHT, chess.BISHOP, chess.ROOK) \
                    and n <= geo.inactive_mobility_max:
                out.append(Feature("inactive_piece", s, [name]))
        for sq in sorted(board.pieces(chess.BISHOP, side)):
            if len(pseudo_moves(board, sq)) >= geo.bishop_open_min_moves:
                out.append(Feature("bishop_diagonal_open", s, names([sq])))
    space = {}
    for side in (chess.WHITE, chess.BLACK):
        att = pawn_attacked(board, side)
        space[side] = sum(1 for sq in att if rr(side, sq) >= 5)
    for side in (chess.WHITE, chess.BLACK):
        diff = space[side] - space[not side]
        if diff >= geo.space_min_diff:
            out.append(Feature("space_advantage", code(side), [], diff))
    pawns_all = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
    for f in range(8):
        if any(chess.square_file(p) == f for p in pawns_all):
            continue
        heavy = {side: [sq for t in (chess.ROOK, chess.QUEEN) for sq in board.pieces(t, side)
                        if chess.square_file(sq) == f] for side in (chess.WHITE, chess.BLACK)}
        owners = [side for side in (chess.WHITE, chess.BLACK) if heavy[side]]
        if len(owners) == 1:
            out.append(Feature("file_control", code(owners[0]), names(heavy[owners[0]]), chess.FILE_NAMES[f]))
    return out
