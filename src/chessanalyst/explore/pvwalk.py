"""E2b: nodes along a candidate's PV and ``complexity`` (§3-ter.2, §4.3, D-29, D-58)."""

from __future__ import annotations

import chess

from chessanalyst.engines.types import NodeResult


def e2b_plies(pv_len: int, plies_max: int) -> list[int]:
    """Positions after 2, 4, … half-moves, up to ``plies_max − 1`` and the PV length."""
    limit = min(plies_max - 1, pv_len)
    return list(range(2, limit + 1, 2))


def mover_cp(eval_white_cp: int, turn: chess.Color) -> int:
    return eval_white_cp if turn == chess.WHITE else -eval_white_cp


def is_forced(result: NodeResult, board: chess.Board, forced_gap_cp: int) -> bool:
    if board.legal_moves.count() == 1:
        return True
    if len(result.lines) < 2:
        return False
    a = mover_cp(result.lines[0].eval_white_cp, board.turn)
    b = mover_cp(result.lines[1].eval_white_cp, board.turn)
    return a - b >= forced_gap_cp


def complexity(nodes: list[tuple[chess.Board, NodeResult | None]], forced_gap_cp: int) -> tuple[int, bool]:
    """(count of forced nodes among the available ones, partial)."""
    partial = any(r is None for _, r in nodes)
    n = sum(1 for b, r in nodes if r is not None and is_forced(r, b, forced_gap_cp))
    return n, partial
