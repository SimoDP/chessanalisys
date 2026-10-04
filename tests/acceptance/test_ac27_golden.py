"""AC-27: each fewshot passes V01–V10 against its frozen pack and ``golden --render``
produces ``rendered/*.md`` identical to the versioned ones."""

from __future__ import annotations

import pytest

from chessanalyst.golden.render import check_fewshot, check_s07_alt, load_meta, render_info
from chessanalyst.render.markdown import render_markdown
from chessanalyst.verify.checker import error_lines


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_fewshot_passes_and_render_is_reproducible(cfg, root, anchor):
    pack, _, res = check_fewshot(cfg, anchor)
    assert res.errors == [], error_lines(res.errors, {})
    doc = render_markdown(cfg, pack, res.output, render_info(res, bool(load_meta(cfg, anchor).get("validated"))))
    versioned = (root / "examples" / "golden" / "rendered" / f"najdorf_w_{anchor}.md").read_text(encoding="utf-8")
    assert doc == versioned


def test_s07_alt_passes(cfg):
    res = check_s07_alt(cfg)
    assert res.errors == [], error_lines(res.errors, {})


def test_terms_file(root):
    terms = (root / "examples" / "golden" / "fewshot" / "_terms.txt").read_text(encoding="utf-8")
    for t in ("Najdorf|Najdorf", "Scheveningen|Scheveningen", "Dragon|Dragon", "attacco inglese|English Attack",
              "Pedone Avvelenato|Poisoned Pawn", "Sozin|Sozin"):
        assert t in terms


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_meta_lists_sections_to_review(cfg, anchor):
    meta = load_meta(cfg, anchor)
    assert meta["validated"] is False and meta["needs_review"]
    assert meta["anchor"] == anchor
