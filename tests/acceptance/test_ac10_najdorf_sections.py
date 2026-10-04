"""AC-10: Najdorf, anchors 1500 and 1900 (M1b, M1c) and 2400 (M2), checked on the versioned
``rendered`` files and on a recorded answer of the real model."""

from __future__ import annotations

import re

import pytest

from chessanalyst.config import SECTION_IDS
from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.pack.section_plan import fill_opp
from chessanalyst.render.report import REPORT_TITLE

EXPECTED = {   # sections after matrix, milestone and §8.2-bis (column 1, user to move); S02 and S09 from M3
    "1500": ["S01", "S02", "S03", "S05", "S06", "S07", "S08", "S09", "S10"],
    "1900": ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"],
    # 2400: S04 absorbed in S03, S05 and S10 excluded (band_2400); S08 by c8 (natural_trap, hard_move):
    # no such move in the frozen pack (Stockfish 19), so S08 is omitted with «no_classified_move»
    "2400": ["S01", "S02", "S03", "S06", "S07", "S09", "S11"],   # S11: c11 (M4)
}
ANCHORS = ["1500", "1900", "2400"]


@pytest.mark.parametrize("anchor", ANCHORS)
def test_rendered_sections(cfg, root, anchor):
    doc = (root / "examples" / "golden" / "rendered" / f"najdorf_w_{anchor}.md").read_text(encoding="utf-8")
    titles = [h for h in re.findall(r"^## (.+)$", doc, re.M) if h != REPORT_TITLE]
    expected = [fill_opp(cfg.section_titles[s][anchor], "il Nero") for s in EXPECTED[anchor]]
    assert titles == expected
    order = [SECTION_IDS.index(s) for s in EXPECTED[anchor]]
    assert order == sorted(order)                                # §8.1 order
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    plan = {s["id"]: s for s in pack["section_plan"]}
    report = doc.split(f"## {REPORT_TITLE}")[1]
    if anchor == "1500":
        assert plan["S04"]["absorbed_into"] == "S03" and "S04 in S03" in report
        assert plan["S08"]["required"]                           # always present at 1500 (D-48)
        assert "S11 (elo<2000)" in report
    elif anchor == "2400":
        assert plan["S04"]["absorbed_into"] == "S03" and "S04 in S03" in report
        assert "S05 (band_2400)" in report and "S10 (band_2400)" in report
        assert plan["S07"]["tables"] == ["T1", "T2"]              # move order at 2400 (§8.5)
        assert not plan["S08"]["required"] and "S08 (no_classified_move)" in report
        assert "S11" not in [o["id"] for o in pack["omitted_sections"]]   # c11 from M4: 2400 >= 2000
    else:
        assert "assorbite: nessuna" in report
        assert plan["S08"]["required"] == bool(plan["S08"]["must_cover"])    # c8
    for o in pack["omitted_sections"]:
        assert f"{o['id']} ({o['reason']})" in report


# -- M1c: a recorded response of the real model --------------------------------------------

@pytest.mark.parametrize("anchor", ANCHORS)
def test_real_model_sections(cfg, anchor):
    from tests.real_llm import replay

    pack, res = replay(cfg, f"najdorf_w_{anchor}")
    titles = [h for h in re.findall(r"^## (.+)$", res.document, re.M) if h != REPORT_TITLE]
    assert titles == [fill_opp(cfg.section_titles[s][anchor], "il Nero") for s in EXPECTED[anchor]]
    report = res.document.split(f"## {REPORT_TITLE}")[1]
    for o in pack["omitted_sections"]:
        assert f"{o['id']} ({o['reason']})" in report
    assert "{{" not in res.document
