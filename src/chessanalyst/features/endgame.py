"""Endgame facts (usefulness test, phase 4, D-77): the kind of endgame, the key squares of a passed pawn and the
opposition. Pure functions on a python-chess board; the theory they encode is the textbook one (king and pawn
against king), the rest comes from the engines through the pack."""

from __future__ import annotations

import chess

KINDS = ("pawn", "rook")


def endgame_kind(board: chess.Board) -> str | None:
    """``pawn``: only kings and pawns; ``rook``: kings, pawns and rooks for both sides; otherwise None."""
    others = {t for t in (chess.KNIGHT, chess.BISHOP, chess.QUEEN) for c in chess.COLORS if board.pieces(t, c)}
    if others:
        return None
    rooks = [bool(board.pieces(chess.ROOK, c)) for c in chess.COLORS]
    if not any(rooks):
        return "pawn"
    return "rook" if all(rooks) else None


def is_passed(board: chess.Board, sq: int) -> bool:
    color = board.color_at(sq)
    f, r = chess.square_file(sq), chess.square_rank(sq)
    ahead = range(r + 1, 8) if color == chess.WHITE else range(0, r)
    return not any(board.piece_at(chess.square(ff, rr)) == chess.Piece(chess.PAWN, not color)
                   for ff in (f - 1, f, f + 1) if 0 <= ff < 8 for rr in ahead)


def key_squares(sq: int, color: chess.Color) -> list[int]:
    """The squares that, reached by the king of the pawn's side, win the pawn ending whoever is to move:
    a pawn up to its 4th rank, the three squares two ranks ahead; on the 5th and 6th, also the three one rank
    ahead; a rook's pawn, the two squares of the next file on the last two ranks."""
    f = chess.square_file(sq)
    rel = chess.square_rank(sq) if color == chess.WHITE else 7 - chess.square_rank(sq)
    to_abs = (lambda r: r) if color == chess.WHITE else (lambda r: 7 - r)
    if f in (0, 7):
        g = 1 if f == 0 else 6
        return [chess.square(g, to_abs(r)) for r in (6, 7)]
    ranks = [rel + 2] if rel <= 3 else [rel + 1, rel + 2]
    return [chess.square(ff, to_abs(r)) for r in ranks if r <= 7 for ff in (f - 1, f, f + 1)]


def has_opposition(board: chess.Board, color: chess.Color) -> bool:
    """Direct opposition: the kings on the same file or rank with one square between, the other side to move."""
    a, b = board.king(color), board.king(not color)
    if a is None or b is None or board.turn == color:
        return False
    df, dr = abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b))
    return (df, dr) in ((0, 2), (2, 0))
