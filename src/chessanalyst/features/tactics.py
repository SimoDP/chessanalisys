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


SLIDERS = (chess.BISHOP, chess.ROOK, chess.QUEEN)


def _worth(board: chess.Board, sq: chess.Square) -> float:
    """Piece value with the king above everything (attacking it is a check)."""
    pt = board.piece_type_at(sq)
    return float("inf") if pt == chess.KING else piece_value(pt)


def _as_side(board: chess.Board, side: chess.Color) -> chess.Board | None:
    """``board`` with ``side`` to move (a null move when needed); None if that is not a legal position."""
    if board.turn == side:
        return board
    if board.is_check():
        return None
    b = board.copy(stack=False)
    b.push(chess.Move.null())
    return b


def _behind(board: chess.Board, a: chess.Square, front: chess.Square) -> chess.Square | None:
    """First occupied square after ``front`` on the line from ``a`` through ``front``."""
    df = (chess.square_file(front) > chess.square_file(a)) - (chess.square_file(front) < chess.square_file(a))
    dr = (chess.square_rank(front) > chess.square_rank(a)) - (chess.square_rank(front) < chess.square_rank(a))
    f, r = chess.square_file(front) + df, chess.square_rank(front) + dr
    while 0 <= f <= 7 and 0 <= r <= 7:
        sq = chess.square(f, r)
        if board.piece_at(sq) is not None:
            return sq
        f, r = f + df, r + dr
    return None


def skewers(board: chess.Board, side: chess.Color) -> list[list[chess.Square]]:
    """M3 ``skewer`` against ``side``: a slider of O attacks a piece of S (no pawn) worth more than the piece
    of S (no pawn, no king) right behind it on the same line, and that piece is undefended."""
    out = []
    for t in SLIDERS:
        for a in board.pieces(t, not side):
            for front in board.attacks(a):
                fp = board.piece_at(front)
                if fp is None or fp.color != side or fp.piece_type == chess.PAWN:
                    continue
                sq = _behind(board, a, front)
                p = board.piece_at(sq) if sq is not None else None
                if (p is not None and p.color == side and p.piece_type not in (chess.PAWN, chess.KING)
                        and _worth(board, front) > _worth(board, sq) and not board.attackers(side, sq)):
                    out.append([a, front, sq])
    return out


def forks(board: chess.Board, side: chess.Color) -> list[list[chess.Square]]:
    """M3 ``fork`` against ``side``: a piece of O attacks >= 2 pieces of S, each worth more than the attacker
    or undefended, and S cannot take the attacker with SEE >= 0."""
    out = []
    b_s = _as_side(board, side)
    for a, ap in board.piece_map().items():
        if ap.color == side:
            continue
        av = _worth(board, a)
        targets = [sq for sq in board.attacks(a)
                   if board.color_at(sq) == side and (_worth(board, sq) > av or not board.attackers(side, sq))]
        if len(targets) < 2:
            continue
        if b_s is not None and any(see_move(b_s, mv) >= 0 for mv in b_s.legal_moves if mv.to_square == a):
            continue
        out.append([a] + sorted(targets, key=chess.square_name))
    return out


def overloaded(board: chess.Board, side: chess.Color) -> list[list[chess.Square]]:
    """M3 ``overloaded_piece``: a piece of S that is the only defender of >= 2 attacked pieces of S."""
    only: dict[chess.Square, list[chess.Square]] = {}
    for sq, p in board.piece_map().items():
        if p.color != side or p.piece_type == chess.KING or not board.attackers(not side, sq):
            continue
        d = list(board.attackers(side, sq))
        if len(d) == 1:
            only.setdefault(d[0], []).append(sq)
    return [[d] + sorted(v, key=chess.square_name) for d, v in sorted(only.items()) if len(v) >= 2]


def tempo_counts(board: chess.Board, pv: list[str], plies: int, see_min: int) -> dict[chess.Color, int]:
    """M3 ``tempo_count``: forcing moves (checks, captures, threats of a capture with SEE >= ``see_min``)
    per side in the first ``plies`` half-moves of ``pv`` (SAN from ``board``)."""
    counts = {chess.WHITE: 0, chess.BLACK: 0}
    b = board.copy(stack=False)
    for san in pv[:plies]:
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        mover = b.turn
        forcing = b.is_capture(mv) or b.gives_check(mv)
        b.push(mv)
        if not forcing and not b.is_check():
            again = _as_side(b, mover)
            if again is not None and any(again.is_capture(m) and see_move(again, m) >= see_min
                                         for m in again.legal_moves):
                forcing = True
        counts[mover] += int(forcing)
    return counts


def tactic_m3_features(board: chess.Board, best_pv: list[str], geo) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        for a, f1, f2 in skewers(board, side):
            out.append(Feature("skewer", s, [chess.square_name(a), chess.square_name(f1), chess.square_name(f2)]))
        for w in forks(board, side):
            out.append(Feature("fork", s, [chess.square_name(x) for x in w]))
        for w in overloaded(board, side):
            out.append(Feature("overloaded_piece", s, [chess.square_name(x) for x in w]))
    if best_pv:
        tc = tempo_counts(board, best_pv, geo.tempo_plies, geo.tempo_threat_see_min)
        for side in (chess.WHITE, chess.BLACK):
            if tc[side]:
                out.append(Feature("tempo_count", code(side), [], tc[side]))
    return out
