"""Opponent context move for T3 (§3-ter.6, D-44)."""

from __future__ import annotations

from dataclasses import dataclass

import chess

from chessanalyst.engines.types import NodeResult


@dataclass
class ContextNode:
    key: str                          # identifies the T3 node (its path label)
    board: chess.Board                # opponent to move
    result: NodeResult                # MultiPV of the node
    policy: dict[str, float]          # Maia-2 at the opponent's Elo (uci → p)
    extra: dict[str, int] | None = None   # E2c: uci → eval_white_cp from restricted searches


def _opp_cp(eval_white_cp: int, board: chess.Board) -> int:
    return eval_white_cp if board.turn == chess.WHITE else -eval_white_cp


def context_candidates(nodes: list[ContextNode], n_keep: int, min_p: float = 0.0) -> list[str]:
    """Moves present in the MultiPV of ≥ 2 nodes, minus a move that is best in all
    the nodes where it appears, with mean p_opp ≥ ``min_p`` (D-68: only moves the
    opponent really plays); ordered by (#nodes, mean p_opp) desc."""
    seen: dict[str, list[ContextNode]] = {}
    for n in nodes:
        for ln in n.result.lines:
            seen.setdefault(ln.uci, []).append(n)
    cands = []
    for u, ns in seen.items():
        if len(ns) < 2:
            continue
        if all(n.result.lines and n.result.lines[0].uci == u for n in ns):
            continue
        cands.append(u)

    def mean_p(u: str) -> float:
        legal = [n for n in nodes if chess.Move.from_uci(u) in n.board.legal_moves]
        return sum(n.policy.get(u, 0.0) for n in legal) / len(legal) if legal else 0.0

    cands = [u for u in cands if mean_p(u) >= min_p]
    cands.sort(key=lambda u: (-len(seen[u]), -mean_p(u), u))
    return cands[:n_keep]


def missing_nodes(nodes: list[ContextNode], move: str) -> list[ContextNode]:
    """Nodes where ``move`` is legal but absent from the MultiPV (→ E2c)."""
    m = chess.Move.from_uci(move)
    return [n for n in nodes if m in n.board.legal_moves and all(ln.uci != move for ln in n.result.lines)]


def eval_of(n: ContextNode, move: str) -> int | None:
    for ln in n.result.lines:
        if ln.uci == move:
            return ln.eval_white_cp
    if n.extra and move in n.extra:
        return n.extra[move]
    return None


def choose_context(nodes: list[ContextNode], cands: list[str], spread_min: int,
                   blunder_cp: int | None = None) -> dict | None:
    """Context move: largest cost spread across the T3 nodes (§3-ter.6). D-68: a node where the move
    costs at least ``blunder_cp`` is left out (there it is a tactical error, not a context cost)."""
    best = None
    for u in cands:
        rows = []
        for n in nodes:
            ev = eval_of(n, u)
            if ev is None or not n.result.lines:
                continue
            best_ev = n.result.lines[0].eval_white_cp
            cost = max(0, _opp_cp(best_ev, n.board) - _opp_cp(ev, n.board))
            if blunder_cp is not None and cost >= blunder_cp:
                continue
            rows.append({"node": n, "move_eval_white": ev, "best": n.result.lines[0], "cost_cp": cost,
                         "p_opp": n.policy.get(u, 0.0)})
        if len(rows) < 2:
            continue
        costs = [r["cost_cp"] for r in rows]
        spread = max(costs) - min(costs)
        legal = [n for n in nodes if chess.Move.from_uci(u) in n.board.legal_moves]
        mean_p = sum(n.policy.get(u, 0.0) for n in legal) / len(legal) if legal else 0.0
        key = (spread, mean_p, [-ord(c) for c in u])
        if spread >= spread_min and (best is None or key > best[0]):
            best = (key, {"uci": u, "rows": rows, "spread_cp": spread})
    return None if best is None else best[1]
