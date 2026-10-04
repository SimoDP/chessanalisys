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


# -- M2: recorded nodes of fixtures/golden_nodes.json (Stockfish 16, raw 1900) -----------------

import json  # noqa: E402
from pathlib import Path  # noqa: E402

from chessanalyst.engines.types import NodeResult as _NR  # noqa: E402

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures"
# One E2 node and the three ℓ2 nodes that reproduce the rows of the raw 1900 (§3-ter.6)
T3_LABELS = ("6.Be3", "6.Be3 e5 7.Nb3", "6.Be2 e5 7.Nb3", "6.f4 e5 7.Nb3")


def golden_t3_nodes() -> list[ContextNode]:
    nodes = {n["label"]: n for n in json.loads((GOLDEN / "golden_nodes.json").read_text(encoding="utf-8"))["nodes"]}
    maia = json.loads((GOLDEN / "golden_maia.json").read_text(encoding="utf-8"))["anchors"]["1900"]["nodes"]
    policy = {n["label"]: {x["uci"]: x["p"] for x in n["policy"]} for n in maia}
    out = []
    for label in T3_LABELS:
        n = nodes[label]
        out.append(ContextNode(label, chess.Board(n["fen"]), _NR.from_dict(n["result"]), policy[label]))
    return out


def test_recorded_nodes_choose_nc6():
    ns = golden_t3_nodes()
    assert all(n.board.turn == chess.BLACK for n in ns)
    ctx = choose_context(ns, context_candidates(ns, 3), 30)
    assert ctx is not None and ctx["uci"] == "b8c6"
    costs = {r["node"].key: r["cost_cp"] for r in ctx["rows"]}
    # ...Nc6 costs about half a pawn after 6.Be3 e5 7.Nb3, almost nothing against 6.f4 (§8-bis.2)
    assert costs["6.Be3 e5 7.Nb3"] >= 50 and costs["6.f4 e5 7.Nb3"] <= 5 and costs["6.Be3"] <= 10
    assert 45 <= ctx["spread_cp"] <= 55                    # «spread ≈ 50»


def test_recorded_nodes_threshold():
    ns = golden_t3_nodes()
    spread = choose_context(ns, context_candidates(ns, 3), 30)["spread_cp"]
    assert choose_context(ns, context_candidates(ns, 3), spread + 1) is None


def test_recorded_nodes_with_the_d68_filter(cfg):
    # D-68: only moves the opponent really plays (mean p_opp ≥ context_min_p) are context candidates
    ns = golden_t3_nodes()
    sel = cfg.thresholds.selection
    cands = context_candidates(ns, sel.context_candidates, sel.context_min_p)
    ctx = choose_context(ns, cands, sel.context_spread_cp, cfg.thresholds.profile.tactical.gap_cp)
    assert ctx["uci"] == "b8c6" and 45 <= ctx["spread_cp"] <= 55


def test_d68_rows_where_the_move_is_a_blunder_are_left_out(cfg):
    ns = nodes()
    ns.append(node("Bc4", {"e5": -20, "Nc6": -300, "e6": -25}, {"e5": 0.4, "Nc6": 0.2}))   # Nc6 drops a piece
    gap = cfg.thresholds.profile.tactical.gap_cp
    assert choose_context(ns, ["b8c6"], 30)["spread_cp"] == 280 - 8                  # v0.9.1 rule
    ctx = choose_context(ns, ["b8c6"], 30, gap)
    assert sorted(r["cost_cp"] for r in ctx["rows"]) == [8, 10, 53] and ctx["spread_cp"] == 45


def test_d68_filter_drops_moves_nobody_plays():
    ns = nodes()
    # ...Nc6 has mean p_opp 0.15: kept at 3%, dropped at 20%
    assert "b8c6" in context_candidates(ns, 3, 0.03)
    assert "b8c6" not in context_candidates(ns, 3, 0.20)
    assert context_candidates(ns, 3, 0.20) == ["e7e5"]
