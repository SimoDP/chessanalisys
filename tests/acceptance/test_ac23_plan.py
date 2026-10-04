"""AC-23: token ``plan`` (§9-bis.3, D-26)."""

from __future__ import annotations

import copy

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import verify_response
from chessanalyst.verify.resolve import ResolveError, Resolver
from tests.llm_helpers import check_recorded, codes, fewshot


@pytest.fixture(scope="module")
def r(cfg):
    return Resolver(load_frozen_pack(cfg, "najdorf_w_1900"), cfg.wording)


@pytest.mark.parametrize("token,text", [
    ("{{plan:w:Be2,Be3,O-O@N1}}", "Be2 → Be3 → O-O"),           # side to move
    ("{{plan:w:f3,Qd2,O-O-O@N4}}", "f3 → Qd2 → O-O-O"),         # side not to move: null move first
    ("{{plan:b:b5,b4@N4}}", "...b5 → ...b4"),
    ("{{plan:b:e5,Be6,Be7,O-O@N3}}", "...e5 → ...Be6 → ...Be7 → ...O-O"),
    ("{{plan:w:Bb5+@N1}}", "Bb5+"),                              # check allowed as the last move
])
def test_valid(r, token, text):
    assert r.resolve(token).text == text


@pytest.mark.parametrize("token,why", [
    ("{{plan:w:Be3,Qd2,Qxd8@N1}}", "non è legale"),
    ("{{plan:w:Bb5,O-O@N1}}", "scacco"),                         # non-final check
    ("{{plan:w:a3,a4,b3,b4,c3,h3,h4@N1}}", "mosse"),             # beyond plan_max_moves (6)
    ("{{plan:b:Qh4@N1}}", "non è legale"),
])
def test_v04(r, token, why):
    with pytest.raises(ResolveError) as e:
        r.resolve(token)
    assert e.value.code == "V04" and why in e.value.message


def test_side_in_check_cannot_pass(cfg):
    pack = copy.deepcopy(load_frozen_pack(cfg, "najdorf_w_1900"))
    node = next(n for n in pack["nodes"] if n["id"] == "N1")
    node["fen"] = "rnbqkbnr/ppp2ppp/3p4/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 1 3"   # in_check.fen
    with pytest.raises(ResolveError) as e:
        Resolver(pack, cfg.wording).resolve("{{plan:w:O-O@N1}}")
    assert e.value.code == "V04" and "sotto scacco" in e.value.message


def test_plan_in_engine_paragraph_is_v10(cfg):
    assert codes(check_recorded(cfg, "bad_plan_engine.json")) == {"V10"}


def test_plan_allowed_in_theory_and_mixed(cfg):
    out = fewshot("1900")
    res = verify_response(cfg, load_frozen_pack(cfg, "najdorf_w_1900"), out)
    assert res.errors == []
    assert any("{{plan:" in u["text"] for s in out["sections"] for b in s["blocks"]
               for u in ([b] if b["type"] == "p" else b.get("items", [])) if u["source"] in ("theory", "mixed"))
