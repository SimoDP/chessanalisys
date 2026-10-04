"""AC-06: the document's sections match the SectionPlan; omissions and absorptions recorded with reason."""

from __future__ import annotations

import copy
import re

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.render.markdown import RenderInfo, render_markdown
from chessanalyst.render.report import REPORT_TITLE
from chessanalyst.verify.checker import verify_response
from chessanalyst.verify.degrade import degrade
from tests.llm_helpers import fewshot


def headings(doc: str) -> list[str]:
    return [h for h in re.findall(r"^## (.+)$", doc, re.M) if h != REPORT_TITLE]


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_document_follows_plan(cfg, anchor):
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    doc = render_markdown(cfg, pack, fewshot(anchor))
    assert headings(doc) == [s["title"] for s in pack["section_plan"] if s["required"]]
    report = doc.split(f"## {REPORT_TITLE}")[1]
    for o in pack["omitted_sections"]:
        assert f"{o['id']} ({o['reason']})" in report
    for s in pack["section_plan"]:
        if s["absorbed_into"]:
            assert f"{s['id']} in {s['absorbed_into']}" in report


def test_degraded_structure_is_repaired_and_reported(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = copy.deepcopy(fewshot("1900"))
    secs = {s["id"]: s for s in out["sections"]}
    out["sections"] = [secs["S03"], secs["S01"]] + [s for k, s in secs.items() if k not in ("S01", "S03", "S05")]
    out["sections"].append({"id": "S11", "blocks": [{"type": "p", "text": "Extra: {{ev:C1}}.", "source": "engine"}]})
    res = verify_response(cfg, pack, out)
    v07a = [e for e in res.errors if e.code == "V07" and e.sub == "a"]
    assert {e.detail for e in v07a} >= {"sezione mancante", "sezione non prevista"}
    d = degrade(pack, res.output, res.errors)
    assert [s["id"] for s in d.output["sections"]] == [s["id"] for s in pack["section_plan"] if s["required"]]
    assert any("S05 mancante" in r for r in d.removed) and any("S11 non prevista" in r for r in d.removed)
    doc = render_markdown(cfg, pack, d.output, RenderInfo(removed=d.removed, warnings=d.warnings))
    assert headings(doc) == [s["title"] for s in pack["section_plan"] if s["required"]]
    s05 = doc.split("## Cosa vuole ogni pezzo")[1].split("## ")[0]
    assert cfg.wording["fixed"]["section_unavailable"] in s05
    assert "S05 mancante" in doc.split(f"## {REPORT_TITLE}")[1]
