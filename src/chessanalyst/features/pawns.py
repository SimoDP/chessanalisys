"""Pawn-structure features (§5.1)."""

from __future__ import annotations

import chess

from chessanalyst.features.model import Feature
from chessanalyst.features.values import code, names, rr

CENTRAL_FILES = range(2, 6)          # c..f for weak squares
QUEENSIDE, KINGSIDE = range(0, 4), range(4, 8)


def pawns(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    return list(board.pieces(chess.PAWN, side))


def _adjacent(f: int) -> list[int]:
    return [x for x in (f - 1, f + 1) if 0 <= x <= 7]


def _front(side: chess.Color, sq: chess.Square) -> chess.Square | None:
    r = chess.square_rank(sq) + (1 if side == chess.WHITE else -1)
    return chess.square(chess.square_file(sq), r) if 0 <= r <= 7 else None


def _pawn_attacks(board: chess.Board, side: chess.Color, sq: chess.Square) -> bool:
    return any(board.piece_type_at(a) == chess.PAWN and board.color_at(a) == side
               for a in board.attackers(side, sq))


def is_isolated(board, side, sq) -> bool:
    return not any(chess.square_file(p) in _adjacent(chess.square_file(sq)) for p in pawns(board, side))


def is_passed(board, side, sq) -> bool:
    f = chess.square_file(sq)
    for p in pawns(board, not side):
        if chess.square_file(p) in (f - 1, f, f + 1) and rr(side, p) > rr(side, sq):
            return False
    return True


def weak_squares(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    """Squares on files c–f, rr 3–5 for ``side``, no own pawn on them, that no own
    pawn on an adjacent file can ever attack (none with rr ≤ rr(q) − 1)."""
    own = pawns(board, side)
    out = []
    for f in CENTRAL_FILES:
        for sq in (chess.square(f, r) for r in range(8)):
            q = rr(side, sq)
            if not 3 <= q <= 5:
                continue
            if sq in own:
                continue
            if any(chess.square_file(p) in _adjacent(f) and rr(side, p) <= q - 1 for p in own):
                continue
            out.append(sq)
    return out


def outposts(board: chess.Board, side: chess.Color) -> list[chess.Square]:
    """Weak squares of the opponent with rr 4–6 for ``side``, defended by an own pawn."""
    return [sq for sq in weak_squares(board, not side)
            if 4 <= rr(side, sq) <= 6 and _pawn_attacks(board, side, sq)]


def pawn_features(board: chess.Board) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        own = pawns(board, side)
        files: dict[int, list[chess.Square]] = {}
        for p in own:
            files.setdefault(chess.square_file(p), []).append(p)
        for p in sorted(own):
            if is_isolated(board, side, p):
                out.append(Feature("isolated_pawn", s, names([p])))
        for f in sorted(files):
            if len(files[f]) >= 2:
                out.append(Feature("doubled_pawn", s, names(files[f])))
        for p in sorted(own):
            if is_isolated(board, side, p):
                continue
            adj = [q for q in own if chess.square_file(q) in _adjacent(chess.square_file(p))]
            front = _front(side, p)
            if adj and all(rr(side, q) > rr(side, p) for q in adj) and front is not None \
                    and _pawn_attacks(board, not side, front):
                out.append(Feature("backward_pawn", s, names([p])))
        for p in sorted(own):
            if is_passed(board, side, p):
                protected = _pawn_attacks(board, side, p)
                connected = any(chess.square_file(q) in _adjacent(chess.square_file(p)) and is_passed(board, side, q)
                                for q in own if q != p)
                out.append(Feature("passed_pawn", s, names([p]), {"protected": protected, "connected": connected}))
        if own:
            islands, prev = 0, -2
            for f in sorted(files):
                if f != prev + 1:
                    islands += 1
                prev = f
            out.append(Feature("pawn_island_count", s, [], islands))
        theirs = pawns(board, not side)
        for wing, rng in (("queenside", QUEENSIDE), ("kingside", KINGSIDE)):
            mine_n = sum(1 for p in own if chess.square_file(p) in rng)
            their_n = sum(1 for p in theirs if chess.square_file(p) in rng)
            if mine_n > their_n:
                out.append(Feature("pawn_majority", s, [], wing))
        weak = weak_squares(board, side)
        if weak:
            out.append(Feature("weak_square", s, names(weak)))
        posts = outposts(board, side)
        if posts:
            out.append(Feature("outpost", s, names(posts)))
            for sq in posts:
                pc = board.piece_at(sq)
                if pc and pc.piece_type == chess.KNIGHT and pc.color == side:
                    out.append(Feature("knight_outpost", s, names([sq])))
    return out
