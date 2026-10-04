"""Static exchange evaluation with legal moves only (§5.1)."""

from __future__ import annotations

import chess

from chessanalyst.features.values import piece_value


def _least_valuable_capture(board: chess.Board, square: chess.Square) -> chess.Move | None:
    best: tuple[int, chess.Move] | None = None
    for mv in board.legal_moves:
        if mv.to_square != square or not board.is_capture(mv):
            continue
        v = piece_value(board.piece_type_at(mv.from_square))
        if mv.promotion:
            v = piece_value(chess.PAWN)
        if best is None or v < best[0]:
            best = (v, mv)
    return best[1] if best else None


def _see_square(board: chess.Board, square: chess.Square) -> int:
    """Best gain for the side to move from capturing on ``square`` (0 = stand pat)."""
    mv = _least_valuable_capture(board, square)
    if mv is None:
        return 0
    captured = piece_value(board.piece_type_at(square))
    board.push(mv)
    try:
        return max(0, captured - _see_square(board, square))
    finally:
        board.pop()


def see_move(board: chess.Board, move: chess.Move) -> int:
    """Material balance of ``move`` (a capture) followed by the best legal recaptures."""
    if board.is_en_passant(move):
        captured = piece_value(chess.PAWN)
    else:
        captured = piece_value(board.piece_type_at(move.to_square))
    b = board.copy(stack=False)
    b.push(move)
    return captured - _see_square(b, move.to_square)
