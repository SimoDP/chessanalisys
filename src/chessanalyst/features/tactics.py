"""Tactical features (§5.1, M1 subset)."""

from __future__ import annotations

import chess

from chessanalyst.features.model import Feature
from chessanalyst.features.see import see_move
from chessanalyst.features.values import code, names, piece_value


def _pinner(board: chess.Board, side: chess.Color, sq: chess.Square) -> chess.Square | None:
    ray = board.pin(side, sq)
    for s in ray:
        p = board.piece_at(s)
        if p and p.color != side and p.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            return s
    return None


def hanging_squares(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    """Pieces of ``side`` (no pawns, no king) attacked and undefended, or attacked
    by a piece of lower value (D-32)."""
    out = []
    for sq, p in board.piece_map().items():
        if p.color != side or p.piece_type in (chess.PAWN, chess.KING):
            continue
        attackers = board.attackers(not side, sq)
        if not attackers:
            continue
        defended = bool(board.attackers(side, sq))
        lower = any(piece_value(board.piece_type_at(a)) < piece_value(p.piece_type) for a in attackers)
        if not defended or lower:
            out.append(sq)
    return out


def unresolved_captures(board: chess.Board, see_min: int) -> list[tuple[chess.Move, int]]:
    out = []
    for mv in board.legal_moves:
        if board.is_capture(mv):
            v = see_move(board, mv)
            if v >= see_min:
                out.append((mv, v))
    return sorted(out, key=lambda x: (x[0].from_square, x[0].to_square))


def tactic_features(board: chess.Board, see_min: int, e0_best_mate_white: int | None) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        king = board.king(side)
        for sq in sorted(board.piece_map()):
            p = board.piece_at(sq)
            if p.color == side and sq != king and board.is_pinned(side, sq):
                pinner = _pinner(board, side, sq)
                out.append(Feature("pin", s, [chess.square_name(sq)] + ([chess.square_name(pinner)] if pinner is not None else [])))
        for sq in sorted(hanging_squares(board, side)):
            out.append(Feature("hanging_piece", s, names([sq])))
    if e0_best_mate_white is not None:
        mater = chess.WHITE if e0_best_mate_white > 0 else chess.BLACK
        out.append(Feature("mate_in_n", code(mater), [], abs(e0_best_mate_white)))
    stm = code(board.turn)
    for mv, v in unresolved_captures(board, see_min):
        out.append(Feature("unresolved_capture", stm, [chess.square_name(mv.from_square), chess.square_name(mv.to_square)], v))
    checks = sorted({mv.to_square for mv in board.legal_moves if board.gives_check(mv)})
    if checks:
        out.append(Feature("check_available", stm, names(checks)))
    return out
