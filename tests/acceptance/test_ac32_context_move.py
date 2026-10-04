"""AC-32 (synthetic): opponent context move (§3-ter.6)."""

from __future__ import annotations

import chess

from chessanalyst.engines.types import EngineLine, NodeResult
from chessanalyst.explore.context import ContextNode, choose_context, context_candidates, missing_nodes

ROOT = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def node(first: str, evals_black: dict[str, int], policy: dict[str, float]) -> ContextNode:
    b = chess.Board(ROOT)
    b.push_san(first)
    lines = []
    for i, (san, ev) in enumerate(sorted(evals_black.items(), key=lambda kv: -kv[1]), 1):
        mv = b.parse_san(san)
        lines.append(EngineLine(i, san, mv.uci(), -ev, None, None, [san], [mv.uci()]))
    res = NodeResult(b.fen(), len(lines), 18, 20, 1, 1.0, False, "x", None, lines)
    pol = {b.parse_san(s).uci(): p for s, p in policy.items()}
    return ContextNode(first, b, res, pol)


def nodes():
    # Black's point of view (higher = better for Black). Nc6 costs 8, 53, 10 cp.
    return [
        node("Be3", {"Ng4": -33, "e5": -35, "Nc6": -41, "e6": -50}, {"e5": 0.5, "Nc6": 0.1}),
        node("Be2", {"e5": -24, "Nc6": -77, "e6": -30}, {"e5": 0.6, "Nc6": 0.15}),
        node("f4", {"e5": -6, "Nc6": -16, "e6": -20}, {"e5": 0.5, "Nc6": 0.2}),
    ]


def test_candidates_exclude_move_best_everywhere():
    ns = nodes()
    cands = context_candidates(ns, 3)
    assert "f8e7" not in cands
    # all three appear in 3 nodes; order by mean p_opp: e5 (0.53), Nc6 (0.15), e6 (0)
    assert cands == ["e7e5", "b8c6", "e7e6"]   # e5 is best in two nodes but not in Be3 → kept


def test_choice_and_spread():
    ns = nodes()
    ctx = choose_context(ns, context_candidates(ns, 3), 30)
    assert ctx["uci"] == "b8c6"
    assert sorted(r["cost_cp"] for r in ctx["rows"]) == [8, 10, 53]
    assert ctx["spread_cp"] == 45


def test_threshold_respected():
    ns = nodes()
    assert choose_context(ns, context_candidates(ns, 3), 46) is None


def test_missing_nodes_for_e2c():
    ns = nodes()
    ns[1] = node("Be2", {"e5": -24, "e6": -30}, {"e5": 0.6})
    assert [n.key for n in missing_nodes(ns, "b8c6")] == ["Be2"]
    ns[1].extra = {"b8c6": 77}       # E2c result, White's point of view
    ctx = choose_context(ns, ["b8c6"], 30)
    assert ctx is not None and sorted(r["cost_cp"] for r in ctx["rows"]) == [8, 10, 53]
