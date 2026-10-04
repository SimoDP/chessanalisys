"""AC-16 (M1b, verification): each defective response of Appendix G.6 produces the
expected errors; in degraded mode every error ends up removed, marked or reported."""

from __future__ import annotations

import json

import pytest

from chessanalyst.render.markdown import RenderInfo, render_markdown
from chessanalyst.render.report import REPORT_TITLE
from chessanalyst.verify.degrade import degrade
from chessanalyst.verify.report import check_outcomes, verification_json
from tests.fault_fixtures import EXPECTED, OUT, build
from tests.llm_helpers import check_recorded, codes, pack_for, recorded


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_expected_errors(cfg, name):
    assert codes(check_recorded(cfg, name)) == EXPECTED[name][1]


def test_bad_plan_has_both_defects(cfg):
    res = check_recorded(cfg, "bad_plan.json")
    details = " ".join(e.detail for e in res.errors)
    assert "Qxd8 non è legale" in details and "scacco" in details


def test_contamination_names_the_term(cfg):
    res = check_recorded(cfg, "bad_contamination.json")
    assert {e.text for e in res.errors if e.code == "V09"} == {"Najdorf"}


def test_v09_skipped_on_the_example_position(cfg):
    # the Najdorf names are allowed when the analysed EPD is the example's (D-52)
    assert check_recorded(cfg, "good_najdorf_1900.json").errors == []


@pytest.mark.parametrize("name", sorted(n for n in EXPECTED if n.startswith("bad_")))
def test_no_unreported_error_in_degraded_mode(cfg, name):
    res = check_recorded(cfg, name)
    pack = pack_for(cfg, name)
    if res.output is None:          # V01 on the schema: no degraded mode (exit code 5 in M1c)
        assert codes(res) == {"V01"}
        return
    d = degrade(pack, res.output, res.errors)
    reported = d.removed + d.marked + d.warnings
    for e in res.errors:
        where = e.section or ""
        assert any(where in r for r in reported), (e.code, e.section, reported)
    info = RenderInfo(removed=d.removed, marked=d.marked, warnings=d.warnings,
                      checks=check_outcomes(res, d))
    doc = render_markdown(cfg, pack, d.output, info)            # V11 passes
    report = doc.split(f"## {REPORT_TITLE}")[1]
    for r in d.removed + d.marked:
        assert r in report
    vj = verification_json([res], d, cfg.wording["verify_hints"])
    assert vj["attempts"][0]["errors"] and vj["final"]["removed"] + vj["final"]["marked"] + vj["final"]["warnings"]


def test_v06_marks_instead_of_removing(cfg):
    res = check_recorded(cfg, "bad_assertion.json")
    d = degrade(pack_for(cfg, "bad_assertion.json"), res.output, res.errors)
    assert d.marked and not d.removed
    doc = render_markdown(cfg, pack_for(cfg, "bad_assertion.json"), d.output, RenderInfo(marked=d.marked))
    assert cfg.wording["fixed"]["unverified_mark"] in doc.split(f"## {REPORT_TITLE}")[0]


def test_drop_mode_replaces_sections(cfg):
    res = check_recorded(cfg, "bad_chain.json")
    d = degrade(pack_for(cfg, "bad_chain.json"), res.output, res.errors, on_fail="drop")
    s04 = next(s for s in d.output["sections"] if s["id"] == "S04")
    assert s04.get("_unavailable") and any("S04" in r for r in d.removed)


def test_fixtures_are_up_to_date():
    rook = json.loads((OUT / "rook_endgame.pack.json").read_text(encoding="utf-8"))
    for name, data in build(rook).items():
        assert recorded(name) == data, f"{name}: rigenera con python -m tests.fault_fixtures"
