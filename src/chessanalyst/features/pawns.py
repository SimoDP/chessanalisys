"""Pawn-structure features (§5.1)."""

from __future__ import annotations

import chess

from chessanalyst.config import FeatureGeometry
from chessanalyst.features.model import Feature
from chessanalyst.features.values import code, names, rr



def _files(letters: str) -> list[int]:
    return [chess.FILE_NAMES.index(c) for c in letters]


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


def weak_squares(board: chess.Board, side: chess.Color, geo: FeatureGeometry) -> list[chess.Square]:
    """Squares on files c–f, rr 3–5 for ``side`` (``geo``), no own pawn on them, that no own
    pawn on an adjacent file can ever attack (none with rr ≤ rr(q) − 1)."""
    own = pawns(board, side)
    lo, hi = geo.weak_square_ranks
    out = []
    for f in _files(geo.weak_square_files):
        for sq in chess.SquareSet(chess.BB_FILES[f]):
            q = rr(side, sq)
            if not lo <= q <= hi:
                continue
            if sq in own:
                continue
            if any(chess.square_file(p) in _adjacent(f) and rr(side, p) <= q - 1 for p in own):
                continue
            out.append(sq)
    return out


def outposts(board: chess.Board, side: chess.Color, geo: FeatureGeometry) -> list[chess.Square]:
    """Weak squares of the opponent with rr 4–6 for ``side`` (``geo``), defended by an own pawn."""
    lo, hi = geo.outpost_ranks
    return [sq for sq in weak_squares(board, not side, geo)
            if lo <= rr(side, sq) <= hi and _pawn_attacks(board, side, sq)]


def pawn_features(board: chess.Board, geo: FeatureGeometry) -> list[Feature]:
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
        for wing, rng in (("queenside", _files(geo.queenside_files)), ("kingside", _files(geo.kingside_files))):
            mine_n = sum(1 for p in own if chess.square_file(p) in rng)
            their_n = sum(1 for p in theirs if chess.square_file(p) in rng)
            if mine_n > their_n:
                out.append(Feature("pawn_majority", s, [], wing))
        weak = weak_squares(board, side, geo)
        if weak:
            out.append(Feature("weak_square", s, names(weak)))
        posts = outposts(board, side, geo)
        if posts:
            out.append(Feature("outpost", s, names(posts)))
            for sq in posts:
                pc = board.piece_at(sq)
                if pc and pc.piece_type == chess.KNIGHT and pc.color == side:
                    out.append(Feature("knight_outpost", s, names([sq])))
    return out


def _defends(side: chess.Color, p: chess.Square, q: chess.Square) -> bool:
    """Pawn ``p`` of ``side`` defends square ``q`` (diagonally in front)."""
    dr = 1 if side == chess.WHITE else -1
    return chess.square_rank(q) - chess.square_rank(p) == dr and abs(chess.square_file(q) - chess.square_file(p)) == 1


def pawn_chains(board: chess.Board, side: chess.Color, min_len: int) -> list[list[chess.Square]]:
    """Maximal diagonal chains of ``side``'s pawns, each defended by the previous one."""
    own = sorted(pawns(board, side))
    nxt = {p: [q for q in own if _defends(side, p, q)] for p in own}
    bases = [p for p in own if not any(_defends(side, q, p) for q in own)]
    chains: list[list[chess.Square]] = []

    def walk(path: list[chess.Square]) -> None:
        if not nxt[path[-1]]:
            if len(path) >= min_len:
                chains.append(path)
            return
        for q in nxt[path[-1]]:
            walk(path + [q])

    for b in bases:
        walk([b])
    seen, out = set(), []
    for c in chains:
        key = frozenset(c)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def pawn_m3_features(board: chess.Board, geo: FeatureGeometry) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        for c in pawn_chains(board, side, geo.pawn_chain_min):
            out.append(Feature("pawn_chain", s, names(c)))
        files = _files(geo.minority_pawn_files)
        mine = sum(1 for p in pawns(board, side) if chess.square_file(p) in files)
        theirs = sum(1 for p in pawns(board, not side) if chess.square_file(p) in files)
        heavy = [sq for t in (chess.ROOK, chess.QUEEN) for sq in board.pieces(t, side)
                 if chess.square_file(sq) in _files(geo.minority_piece_files)]
        if mine == geo.minority_own_pawns and theirs == geo.minority_opp_pawns and heavy:
            out.append(Feature("minority_attack", s, names(heavy)))
    return out
