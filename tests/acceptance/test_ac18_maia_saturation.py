"""AC-18 (pack): saturated Elo → confidence low, p_up null, no improbable_error."""

from __future__ import annotations

import pytest

from tests.recorded import recorded_pack


@pytest.mark.parametrize("elo", [1900, 2400])
def test_saturated(cfg, root, elo):
    pack, _, _ = recorded_pack(cfg, root, "najdorf", "w", elo)
    m = pack["maia"]
    assert m["saturated"] and m["confidence"] == "low" and m["bucket_user"] == 10
    assert m["p_up_elo"] is None and m["p_up_bucket"] is None
    cands = pack["engine"]["candidates"]
    assert all(c["p_up"] is None for c in cands)
    assert all(c["category"] != "improbable_error" for c in cands)
    assert "maia_low_confidence_header" in pack["warnings"]
    assert pack["tables"]["T1"]["footnote"] == cfg.wording["fixed"]["maia_low_confidence_table"]
    assert any(c["header"].endswith("*") for c in pack["tables"]["T1"]["columns"])
    plan = {s["id"]: s for s in pack["section_plan"]}
    for sid in ("S06", "S08"):
        assert plan[sid]["maia_low_confidence"] == plan[sid]["required"]


def test_not_saturated_at_1500(cfg, root):
    pack, _, _ = recorded_pack(cfg, root, "najdorf", "w", 1500)
    m = pack["maia"]
    assert not m["saturated"] and m["confidence"] == "normal"
    assert m["p_up_elo"] == 2000 and m["p_up_bucket"] == "top"
    assert all(c["p_up"] is not None for c in pack["engine"]["candidates"])
    assert pack["tables"]["T1"]["footnote"] is None


# -- M1b: the document --------------------------------------------------------------------

@pytest.mark.parametrize("anchor", ["1900", "2400"])
def test_document_fixed_sentences(cfg, root, anchor):
    from chessanalyst.golden.packs import load_frozen_pack

    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    doc = (root / "examples" / "golden" / "rendered" / f"najdorf_w_{anchor}.md").read_text(encoding="utf-8")
    sentence = cfg.wording["fixed"]["maia_low_confidence"]
    for s in pack["section_plan"]:
        if s["id"] in ("S06", "S08") and s["required"]:
            assert f"## {s['title']}\n\n{sentence}" in doc, s["id"]
    t1 = doc.split("| Mossa |")[1]
    assert cfg.wording["fixed"]["maia_low_confidence_table"] in t1.split("\n\n")[1]
    assert cfg.wording["header"]["maia_low_confidence_header"] in doc.split("## ")[0]


def test_v11_detects_a_missing_fixed_sentence(cfg):
    from chessanalyst.golden.packs import load_frozen_pack
    from chessanalyst.render.markdown import RenderBug, check_document, render_markdown
    from tests.llm_helpers import fewshot

    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    doc = render_markdown(cfg, pack, fewshot("1900"))
    broken = doc.replace(cfg.wording["fixed"]["maia_low_confidence"], "", 1)
    with pytest.raises(RenderBug):
        check_document(cfg, pack, broken)
    with pytest.raises(RenderBug):
        check_document(cfg, pack, doc + "\n{{ev:C1}}")


def test_no_fixed_sentence_at_1500(cfg, root):
    doc = (root / "examples" / "golden" / "rendered" / "najdorf_w_1500.md").read_text(encoding="utf-8")
    assert cfg.wording["fixed"]["maia_low_confidence"] not in doc
