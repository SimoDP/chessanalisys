"""AC-10 (M1b): Najdorf, anchors 1500 and 1900, checked on the versioned ``rendered`` files."""

from __future__ import annotations

import re

import pytest

from chessanalyst.config import SECTION_IDS
from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.pack.section_plan import fill_opp
from chessanalyst.render.report import REPORT_TITLE

EXPECTED = {   # sections after matrix, milestone and §8.2-bis (column 1, user to move, M1)
    "1500": ["S01", "S03", "S05", "S06", "S07", "S08", "S10"],
    "1900": ["S01", "S03", "S04", "S05", "S06", "S07", "S08", "S10"],
}


@pytest.mark.parametrize("anchor", ["1500", "1900"])
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
    else:
        assert "assorbite: nessuna" in report
        assert plan["S08"]["required"] == bool(plan["S08"]["must_cover"])    # c8
    for o in pack["omitted_sections"]:
        assert f"{o['id']} ({o['reason']})" in report


# -- M1c: a recorded response of the real model --------------------------------------------

@pytest.mark.parametrize("anchor", ["1500", "1900"])
def test_real_model_sections(cfg, anchor):
    from tests.real_llm import replay

    pack, res = replay(cfg, f"najdorf_w_{anchor}")
    titles = [h for h in re.findall(r"^## (.+)$", res.document, re.M) if h != REPORT_TITLE]
    assert titles == [fill_opp(cfg.section_titles[s][anchor], "il Nero") for s in EXPECTED[anchor]]
    report = res.document.split(f"## {REPORT_TITLE}")[1]
    for o in pack["omitted_sections"]:
        assert f"{o['id']} ({o['reason']})" in report
    assert "{{" not in res.document
