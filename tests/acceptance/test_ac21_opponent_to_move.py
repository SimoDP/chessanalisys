"""AC-21 (pack): Najdorf after 6.Be3, user White, Black to move."""

from __future__ import annotations

import re

from tests.recorded import recorded_pack


def test_opponent_pack(cfg, root):
    pack, _, _ = recorded_pack(cfg, root, "najdorf_after_be3", "w", 1900)
    assert pack["position"]["user_to_move"] is False
    assert pack["recommendation"] is None and pack["engine"]["candidates"] == []
    replies = pack["engine"]["replies"]
    assert [r["id"] for r in replies] == [f"R{k}" for k in range(1, len(replies) + 1)]
    assert [r["p_opp"] for r in replies] == sorted((r["p_opp"] for r in replies), reverse=True)
    sel = cfg.thresholds.selection
    for r in replies:
        assert r["user_best"] and all(re.fullmatch(rf"{r['id']}\.u[123]", u["id"]) for u in r["user_best"])
        assert r["user_best"][0]["loss_cp"] == 0
    # the two best replies for Stockfish are always included
    root_node = pack["nodes"][0]
    best2 = {ln["uci"] for ln in root_node["multipv"][: sel.replies_best_sf]}
    assert best2 <= {r["uci"] for r in replies}
    phases = {p["phase"]: p["reason"] for p in pack["omitted_phases"]}
    assert phases["E2b"] == phases["E3"] == "opponent_to_move"
    assert {n["phase"] for n in pack["nodes"]} == {"E0", "E1", "R"}
    reasons = {o["id"]: o["reason"] for o in pack["omitted_sections"]}
    assert reasons["S03"] == reasons["S08"] == "opponent_to_move"
    plan = {s["id"]: s for s in pack["section_plan"]}
    assert plan["S07"]["title"] == "Risposte probabili del Bianco e come prepararsi".replace("Bianco", "Nero")
    assert plan["S07"]["must_cover"] == [r["id"] for r in replies]
    t1 = pack["tables"]["T1"]
    assert [c["key"] for c in t1["columns"]] == ["reply", "p_opp", "eval", "user_best", "prepare"]
    assert [row["id"] for row in t1["rows"]] == [r["id"] for r in replies]
