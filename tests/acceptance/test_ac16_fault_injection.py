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


def test_notes_token_and_digits(cfg):
    # OQ-M1c-10: notes are copied into the report, so V03 applies to them too
    res = check_recorded(cfg, "bad_notes_token.json")
    lines = [e.line({}) for e in res.errors]
    assert any("nota 1 · «{{pct:root.draw}}»" in x for x in lines)
    assert any("digit: 1" in x for x in lines) and all(e.section is None for e in res.errors)


def test_notes_removed_in_both_modes(cfg):
    res = check_recorded(cfg, "bad_notes_token.json")
    pack = pack_for(cfg, "bad_notes_token.json")
    for mode in ("mark", "drop"):
        d = degrade(pack, res.output, res.errors, on_fail=mode)
        assert d.output["notes"] == [] and d.removed == ["nota 1 del modello (V03)"]
        doc = render_markdown(cfg, pack, d.output, RenderInfo(removed=d.removed))     # V11 passes
        assert "{{" not in doc and "nota 1 del modello (V03)" in doc


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


# -- M1c: full cycle (retry, then correction or degraded mode) -----------------------------

from chessanalyst.errors import ModelError  # noqa: E402
from chessanalyst.golden.packs import load_frozen_pack  # noqa: E402
from chessanalyst.llm.client import FakeLLM  # noqa: E402
from chessanalyst.llm.cycle import run_model  # noqa: E402


def _cycle(cfg, names):
    llm = FakeLLM([recorded(n) for n in names])
    return run_model(cfg, load_frozen_pack(cfg, "najdorf_w_1900"), llm), llm


@pytest.mark.parametrize("name", sorted(n for n in EXPECTED if n.startswith("bad_") and EXPECTED[n][0] != "rook_endgame"))
def test_retry_then_corrected(cfg, name):
    res, llm = _cycle(cfg, [name, "good_najdorf_1900.json"])
    assert res.retries == 1 and not res.degraded
    assert [bool(a["errors"]) for a in res.verification["attempts"]] == [True, False]
    second = llm.requests[1]["messages"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    assert second[1]["content"] == recorded(name)["content"]                 # the response as received
    result = second[2]["content"][0]
    assert result["type"] == "tool_result" and result["is_error"] is True
    assert result["tool_use_id"] == "toolu_recorded"
    assert result["content"].startswith("La consegna contiene errori. Correggi solo questi punti")
    code = sorted(EXPECTED[name][1])[0][:3]
    assert f"\n{code}" in result["content"]


def test_degraded_after_the_retries(cfg):
    res, llm = _cycle(cfg, ["bad_chain.json"] * 3)
    assert res.retries == 2 and res.degraded and len(llm.requests) == 3
    removed = res.verification["final"]["removed"]
    assert removed and all("V03" in r for r in removed)
    assert "Rimossi in modalità degradata: S04" in res.document and "Retry: 2" in res.document


def test_marked_after_the_retries(cfg):
    res, _ = _cycle(cfg, ["bad_assertion.json"] * 3)
    assert res.verification["final"]["marked"] and cfg.wording["fixed"]["unverified_mark"] in res.document


def test_word_budget_only_one_retry(cfg):
    import copy

    out = copy.deepcopy(recorded("good_najdorf_1900.json"))
    s10 = next(s for s in out["content"][0]["input"]["sections"] if s["id"] == "S10")
    s10["blocks"].append({"type": "p", "source": "theory", "text": " ".join(["parola"] * 200)})
    llm = FakeLLM([out, out, out])
    res = run_model(cfg, load_frozen_pack(cfg, "najdorf_w_1900"), llm)
    assert res.retries == 1 and len(llm.requests) == 2                       # V07(d) alone: at most one retry
    assert any("S10" in w for w in res.verification["final"]["warnings"])


def test_degraded_mode_uses_the_last_response_that_passed_v01(cfg):
    res, _ = _cycle(cfg, ["bad_chain.json", "max_tokens.json", "max_tokens.json"])
    assert res.degraded and len(res.raw) == 3
    assert "g4-g5" not in res.document


def test_invalid_tool_arguments_are_retried(cfg):
    # OQ-M2-9: a real DeepSeek answer with invalid JSON arguments ended the cycle without a retry (exit 5)
    res, llm = _cycle(cfg, ["bad_tool_arguments.json", "good_najdorf_1900.json"])
    assert res.retries == 1 and not res.degraded and len(llm.requests) == 2
    assert "V01" in llm.requests[1]["messages"][2]["content"][0]["content"]


def test_no_valid_response_is_exit_code_5(cfg):
    with pytest.raises(ModelError) as e:
        _cycle(cfg, ["max_tokens.json"] * 3)
    assert e.value.exit_code == 5
