"""AC-08: no line beyond ``max_pv_plies`` (V05 on defective responses)."""

from __future__ import annotations

import copy

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import verify_response
from tests.llm_helpers import check_recorded, codes, fewshot


def test_pv_token_beyond_max(cfg):
    res = check_recorded(cfg, "bad_long_line.json")
    assert codes(res) == {"V05"}
    assert res.errors[0].section == "S07" and "{{pv:PV1:10}}" in res.errors[0].text


def test_line_block_beyond_max(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1500")              # max_pv_plies 4
    out = copy.deepcopy(fewshot("1500"))
    s07 = next(s for s in out["sections"] if s["id"] == "S07")
    s07["blocks"].append({"type": "line", "pv": "PV1", "plies": 5})
    s07["blocks"].append({"type": "line", "pv": "PV2", "plies": 4,
                          "caption": {"text": "Il piano con l'arrocco lungo: {{ev:C2}}.", "source": "engine"}})
    res = verify_response(cfg, pack, out)
    assert [(e.code, e.block) for e in res.errors if e.code == "V05"] == [("V05", len(s07["blocks"]) - 1)]


def test_all_lines_of_fewshots_within_limit(cfg):
    for anchor in ("1500", "1900", "2400"):
        res = verify_response(cfg, load_frozen_pack(cfg, f"najdorf_w_{anchor}"), fewshot(anchor))
        assert "V05" not in {e.code for e in res.errors}
