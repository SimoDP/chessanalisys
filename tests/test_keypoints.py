"""Key points chosen and ordered by the code (plan/keypoints.py) and the radar with the opponent to move.
Frozen bench packs and the user's real case; no engines."""

from __future__ import annotations

import json

import pytest

from chessanalyst import bench
from chessanalyst.pack.builder import rescore_pack
from chessanalyst.plan.keypoints import key_points


def _kp(cfg, name: str) -> dict[str, dict]:
    pack = bench.load_pack(cfg, bench.load_spec(cfg, name))
    return {k["type"]: k for k in key_points(cfg, pack)}, pack


def test_user_case_e4_wins(cfg):
    kp, _ = _kp(cfg, "e4_wins_w_1700")
    assert list(kp) == ["verdict", "main_danger", "likely_reply", "opportunity", "plan", "reasoning"]
    assert "R5" not in kp["verdict"]["ids"] and kp["verdict"]["facts"]["best"]["told_in"] == "main_danger"
    v = kp["verdict"]["facts"]
    assert v["band"] == "decisive_minus" and v["better"] == "opp" and v["best"]["ref"] == "R5"
    assert any(a["square"] == "c3" and a["discovered"] for a in v["best"]["move"]["attacks"])   # why: Bf6 on Nc3
    d = kp["main_danger"]["facts"]
    assert d["ref"] == "R5" and d["san"] == "e4" and d["p_opp"] < 0.05 and d["damage_cp"] >= 400
    first = kp["likely_reply"]["facts"]["replies"][0]
    assert first["ref"] == "R1" and first["answer"]["ref"] == "R1.u1" and first["good_answers"] == ["R1.u1"]
    assert first["trap"]["ref"] == "R1.u3" and first["trap"]["p_user"] > 0.9
    opp = kp["opportunity"]["facts"]["replies"][0]
    assert opp["ref"] == "R4" and opp["answer"]["ref"] == "R4.u1" and opp["answer"]["move"]["captures"]


def test_every_reply_is_in_one_point_only(cfg):
    for name in bench.bench_cfg(cfg)["positions"]:
        pack = bench.load_pack(cfg, bench.load_spec(cfg, name))
        subjects = []
        for k in key_points(cfg, pack):
            if k["type"] == "main_danger" and "ref" in k["facts"]:
                subjects.append(k["facts"]["ref"])
            subjects += [r["ref"] for r in k["facts"].get("replies", [])]
        assert len(subjects) == len(set(subjects)), name


def test_only_move_and_only_answer(cfg):
    kp, _ = _kp(cfg, "iso_e3_w_1700")
    r = kp["recommendation"]["facts"]
    assert r["ref"] == "C1" and r["san"] == "b3" and r["only_move"] and r["second"]["ref"] == "C2"
    assert r["second"]["is_trap"] and "trap" not in r
    assert kp["verdict"]["facts"]["positional"] is True                # equal material, +2,58
    ne5 = next(x for x in kp["likely_reply"]["facts"]["replies"] if x["san"] == "Ne5")
    assert ne5["ref"] == "Ne5@N3" and ne5["answer"]["ref"] == "bxc5@N8" and ne5["only_answer"]
    nd2 = kp["opportunity"]["facts"]["replies"][0]                      # 28...Nd2 leaves e3 to the rook
    assert nd2["san"] == "Nd2" and nd2["gain_cp"] >= cfg.thresholds.keypoints.opportunity_gain_cp


def test_fork_islands_and_loose_pawn(cfg):
    kp, _ = _kp(cfg, "knight_a4_w_1700")
    attacked = {a["square"] for a in kp["recommendation"]["facts"]["move"]["attacks"]}
    assert {"b6", "c5"} <= attacked                                      # Na4 forks queen and pawn
    items = kp["plan"]["facts"]["items"]
    assert {"key": "pawn_island_count", "of": "opp", "value": 3, "user_value": 2} in items
    assert any(i["key"] == "to_defend" and i["squares"] == ["b2"] for i in items)


def test_opponent_to_move_danger_is_its_best_move(cfg):
    kp, _ = _kp(cfg, "knight_d6_b_1700")
    d = kp["main_danger"]["facts"]
    assert d["ref"] == "R1" and d["san"] == "Nd6" and d["p_opp"] > 0.4
    assert "opportunity" not in kp                       # without Nd6 the game is level: no gift


def test_draw_and_systems(cfg):
    kp, _ = _kp(cfg, "rook_checks_b_1700")
    assert kp["verdict"]["facts"]["band"] == "equal" and "best" not in kp["verdict"]["facts"]
    assert kp["verdict"]["facts"]["tablebase"] == "draw" and "main_danger" not in kp
    assert any(i["key"] == "check_available" and i["of"] == "opp" for i in kp["plan"]["facts"]["items"])
    kp, _ = _kp(cfg, "bogo_c5_w_1700")
    assert len(kp["systems"]["ids"]) >= cfg.thresholds.keypoints.systems_min_moves
    assert kp["recommendation"]["facts"]["only_move"] is False
    assert {"key": "context_move", "of": "opp", "san": "Nc6"} in kp["plan"]["facts"]["items"]


def test_detail_changes_how_many_points(cfg):
    pack = bench.load_pack(cfg, bench.load_spec(cfg, "iso_e3_w_1700"))
    for d, n in cfg.thresholds.keypoints.max_points.items():
        p = dict(pack, user=dict(pack["user"], detail_level=int(d)))
        pts = key_points(cfg, p)
        assert len(pts) <= n and pts[0]["type"] == "verdict"
        assert [k["id"] for k in pts] == [f"K{i}" for i in range(1, len(pts) + 1)]


# --- radar with the opponent to move (its best move at the root is a threat) ----------------------


def _node_policy(pack: dict):
    """Maia-2 of the frozen nodes; elsewhere every move «found» (p = 1), so the first move decides P_att."""
    by_fen = {n["fen"]: {e["uci"]: e["p"] for e in n["maia"]["policy"]} for n in pack["nodes"] if n.get("maia")}

    def policy(fen, elo_self, elo_oppo):
        return by_fen.get(fen) or _AnyMove()
    return policy


class _AnyMove(dict):
    def get(self, key, default=None):
        return 1.0


@pytest.fixture
def user_case(root):
    return json.loads((root / "fixtures/user_cases/e4_wins_w_1700.pack.json").read_text(encoding="utf-8"))


def test_radar_sees_the_opponents_winning_move(cfg, user_case):
    before = {c["id"]: c["advice"] for c in user_case["categories"]}
    assert before["threats_dynamics"] == before["king_safety"] == "no_worry"       # the bug of the real case
    new = rescore_pack(cfg, user_case, _node_policy(user_case))
    root_threats = [ln for ln in new["filtered_lines"] if ln["kind"] == "threat" and ln["start_node"] == "N1"]
    assert root_threats and root_threats[0]["plies"][0] == "e4" and root_threats[0]["against_user"]
    after = {c["id"]: c["advice"] for c in new["categories"]}
    assert after["threats_dynamics"] in ("attention", "critical")
    s09 = next(s for s in new["section_plan"] if s["id"] == "S09")
    assert s09["must_cover"] == [ln["id"] for ln in new["filtered_lines"] if not ln["visible_at_level"]]
    # the frozen bench pack carries the rescored radar (live Maia-2)
    bench_pack = bench.load_pack(cfg, bench.load_spec(cfg, "e4_wins_w_1700"))
    assert {c["id"]: c["advice"] for c in bench_pack["categories"]}["threats_dynamics"] in ("attention", "critical")


def test_rescore_keeps_a_pack_with_the_user_to_move(cfg):
    pack = bench.load_pack(cfg, bench.load_spec(cfg, "iso_e3_w_1700"))
    new = rescore_pack(cfg, pack, _node_policy(pack))
    assert not any(ln["start_node"] == "N1" and ln["kind"] == "threat" for ln in new["filtered_lines"])
