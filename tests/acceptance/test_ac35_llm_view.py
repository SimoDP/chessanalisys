"""AC-35: reduced view of the pack (§6.1): no ``citable: false`` node, no tables, at most 5 lines per node."""

from __future__ import annotations

import json

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.pack.llm_view import llm_view, llm_view_json


@pytest.mark.parametrize("name", ["najdorf_w_1500", "najdorf_w_1900", "najdorf_w_2400", "najdorf_after_be3_w_1900"])
def test_view(cfg, name):
    pack = load_frozen_pack(cfg, name)
    view = cfg.default.llm.view
    v = llm_view(pack, view)
    assert "tables" not in v and "omitted_nodes" not in v and "config_hash" not in v
    assert v["nodes"] and all(n["citable"] for n in v["nodes"])
    assert {n["id"] for n in v["nodes"]} == {n["id"] for n in pack["nodes"] if n["citable"]}
    for n in v["nodes"]:
        assert len(n["multipv"]) <= view.multipv_lines and all(len(ln["pv"]) <= view.pv_plies for ln in n["multipv"])
        assert n["maia"] is None or len(n["maia"]["policy"]) <= view.policy_moves
    assert v["section_plan"] == pack["section_plan"] and v["engine"] == pack["engine"]
    assert json.loads(llm_view_json(pack, view)) == v


def test_view_does_not_modify_the_pack(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    before = json.dumps(pack, sort_keys=True)
    llm_view(pack, cfg.default.llm.view)
    assert json.dumps(pack, sort_keys=True) == before
