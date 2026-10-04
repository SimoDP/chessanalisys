"""Output schema (§9-bis.6, Appendix F) as used by V01."""

from __future__ import annotations

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import extract_output, verify_response

BASE = {"schema_version": "1", "notes": [], "sections": [{"id": "S01", "blocks": []}]}


def _with(block):
    return {**BASE, "sections": [{"id": "S01", "blocks": [block]}]}


@pytest.mark.parametrize("bad", [
    {**BASE, "schema_version": "2"},
    {**BASE, "extra": 1},
    {"schema_version": "1", "sections": []},
    BASE,                                                                     # a section without blocks
    _with({"type": "p", "text": "", "source": "engine"}),
    _with({"type": "p", "text": "x", "source": "opinion"}),
    _with({"type": "h1", "text": "x"}),
    _with({"type": "line", "pv": "P1", "plies": 2}),
    _with({"type": "line", "pv": "PV1", "plies": 0}),
    _with({"type": "table", "ref": "T9"}),
    _with({"type": "text_table", "columns": ["Solo"], "rows": [[{"text": "a", "source": "theory"}]]}),
    _with({"type": "text_table", "columns": ["A", "B"], "rows": [[{"text": "a", "source": "theory"}]]}),
    _with({"type": "p", "text": "x", "source": "feature",
           "assertions": [{"kind": "feature", "key": "k", "side": "w", "squares": ["z9"]}]}),
    _with({"type": "p", "text": "x", "source": "mixed",
           "assertions": [{"kind": "classification", "ref": "C1", "category": "brilliant"}]}),
])
def test_v01_schema(cfg, bad):
    res = verify_response(cfg, load_frozen_pack(cfg, "najdorf_w_1900"), bad)
    assert res.output is None and {e.code for e in res.errors} == {"V01"}


def test_tool_use_extraction():
    out = {"schema_version": "1", "sections": [], "notes": []}
    assert extract_output({"stop_reason": "tool_use", "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "name": "submit_analysis", "input": out}]}) == (out, [])
    _, errs = extract_output({"stop_reason": "end_turn", "content": [{"type": "text", "text": "ciao"}]})
    assert [e.code for e in errs] == ["V01"]
