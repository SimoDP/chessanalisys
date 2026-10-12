"""Strategic facts the books name often and the plan lacked (data plan, step 4 bis): the sacrifice of a move,
the bad bishop, the weak squares of the opponent that a piece can use. Thresholds in ``thresholds.yaml:
keypoints.strategic``."""

from __future__ import annotations

import chess

from chessanalyst.features.pawns import weak_squares
from chessanalyst.features.see import _see_square
from chessanalyst.features.values import MINORS, piece_value, rr

USERS = MINORS


def sacrifice(board: chess.Board, move: chess.Move) -> int:
    """Material (pawns) that ``move`` gives if the opponent takes what it can on the destination square with the
    best recaptures; 0 when it gives nothing."""
    if board.is_en_passant(move):
        captured = piece_value(chess.PAWN)
    else:
        captured = piece_value(board.piece_type_at(move.to_square))
    after = board.copy(stack=False)
    after.push(move)
    return max(0, _see_square(after, move.to_square) - captured)


def bad_bishops(board: chess.Board, side: chess.Color, st) -> list[chess.Square]:
    """Bishops of ``side`` hemmed in by their own pawns: at least ``st.bad_bishop_pawns`` own pawns on the files
    ``st.bad_bishop_files`` and on the bishop's colour, at least ``st.bad_bishop_blocked`` of them blocked."""
    files = [chess.FILE_NAMES.index(f) for f in st.bad_bishop_files]
    out = []
    for b in sorted(board.pieces(chess.BISHOP, side)):
        colour = chess.BB_LIGHT_SQUARES if chess.BB_SQUARES[b] & chess.BB_LIGHT_SQUARES else chess.BB_DARK_SQUARES
        own = [p for p in board.pieces(chess.PAWN, side)
               if chess.BB_SQUARES[p] & colour and chess.square_file(p) in files]
        step = 8 if side == chess.WHITE else -8
        blocked = [p for p in own if 0 <= p + step < 64 and board.piece_at(p + step) is not None]
        if len(own) >= st.bad_bishop_pawns and len(blocked) >= st.bad_bishop_blocked:
            out.append(b)
    return out


def usable_weak_squares(board: chess.Board, side: chess.Color, geo, st) -> list[chess.Square]:
    """Weak squares of ``side`` (no pawn of its own can ever defend them) on the files ``st.weak_files``, in its
    half of the board (relative ranks up to ``st.weak_max_rank``), that a knight or bishop of the opponent
    occupies or attacks (the pieces that live on a hole)."""
    files = [chess.FILE_NAMES.index(f) for f in st.weak_files]
    out = []
    for sq in weak_squares(board, side, geo):
        if chess.square_file(sq) not in files or rr(side, sq) > st.weak_max_rank:
            continue
        here = board.piece_at(sq)
        if (here is not None and here.color != side and here.piece_type in USERS) or any(
                board.piece_type_at(a) in USERS for a in board.attackers(not side, sq)):
            out.append(sq)
    return out
