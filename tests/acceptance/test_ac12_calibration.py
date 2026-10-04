"""AC-12: the same position at 1200 / 1900 / 2500 (FIDE) gives outputs that differ in at least two of: set of
sections, explained candidates, maximum line length, words (>= 25%). Checked on the packs built from the
recorded engines (sections and budgets of the SectionPlan, explained candidates, max_pv_plies), so that the
difference comes from the program and not from the model."""

from __future__ import annotations

import itertools

import pytest

from tests.recorded import recorded_pack

ELOS = (1200, 1900, 2500)


@pytest.fixture(scope="module")
def packs(cfg, root):
    return {elo: recorded_pack(cfg, root, "najdorf", "w", elo)[0] for elo in ELOS}


def traits(pack):
    plan = [s for s in pack["section_plan"] if s["required"]]
    return {
        "sections": tuple(s["id"] for s in plan),
        "explained": tuple(c["san"] for c in pack["engine"]["candidates"] if c["explained"]),
        "max_plies": pack["constraints"]["max_pv_plies"],
        "words": sum(s["word_budget"] for s in plan),
    }


def differences(a, b):
    out = [k for k in ("sections", "explained", "max_plies") if a[k] != b[k]]
    if abs(a["words"] - b["words"]) >= 0.25 * max(a["words"], b["words"]):
        out.append("words")
    return out


@pytest.mark.parametrize("lo,hi", list(itertools.combinations(ELOS, 2)))
def test_levels_differ_in_at_least_two_ways(packs, lo, hi):
    a, b = traits(packs[lo]), traits(packs[hi])
    assert len(differences(a, b)) >= 2, (a, b)


def test_levels_and_anchors(packs):
    assert [packs[e]["user"]["band"] for e in ELOS] == ["1200_1600", "1600_2000", "ge2400"]   # lower bound included
    assert [packs[e]["user"]["anchor"] for e in ELOS] == ["1500", "1900", "2400"]
    t = {e: traits(packs[e]) for e in ELOS}
    assert t[1200]["max_plies"] < t[1900]["max_plies"] < t[2500]["max_plies"]
    assert "S11" in t[2500]["sections"] and "S11" not in t[1900]["sections"]    # c11 (M4)
