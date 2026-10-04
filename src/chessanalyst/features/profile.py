"""Position profile and matrix column (§5.2, D-32, D-59)."""

from __future__ import annotations

from typing import Any

import chess

from chessanalyst.config import Config
from chessanalyst.engines.types import EngineLine
from chessanalyst.features.activity import activity_features, activity_m3_features
from chessanalyst.features.king import castling_state, king_features, king_zone_features
from chessanalyst.features.material import material_features
from chessanalyst.features.model import Feature
from chessanalyst.features.pawns import pawn_features, pawn_m3_features
from chessanalyst.features.tactics import tactic_features, tactic_m3_features
from chessanalyst.features.values import MINORS, code, material, nonpawn_material


def castling_profile(board: chess.Board) -> dict[str, str]:
    return {code(s): castling_state(board, s) for s in (chess.WHITE, chess.BLACK)}


def extract_features(board: chess.Board, cfg: Config, e0_lines: list[EngineLine]) -> list[Feature]:
    """§5.1 on the root: the M1 keys, then (from M3) the M3 keys."""
    mate = e0_lines[0].mate_white if e0_lines else None
    return static_features(board, cfg, mate) + m3_features(board, cfg, e0_lines[0].pv if e0_lines else [])


def static_features(board: chess.Board, cfg: Config, mate_white: int | None = None) -> list[Feature]:
    """The M1 keys (no engine data besides the mate of the first E0 line)."""
    see_min = cfg.thresholds.profile.unresolved_capture_see_min
    return (material_features(board) + pawn_features(board, cfg.thresholds.features) + king_features(board)
            + activity_features(board, castling_profile(board)) + tactic_features(board, see_min, mate_white))


def m3_features(board: chess.Board, cfg: Config, best_pv: list[str]) -> list[Feature]:
    """The M3 keys of §5.1 (``tempo_count`` needs the best PV)."""
    geo = cfg.thresholds.features
    return (king_zone_features(board) + activity_m3_features(board, geo) + pawn_m3_features(board, geo)
            + tactic_m3_features(board, best_pv, geo))


def mover_cp(line: EngineLine, turn: chess.Color) -> int:
    return line.eval_white_cp if turn == chess.WHITE else -line.eval_white_cp


def mate_plies(mate_white: int, turn: chess.Color) -> int:
    mover_mates = (mate_white > 0) == (turn == chess.WHITE)
    return 2 * abs(mate_white) - 1 if mover_mates else 2 * abs(mate_white)


def phase_of(board: chess.Board, cfg: Config, in_book: bool) -> str:
    p = cfg.thresholds.profile
    total_np = nonpawn_material(board, chess.WHITE) + nonpawn_material(board, chess.BLACK)
    no_queens = not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK)
    few_minors = all(sum(len(board.pieces(t, s)) for t in MINORS) <= p.endgame_no_queens_max_minors_per_side
                     for s in (chess.WHITE, chess.BLACK))
    if total_np <= p.endgame_nonpawn_total_max or (no_queens and few_minors):
        return "endgame"
    if in_book and board.fullmove_number <= p.opening_fullmove_max:
        return "opening"
    return "middlegame"


def blocked_pairs(board: chess.Board) -> int:
    n = 0
    for sq in board.pieces(chess.PAWN, chess.WHITE):
        r = chess.square_rank(sq)
        if r < 7:
            front = chess.square(chess.square_file(sq), r + 1)
            p = board.piece_at(front)
            if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                n += 1
    return n


def matrix_column(profile: dict[str, Any]) -> int:
    if profile["tablebase"]:
        return 4   # endgame with tablebase
    if profile["phase"] == "endgame":
        return 3   # endgame
    if profile["tactical"]:
        return 2   # tactical middlegame
    return 1       # opening or non-tactical middlegame


def compute_profile(board: chess.Board, cfg: Config, e0_lines: list[EngineLine], K: int,
                    features: list[Feature], in_book: bool, quiet: bool, spread_cp: int,
                    tablebase: bool = False) -> dict[str, Any]:
    th = cfg.thresholds.profile
    reasons: list[str] = []
    if len(e0_lines) >= 2 and mover_cp(e0_lines[0], board.turn) - mover_cp(e0_lines[1], board.turn) >= th.tactical.gap_cp:
        reasons.append("gap")
    if any(ln.mate_white is not None and mate_plies(ln.mate_white, board.turn) <= th.tactical.mate_plies
           for ln in e0_lines[:K]):
        reasons.append("mate")
    if board.is_check():
        reasons.append("in_check")
    keys = {f.key for f in features}
    if "hanging_piece" in keys:
        reasons.append("hanging_piece")
    if "unresolved_capture" in keys:
        reasons.append("unresolved_capture")
    w, b = material(board, chess.WHITE), material(board, chess.BLACK)
    profile: dict[str, Any] = {
        "phase": phase_of(board, cfg, in_book),
        "castling": castling_profile(board),
        "tactical": bool(reasons),
        "tactical_reasons": reasons,
        "quiet": quiet,
        "spread_cp": spread_cp,
        "closed": blocked_pairs(board) >= th.closed_min_blocked_pairs,
        "tablebase": tablebase,
        "in_book": in_book,
        "material": {"w": w, "b": b, "balance": w - b},
    }
    profile["matrix_column"] = matrix_column(profile)
    return profile
