"""AC-26: SectionPlan for anchors 1500, 1900, 2400 (user White and Black)."""

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
    assert req == ["S01", "S03", "S05", "S06", "S07", "S08", "S10"]
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
    assert p["S03"]["word_budget"] == round(650 * w["S03"] / s / 10) * 10


@pytest.mark.parametrize("color", ["w", "b"])
def test_anchor_1900(cfg, color):
    p, omitted, _ = plan(cfg, "1900", "1600_2000", color)
    req = [s for s, e in p.items() if e["required"]]
    assert req == ["S01", "S03", "S04", "S05", "S06", "S07", "S08", "S10"]
    assert p["S04"]["title"] == "Dove ti arrocchi"
    assert p["S06"]["tables"] == ["T3"] and p["S06"]["maia_low_confidence"] is True
    assert p["S07"]["tables"] == ["T1"]             # T2 at 1900 only with detail 5 (M4)
    assert p["S08"]["maia_low_confidence"] and p["S08"]["theory_allowed"] is False
    reasons = {o["id"]: o["reason"] for o in omitted}
    assert reasons["S02"] == "milestone" and reasons["S11"] == "elo<2000" and reasons["S12"] == "matrix"


@pytest.mark.parametrize("color", ["w", "b"])
def test_anchor_2400(cfg, color):
    p, omitted, _ = plan(cfg, "2400", "ge2400", color)
    req = [s for s, e in p.items() if e["required"]]
    assert req == ["S01", "S03", "S06", "S07", "S08"]
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


def test_other_columns_in_m1(cfg):
    pi = PlanInput("1900", "1600_2000", 1900, 2, {"w": "can_both", "b": "can_both"}, True, "il Nero",
                   EXPL, 4, {"C3": "hard_move"}, [], "C1", False, False, False)
    entries, omitted, warnings = build_section_plan(cfg, pi)
    req = [e["id"] for e in entries if e["required"]]
    assert req == ["S01", "S06", "S07", "S10"] and warnings == ["profile_unsupported"]
    assert {o["id"]: o["reason"] for o in omitted}["S05"] == "unsupported_profile"
