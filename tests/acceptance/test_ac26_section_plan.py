"""AC-26: SectionPlan for anchors 1500, 1900, 2400 (user White and Black); from M3 with S02 and S09."""

from __future__ import annotations

import pytest

from chessanalyst.pack.section_plan import PlanInput, build_section_plan

EXPL = ["C1", "C2", "C3", "C4", "C5"]


def plan(cfg, anchor, band, color="w", user_to_move=True, **kw):
    opp = "il Nero" if color == "w" else "il Bianco"
    pi = PlanInput(anchor=anchor, band=band, elo_ref_fide={"1500": 1500, "1900": 1900, "2400": 2400}[anchor],
                   matrix_column=1, castling={"w": "can_both", "b": "can_both"}, user_to_move=user_to_move,
                   opp_color_name=opp, explained=EXPL if user_to_move else [], explained_low_loss=4,
                   categories={"C1": "solid", "C3": "hard_move", "C6": "natural_trap"},
                   replies=[] if user_to_move else ["R1", "R2"], recommendation="C1" if user_to_move else None,
                   has_t2=True, has_t3=True, maia_low=anchor != "1500", **kw)
    entries, omitted, warnings = build_section_plan(cfg, pi)
    return {e["id"]: e for e in entries}, omitted, warnings


@pytest.mark.parametrize("color,opp", [("w", "il Nero"), ("b", "il Bianco")])
def test_anchor_1500(cfg, color, opp):
    p, omitted, _ = plan(cfg, "1500", "1200_1600", color)
    req = [s for s, e in p.items() if e["required"]]
    assert req == ["S01", "S02", "S03", "S05", "S06", "S07", "S08", "S09", "S10"]
    assert p["S02"]["title"] == "Radar semplificato" and p["S02"]["theory_allowed"] is False
    assert p["S09"]["title"] == "Minacce invisibili al tuo livello" and p["S09"]["must_cover"] == []
    assert p["S04"]["absorbed_into"] == "S03" and p["S04"]["title"] is None and not p["S04"]["required"]
    assert p["S03"]["title"] == "Le tre cose da fare adesso" and p["S03"]["must_cover"] == ["C1"]
    assert p["S06"]["title"] == f"Cosa fa {opp}"
    assert p["S06"]["tables"] == []                 # T3 only at anchors 1900, 2400
    assert p["S08"]["theory_allowed"] is True and p["S08"]["must_cover"] == ["C3", "C6"]
    assert p["S07"]["tables"] == ["T1"] and p["S07"]["must_cover"] == EXPL
    assert p["S07"]["max_pv_plies"] == 4
    assert {o["id"]: o["reason"] for o in omitted}["S11"] == "elo<2000"   # matrix (c11) comes first
    total = sum(e["word_budget"] for e in p.values() if e["required"])
    assert abs(total - cfg.thresholds.band_params["1200_1600"].prose_words) <= 30
    # S03 carries the weight of the absorbed S04 (absent at 1500): 0.25 / sum
    w = cfg.section_budget["1500"]
    s = sum(w[k] for k in req)
    pw = cfg.thresholds.band_params["1200_1600"].prose_words
    assert p["S03"]["word_budget"] == round(pw * w["S03"] / s / 10) * 10


@pytest.mark.parametrize("color", ["w", "b"])
def test_anchor_1900(cfg, color):
    p, omitted, _ = plan(cfg, "1900", "1600_2000", color)
    req = [s for s, e in p.items() if e["required"]]
    assert req == ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"]
    assert p["S04"]["title"] == "Dove ti arrocchi"
    assert p["S06"]["tables"] == ["T3"] and p["S06"]["maia_low_confidence"] is True
    assert p["S07"]["tables"] == ["T1"]             # T2 at 1900 only with detail 5 (M4)
    assert p["S08"]["maia_low_confidence"] and p["S08"]["theory_allowed"] is False
    reasons = {o["id"]: o["reason"] for o in omitted}
    assert "S02" not in reasons and reasons["S11"] == "elo<2000" and reasons["S12"] == "matrix"


@pytest.mark.parametrize("color", ["w", "b"])
def test_anchor_2400(cfg, color):
    p, omitted, _ = plan(cfg, "2400", "ge2400", color)
    req = [s for s, e in p.items() if e["required"]]
    assert req == ["S01", "S02", "S03", "S06", "S07", "S08", "S09", "S11"]       # S11: c11 (M4)
    assert p["S02"]["title"] == "Fattori decisivi" and p["S11"]["title"] == "Note da maestro"
    assert p["S04"]["absorbed_into"] == "S03"
    assert p["S03"]["title"] == "Piani per struttura"
    assert p["S07"]["title"] == "Mosse candidate e test di move order" and p["S07"]["tables"] == ["T1", "T2"]
    assert p["S08"]["must_cover"] == ["C3", "C6"]   # only natural_trap and hard_move count
    reasons = {o["id"]: o["reason"] for o in omitted}
    assert reasons["S05"] == "band_2400" and reasons["S10"] == "band_2400"


def test_2400_without_counting_categories_omits_s08(cfg):
    pi = PlanInput("2400", "ge2400", 2400, 1, {"w": "can_both", "b": "can_both"}, True, "il Nero",
                   EXPL, 4, {"C2": "practical_alt"}, [], "C1", False, False, True)
    entries, omitted, _ = build_section_plan(cfg, pi)
    assert {o["id"]: o["reason"] for o in omitted}["S08"] == "no_classified_move"


def test_c4_without_castling_rights(cfg):
    p, omitted, _ = plan(cfg, "1900", "1600_2000")
    pi = PlanInput("1900", "1600_2000", 1900, 1, {"w": "castled_short", "b": "lost"}, True, "il Nero",
                   EXPL, 4, {}, [], "C1", False, False, False)
    entries, omitted, _ = build_section_plan(cfg, pi)
    assert {o["id"]: o["reason"] for o in omitted}["S04"] == "matrix"


@pytest.mark.parametrize("anchor,band", [("1500", "1200_1600"), ("1900", "1600_2000"), ("2400", "ge2400")])
def test_opponent_to_move(cfg, anchor, band):
    p, omitted, _ = plan(cfg, anchor, band, user_to_move=False)
    reasons = {o["id"]: o["reason"] for o in omitted}
    assert reasons["S03"] == reasons["S08"] == "opponent_to_move"
    if anchor != "1900":
        assert reasons["S04"] == "opponent_to_move"
    assert p["S07"]["title"] == "Risposte probabili del Nero e come prepararsi"
    assert p["S07"]["must_cover"] == ["R1", "R2"] and p["S07"]["tables"] == ["T1"]


def _other(cfg, col, **kw):
    pi = PlanInput("1900", "1600_2000", 1900, col, kw.pop("castling", {"w": "can_both", "b": "can_both"}), True,
                   "il Nero", EXPL, 4, kw.pop("categories", {"C3": "hard_move"}), [], "C1", False, False, False, **kw)
    entries, omitted, warnings = build_section_plan(cfg, pi)
    return entries, {o["id"]: o["reason"] for o in omitted}, warnings


def test_column_2_tactical_from_m2(cfg):
    # M2: complete matrix (§8.3); S13 mandatory, S05 only with involved pieces (c5)
    entries, omitted, warnings = _other(cfg, 2, focus_squares=["c4", "g5"])
    p = {e["id"]: e for e in entries}
    req = [e["id"] for e in entries if e["required"]]
    assert req == ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S13"] and warnings == []
    assert p["S05"]["focus_squares"] == ["c4", "g5"] and p["S13"]["title"] == "Tattica forzata"
    assert p["S13"]["theory_allowed"] is False and omitted["S12"] == "matrix"
    assert all(e["focus_squares"] == [] for e in entries if e["id"] != "S05")


def test_column_2_without_involved_pieces_omits_s05(cfg):
    _, omitted, _ = _other(cfg, 2, focus_squares=[])
    assert omitted["S05"] == "matrix"


def test_column_3_endgame(cfg):
    entries, omitted, warnings = _other(cfg, 3, castling={"w": "lost", "b": "lost"})
    p = {e["id"]: e for e in entries}
    req = [e["id"] for e in entries if e["required"]]
    assert req == ["S01", "S02", "S06", "S07", "S08", "S10", "S12"] and warnings == []
    assert omitted["S03"] == omitted["S04"] == omitted["S05"] == omitted["S13"] == "matrix"
    assert omitted["S09"] == "no_invisible_line"                         # c9 (M3)
    assert p["S12"]["theory_allowed"] is True and p["S12"]["must_cover"] == []


def test_column_4_tablebase(cfg):
    entries, omitted, _ = _other(cfg, 4, castling={"w": "lost", "b": "lost"}, tablebase=True)
    p = {e["id"]: e for e in entries}
    req = [e["id"] for e in entries if e["required"]]
    assert req == ["S01", "S06", "S07", "S10", "S12"]
    assert omitted["S08"] == "matrix" and p["S12"]["must_cover"] == ["N1"]    # the exact result is cited
    assert omitted["S02"] == omitted["S09"] == "matrix"
    total = sum(e["word_budget"] for e in entries if e["required"])
    assert abs(total - cfg.thresholds.band_params["1600_2000"].prose_words) <= 30


def test_m3_radar_and_invisible_lines(cfg):
    """S02 carries T4; S09 must cite the lines invisible at the level, and in column 3 exists only with them (c9)."""
    p, _, _ = plan(cfg, "1900", "1600_2000", has_t4=True, invisible_lines=["L2", "L5"])
    assert p["S02"]["tables"] == ["T4"] and p["S09"]["must_cover"] == ["L2", "L5"]
    entries, omitted, _ = _other(cfg, 3, castling={"w": "lost", "b": "lost"}, invisible_lines=["L1"])
    assert "S09" not in omitted and {e["id"]: e for e in entries}["S09"]["must_cover"] == ["L1"]


# -- detail 1–5 (§7.2, M4) -------------------------------------------------------------------------------------


@pytest.mark.parametrize("detail,expected", [
    (1, ["S01", "S02", "S03", "S05", "S06", "S07", "S09", "S10"]),        # only the mandatory ones of the matrix
    (2, ["S01", "S02", "S03", "S05", "S06", "S07", "S09", "S10"]),
    (3, ["S01", "S02", "S03", "S05", "S06", "S07", "S08", "S09", "S10"]),  # + S08
    (4, ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"]),
    (5, ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11"]),   # + S11 (c11)
])
def test_detail_sections_1900(cfg, detail, expected):
    p, omitted, _ = plan(cfg, "1900", "1600_2000", detail=detail, has_t4=True)
    assert [s for s, e in p.items() if e["required"]] == expected
    reasons = {o["id"]: o["reason"] for o in omitted}
    if detail <= 2:
        assert reasons["S04"] == reasons["S08"] == "detail"
    if detail <= 3:
        assert p["S06"]["tables"] == (["T3"] if detail == 3 else [])
    assert p["S02"]["tables"] == ["T4"] and p["S07"]["tables"] == (["T1", "T2"] if detail == 5 else ["T1"])
    plies = {1: 6, 2: 7, 3: 8, 4: 8, 5: 10}[detail]
    assert p["S07"]["max_pv_plies"] == plies
    total = sum(e["word_budget"] for e in p.values() if e["required"])
    words = cfg.thresholds.band_params["1600_2000"].prose_words * cfg.thresholds.detail[str(detail)].words
    assert abs(total - words) <= 10 * len(expected)


def test_detail_5_lifts_the_2400_exclusions(cfg):
    p, omitted, _ = plan(cfg, "2400", "ge2400", detail=5)
    req = [s for s, e in p.items() if e["required"]]
    assert {"S05", "S10", "S11"} <= set(req)
    assert p["S05"]["title"] == "Cosa vuole ogni pezzo" and p["S10"]["title"] == "Come ragionare"
    assert p["S07"]["max_pv_plies"] == 12                         # 12 + 2, at most 12
    p1, _, _ = plan(cfg, "1500", "1200_1600", detail=1)
    assert p1["S07"]["max_pv_plies"] == 2                         # 4 − 2, at least 2
    p5, om5, _ = plan(cfg, "1500", "1200_1600", detail=5)
    assert not p5["S11"]["required"] and {o["id"]: o["reason"] for o in om5}["S11"] == "band_1500"


def test_detail_helpers(cfg):
    from chessanalyst.detail import e3_active, effective_k

    assert [effective_k(cfg, "1600_2000", d) for d in (1, 2, 3, 4, 5)] == [3, 3, 4, 5, 5]
    assert effective_k(cfg, "lt1200", 3) == 2                     # explained_min + 1, at most K
    assert not e3_active(cfg, 1900, 3) and e3_active(cfg, 1900, 4) and e3_active(cfg, 2200, 1)
