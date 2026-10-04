"""King and castling features (§5.1, §5.2)."""

from __future__ import annotations

import chess

from chessanalyst.features.model import Feature
from chessanalyst.features.values import code, names, rr

SHORT_FILES = (6, 7)     # g, h
LONG_FILES = (1, 2)      # b, c


def castling_state(board: chess.Board, side: chess.Color) -> str:
    short = board.has_kingside_castling_rights(side)
    long_ = board.has_queenside_castling_rights(side)
    if short and long_:
        return "can_both"
    if short:
        return "can_short"
    if long_:
        return "can_long"
    k = board.king(side)
    if k is not None and rr(side, k) == 1:
        if chess.square_file(k) in SHORT_FILES:
            return "castled_short"
        if chess.square_file(k) in LONG_FILES:
            return "castled_long"
    return "lost"


def _king_files(k: chess.Square) -> list[int]:
    f = chess.square_file(k)
    return [x for x in (f - 1, f, f + 1) if 0 <= x <= 7]


def king_features(board: chess.Board) -> list[Feature]:
    out: list[Feature] = []
    for side in (chess.WHITE, chess.BLACK):
        s = code(side)
        k = board.king(side)
        if k is None:
            continue
        state = castling_state(board, side)
        ksq = names([k])
        if state in ("castled_short", "castled_long"):
            out.append(Feature("king_castled", s, ksq, state))
        if state in ("can_both", "can_short"):
            out.append(Feature("can_castle_short", s, ksq))
        if state in ("can_both", "can_long"):
            out.append(Feature("can_castle_long", s, ksq))
        if state == "lost":
            out.append(Feature("castling_lost", s, ksq))
        own_pawns = list(board.pieces(chess.PAWN, side))
        files = _king_files(k)
        if state in ("castled_short", "castled_long"):
            shield, uncovered = [], []
            for f in files:
                ps = [p for p in own_pawns if chess.square_file(p) == f and rr(side, p) in (2, 3)]
                if ps:
                    shield.extend(ps)
                else:
                    uncovered.append(chess.square(f, 1 if side == chess.WHITE else 6))
            if not uncovered:
                out.append(Feature("pawn_shield_intact", s, names(shield)))
            else:
                out.append(Feature("pawn_shield_weakened", s, names(uncovered)))
        open_files = [f for f in files if not any(chess.square_file(p) == f for p in own_pawns)]
        if open_files:
            out.append(Feature("open_file_to_king", s, ksq, "".join(chess.FILE_NAMES[f] for f in open_files)))
    return out
