"""Category Scoring Engine (§5-bis, M3): unit tests of the formulas on hand-made nodes."""

from __future__ import annotations

import math

import chess
import pytest

from chessanalyst.features.model import Feature
from chessanalyst.scoring.categories import advice, quiescent_leaf, score_categories, static_t
from chessanalyst.scoring.filter import (ScoredLine, attacker_probability, build_lines, filter_lines,
                                         path_probability, side_value)

START = chess.Board()


def node(nid, fen, phase, multipv, parent=None, via=None, maia=None, path=(), unstable=False):
    b = chess.Board(fen)
    return {"id": nid, "fen": fen, "phase": phase, "parent": parent, "via_uci": via[0] if via else None,
            "via_san": via[1] if via else None, "side_to_move": "w" if b.turn else "b", "citable": True,
            "multipv": multipv, "maia": maia, "path": list(path), "unstable_depth": unstable}


def mpv(uci, san, cp, pv, mate=None, rank=1):
    return {"rank": rank, "uci": uci, "san": san, "eval_user_cp": cp, "mate_user": mate, "pv": pv}


def pol(**p):
    return {"policy": [{"uci": u, "san": u, "p": v} for u, v in p.items()]}


def test_side_value_and_mates():
    e = {"eval_user_cp": 40, "mate_user": None}
    assert side_value(e, "w", "w", 1000) == 40 and side_value(e, "b", "w", 1000) == -40
    m = {"eval_user_cp": 0, "mate_user": -3}            # mate against the user
    assert side_value(m, "w", "w", 1000) == -1000 and side_value(m, "b", "w", 1000) == 1000


def test_path_probability():
    root = node("N1", START.fen(), "E0", [], maia=pol(e2e4=0.5))
    b = START.copy()
    b.push_uci("e2e4")
    n2 = node("N2", b.fen(), "E2", [], parent="N1", via=("e2e4", "e4"), maia=pol(e7e5=0.4))
    b.push_uci("e7e5")
    n3 = node("N3", b.fen(), "E3l1", [], parent="N2", via=("e7e5", "e5"))
    by = {n["id"]: n for n in (root, n2, n3)}
    assert path_probability(n3, by) == pytest.approx(0.5 * 0.4)
    assert path_probability(root, by) == 1.0


def test_attacker_probability_counts_only_the_attacker():
    calls = []

    def policy(fen, es, eo):
        calls.append((chess.Board(fen).turn, es, eo))
        return {"e2e4": 0.5, "g1f3": 0.25, "e7e5": 0.9}

    p, moves = attacker_probability(START, ["e4", "e5", "Nf3", "Nc6"], chess.WHITE, 4, {"w": 1500, "b": 1700}, policy)
    assert p == pytest.approx(0.5) and [m["san"] for m in moves] == ["e4"]      # Nf3 is a quiet follow-up
    b = chess.Board("4k3/8/8/3p4/8/8/4P3/4K1N1 w - - 0 1")
    p, moves = attacker_probability(b, ["e4", "Kd7", "exd5"], chess.WHITE, 4, {"w": 1500, "b": 1500},
                                    lambda fen, s, o: {"e2e4": 0.5, "e4d5": 0.8})
    assert p == pytest.approx(0.4) and [m["san"] for m in moves] == ["e4", "exd5"]   # the capture counts
    assert all(turn == chess.WHITE and es == 1500 and eo == 1700 for turn, es, eo in calls)


def _line(kind="refutation", impact=300, p_att=0.5, p_walk=0.4, mate=None, attacker="b", start="N3", user="w"):
    st = {"id": start, "fen": START.fen(), "path": ["e4"], "unstable_depth": False}
    return ScoredLine(kind=kind, start=st, rank=1, attacker=attacker, entry=None, plies=["e4"], eval_end_user_cp=0,
                      mate_user=mate, impact_cp=impact, p_att=p_att, p_walk=p_walk, attacker_moves=[], user=user)


def test_risk_and_filter(cfg):
    sc = cfg.thresholds.scoring
    a = _line(impact=300, p_att=0.5, p_walk=0.4)          # risk = 0.5 × 0.4 × 3 = 0.6
    assert a.risk == pytest.approx(0.6)
    b = _line(impact=60, p_att=0.5, p_walk=0.1, start="N2")  # 0.03: below θ, not decisive -> out
    c = _line(impact=250, p_att=0.01, p_walk=0.1, start="N4")  # decisive, P_att low -> in, invisible
    d = _line(kind="threat", impact=100, p_att=0.9, p_walk=0.9, start="N9")   # 0.81 -> in, first (threat)
    m = _line(impact=1000, p_att=0.2, p_walk=0.001, mate=-2, start="N5")      # mate for the attacker (Black)
    kept = filter_lines([a, b, c, d, m], "1600_2000", sc)
    assert [(x.id, x.start["id"], x.reason, x.visible) for x in kept] == [
        ("L1", "N9", "theta", True), ("L2", "N3", "theta", True), ("L3", "N4", "decisive", False),
        ("L4", "N5", "mate", True)]
    # θ decreases with the level: the same line enters at 2400 and not at 1500
    e = _line(impact=100, p_att=0.4, p_walk=0.4)          # 0.16
    assert filter_lines([e], "ge2400", sc) and not filter_lines([_line(impact=100, p_att=0.4, p_walk=0.4)],
                                                                "1200_1600", sc)


def test_build_lines_threat_and_refutation(cfg):
    sc = cfg.thresholds.scoring
    root = node("N1", START.fen(), "E0", [mpv("e2e4", "e4", 30, ["e4"]), mpv("a2a3", "a3", -20, ["a3"], rank=2)],
                maia=pol(e2e4=0.6, a2a3=0.3))
    nb = START.copy()
    nb.push(chess.Move.null())
    null = node("N2", nb.fen(), "E1", [mpv("e7e5", "e5", -170, ["e5", "a3"])], path=["--"])   # free tempo: 2 pawns
    b = START.copy()
    b.push_uci("a2a3")
    e2 = node("N3", b.fen(), "E2", [mpv("e7e5", "e5", -60, ["e5", "e4", "d5"])], parent="N1",
              via=("a2a3", "a3"), maia=pol(e7e5=0.7), path=["a3"])
    root["multipv"][0]["rank"] = 1
    lines = build_lines([root, null, e2], "w", {"w": 1500, "b": 1500}, sc,
                        lambda fen, s, o: {"e7e5": 0.5, "d7d5": 0.5}, {"e2e4": 0, "a2a3": 50})
    th, ref = lines
    # null move: impact = 30 - (-170) = 200; a3 (loss 50 < 100) parries, e4 too -> p_walk = 1 - 0.9
    assert (th.kind, th.attacker, th.impact_cp, th.p_walk) == ("threat", "b", 200, pytest.approx(0.1))
    assert th.p_att == pytest.approx(0.5)                 # the first black move
    # refutation of a3: impact = 30 - (-60) = 90, p_walk = p(a3) × path(N1) = 0.3
    assert (ref.kind, ref.impact_cp, ref.p_walk, ref.entry["san"]) == ("refutation", 90, pytest.approx(0.3), "a3")
    assert ref.p_att == pytest.approx(0.5)                # e5 (d5 is a quiet follow-up)


def test_static_t_and_relative(cfg):
    sc = cfg.thresholds.scoring
    feats = [Feature("isolated_pawn", "w", ["d4"]), Feature("passed_pawn", "b", ["a5"], {}),
             Feature("inactive_piece", "w", ["a1"]), Feature("inactive_piece", "b", ["a8"]),
             Feature("inactive_piece", "b", ["h8"])]
    own, opp = sc.static["pawn_structure"].own, sc.static["pawn_structure"].opp
    t, used = static_t("pawn_structure", "w", feats, sc)
    assert t == 100 - own["isolated_pawn"] - opp["passed_pawn"] and used == [0, 1]
    # piece_activity is relative: White has one inactive piece, Black two -> White 100, Black 100 - 8
    k = sc.static["piece_activity"].own["inactive_piece"]
    assert static_t("piece_activity", "w", feats, sc)[0] == 100
    assert static_t("piece_activity", "b", feats, sc)[0] == 100 - k


def test_advice_bands(cfg):
    sc = cfg.thresholds.scoring
    assert [advice(t, sc) for t in (100, 85, 84, 60, 59, 30, 29)] == [
        "no_worry", "no_worry", "monitor", "monitor", "attention", "attention", "critical"]


def test_t_combination_override_and_r(cfg):
    sc = cfg.thresholds.scoring
    root = node("N1", START.fen(), "E0", [mpv("e2e4", "e4", 0, ["e4"])], maia=pol(e2e4=1.0))
    line = _line(impact=300, p_att=0.5, p_walk=0.4, attacker="b")      # against White, risk 0.6
    line.id, line.tags, line.primary = "L1", ["king_safety"], "king_safety"
    cats = {c["id"]: c for c in score_categories(cfg, [root], [], [line], "w", "middlegame", False, "1600_2000")}
    ks = cats["king_safety"]
    k, w = sc.k["king_safety"], sc.w["king_safety"]
    t_dyn = 100 * math.exp(-0.6 / k)
    t = w * t_dyn + (1 - w) * 100
    t = min(t, sc.override.t_max)                         # decisive impact with P_att 0.5 >= 0.10
    assert ks["T"] == {"w": round(t), "b": 100} and ks["components"]["override"] == {"w": True, "b": False}
    assert ks["advice"] == "critical" and ks["balance"] == round(t) - 100 and ks["trace"]["lines"] == ["L1"]
    rel = sc.relevance
    prox = 100.0 * min(1.0, 0.6 / sc.theta["1600_2000"])  # the line starts one half-move from the root
    raw = (rel.weights["worry"] * (100 - round(t)) + rel.weights["balance"] * abs(round(t) - 100)
           + rel.weights["proximity"] * prox) / sum(rel.weights.values())
    assert ks["R"] == round(rel.phase["middlegame"]["king_safety"] * raw)
    assert cats["material"]["T"] == {"w": 100, "b": 100} and cats["material"]["R"] == 0


def test_confidence_low_when_saturated_or_unstable(cfg):
    root = node("N1", START.fen(), "E0", [mpv("e2e4", "e4", 0, ["e4"])], maia=pol(e2e4=1.0))
    assert all(c["confidence"] == "low" for c in score_categories(cfg, [root], [], [], "w", "opening", True, "ge2400"))
    root["unstable_depth"] = True
    assert all(c["confidence"] == "low" for c in score_categories(cfg, [root], [], [], "w", "opening", False, "ge2400"))


def test_quiescent_leaf_follows_the_line():
    b = chess.Board("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
    # horizon 1: e4xd5 is the only move; the line has no more moves -> SEE: nothing to take
    leaf = quiescent_leaf(b, ["exd5"], 1, 1, 4)
    assert leaf.board_fen() == "4k3/8/8/3P4/8/8/8/4K3"
    # horizon 0: the next move of the line is a capture, so it is played
    assert quiescent_leaf(b, ["exd5", "Kd7"], 0, 1, 4).board_fen() == "4k3/8/8/3P4/8/8/8/4K3"


def test_override_only_on_the_primary_category(cfg):
    sc = cfg.thresholds.scoring
    root = node("N1", START.fen(), "E0", [mpv("e2e4", "e4", 0, ["e4"])], maia=pol(e2e4=1.0))
    line = _line(kind="threat", impact=300, p_att=0.5, p_walk=0.01, attacker="b")     # risk 0.015
    line.id, line.tags, line.primary = "L1", ["king_safety", "threats_dynamics"], "threats_dynamics"
    cats = {c["id"]: c for c in score_categories(cfg, [root], [], [line], "w", "middlegame", False, "1600_2000")}
    assert cats["threats_dynamics"]["T"]["w"] == sc.override.t_max and cats["threats_dynamics"]["advice"] == "critical"
    assert cats["king_safety"]["components"]["override"]["w"] is False and cats["king_safety"]["T"]["w"] > 90
