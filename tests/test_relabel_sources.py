"""D-71: a wrong ``source`` label between engine, maia and feature is fixed by the checker (recorded in
``relabeled``); theory with data and plan outside theory/mixed stay errors (AC-16, AC-23)."""

from __future__ import annotations

import copy
import json

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import verify_response


def _with_s01_block(root, block):
    out = json.loads((root / "examples/golden/fewshot/najdorf_w_1900.json").read_text(encoding="utf-8"))
    out = copy.deepcopy(out)
    s01 = next(s for s in out["sections"] if s["id"] == "S01")
    s01["blocks"].append(block)
    return out


def test_engine_with_maia_becomes_mixed(cfg, root):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = _with_s01_block(root, {"type": "p", "source": "engine",
                                 "text": "Il motore dà {{ev:C1}} e il {{pct:C1.p_user}} la gioca."})
    res = verify_response(cfg, pack, out)
    assert not [e for e in res.errors if e.code == "V10"]
    assert len(res.relabeled) == 1 and res.relabeled[0].endswith("engine → mixed")


def test_no_data_in_a_section_without_theory_stays_v10(cfg, root):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = _with_s01_block(root, {"type": "p", "source": "engine", "text": "In pratica conta il piano."})
    res = verify_response(cfg, pack, out)          # S01 does not allow theory: nothing to relabel to
    assert any(e.code == "V10" for e in res.errors) and not res.relabeled


def test_plan_in_engine_is_not_relabeled(cfg, root):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = _with_s01_block(root, {"type": "p", "source": "engine",
                                 "text": "Con {{ev:C1}} il piano è {{plan:w:Be3,Qd2@N3}}."})
    res = verify_response(cfg, pack, out)
    assert any(e.code == "V10" for e in res.errors) and not res.relabeled
