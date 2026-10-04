"""M3 exit criterion (§13): every T and R is traceable to features or lines, and recomputable from them.

On every frozen pack: T_stat from the traced features (§5-bis.4 point 3), T_dyn from the traced lines
(point 2), T from the combination and the override (points 4–5), R from its terms (point 6); every line of
the report satisfies the filter of §5-bis.3; T4 follows R.
"""

from __future__ import annotations

import json
import math

import pytest

from chessanalyst.features.model import Feature
from chessanalyst.scoring.categories import static_t

PACKS = ["examples/golden/packs/najdorf_w_1500", "examples/golden/packs/najdorf_w_1900",
         "examples/golden/packs/najdorf_w_2400", "examples/golden/packs/najdorf_after_be3_w_1900",
         "fixtures/packs/fried_liver_w_1500", "fixtures/packs/rook_endgame_w_1900", "fixtures/packs/lucena_w_1900"]


def load(root, name):
    return json.loads((root / f"{name}.pack.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", PACKS)
def test_every_t_and_r_is_traceable(cfg, root, name):
    pack = load(root, name)
    sc = cfg.thresholds.scoring
    me = pack["user"]["color"]
    band = pack["user"]["band"]
    feats = [Feature(**f) for f in pack["features"]]
    lines = {ln["id"]: ln for ln in pack["filtered_lines"]}
    pvs = {p["id"] for p in pack["engine"]["pvs"]}
    nodes = {n["id"] for n in pack["nodes"]}
    assert [c["id"] for c in pack["categories"]] == sc.categories
    for c in pack["categories"]:
        cat, comp, tr = c["id"], c["components"], c["trace"]
        assert set(tr["lines"]) <= set(lines) and set(tr["pvs"]) <= pvs and set(tr["nodes"]) <= nodes
        assert all(0 <= i < len(feats) for i in tr["features"])
        # the traced lines are exactly the report's lines with this tag
        assert tr["lines"] == [i for i, ln in lines.items() if cat in ln["tags"]]
        for s in ("w", "b"):
            if cat == "practical_complexity":
                assert tr["nodes"] and c["T"][s] == comp["T_stat"][s]
                continue
            t_stat, used = static_t(cat, s, feats, sc)
            assert set(used) <= set(tr["features"]) and round(t_stat) == comp["T_stat"][s]
            risk = sum(lines[i]["risk"] for i in tr["lines"] if lines[i]["defender"] == s)
            assert comp["risk"][s] == pytest.approx(risk, abs=1e-4)
            t_dyn = 100 * math.exp(-risk / sc.k[cat])
            assert round(t_dyn) == comp["T_dyn"][s]
            t = sc.w[cat] * t_dyn + (1 - sc.w[cat]) * t_stat
            override = any((lines[i]["reason"] == "mate" or lines[i]["impact_cp"] >= sc.decisive_cp)
                           and lines[i]["p_att"] >= sc.override.p_att_min and lines[i]["primary"] == cat
                           and lines[i]["defender"] == s for i in tr["lines"])
            assert comp["override"][s] == override
            assert c["T"][s] == round(min(t, sc.override.t_max) if override else t)
        opp = "b" if me == "w" else "w"
        assert c["balance"] == c["T"][me] - c["T"][opp]
        rel = sc.relevance
        wt = rel.weights
        raw = (wt["worry"] * (100 - min(c["T"].values())) + wt["balance"] * abs(c["balance"])
               + wt["proximity"] * comp["proximity"] + wt["decision"] * comp["decision"]) / sum(wt.values())
        assert abs(c["R"] - rel.phase[pack["profile"]["phase"]][cat] * raw) <= 1     # proximity/decision rounded


@pytest.mark.parametrize("name", PACKS)
def test_filtered_lines_satisfy_the_filter(cfg, root, name):
    pack = load(root, name)
    sc = cfg.thresholds.scoring
    theta = sc.theta[pack["user"]["band"]]
    for k, ln in enumerate(pack["filtered_lines"], 1):
        assert ln["id"] == f"L{k}" and ln["impact_cp"] >= sc.lines.impact_min_cp
        assert ln["risk"] == pytest.approx(ln["p_att"] * ln["p_walk"] * ln["impact_cp"] / 100, abs=1e-4)
        assert ln["p_att"] == pytest.approx(math.prod(m["p"] for m in ln["attacker_moves"]), abs=1e-3)
        if ln["reason"] == "theta":
            assert ln["risk"] >= theta and ln["visible_at_level"]
        else:   # forced mate or decisive loss: always in, invisible with a low P_att
            assert ln["risk"] < theta and ln["visible_at_level"] == (ln["p_att"] >= sc.visible_p_att_min)
        assert ln["primary"] in ln["tags"]


@pytest.mark.parametrize("name", PACKS)
def test_t4_follows_r(cfg, root, name):
    pack = load(root, name)
    if pack["profile"]["matrix_column"] == 4:
        assert "T4" not in pack["tables"]
        return
    rows = pack["tables"]["T4"]["rows"]
    cats = {c["id"]: c for c in pack["categories"]}
    rs = [cats[r["id"]]["R"] for r in rows]
    assert rs == sorted(rs, reverse=True) and len(rows) == min(9, cfg.tables["T4"]["rows_max"][pack["user"]["anchor"]])
    me = pack["user"]["color"]
    assert all(r["cells"]["T"] == str(cats[r["id"]]["T"][me]) for r in rows)
    s09 = next(s for s in pack["section_plan"] if s["id"] == "S09")
    assert s09["must_cover"] == [ln["id"] for ln in pack["filtered_lines"] if not ln["visible_at_level"]] \
        or not s09["required"]
