"""Verification of the M3 tokens and assertions (§9-bis.2, §9-bis.5): sc, L<n> in pv/ev/loss and in line blocks,
category_advice; and the reduced view of categories and lines (§6.1, O-5)."""

from __future__ import annotations

import json

import pytest

from chessanalyst.pack.llm_view import llm_view
from chessanalyst.verify.assertions import check_assertion
from chessanalyst.verify.checker import Checker, Unit
from chessanalyst.verify.resolve import ResolveError, Resolver


@pytest.fixture(scope="module")
def pack(root):
    return json.loads((root / "fixtures" / "packs" / "fried_liver_w_1500.pack.json").read_text(encoding="utf-8"))


def test_sc_tokens(cfg, pack):
    r = Resolver(pack, cfg.wording)
    td = next(c for c in pack["categories"] if c["id"] == "threats_dynamics")
    assert r.resolve("{{sc:threats_dynamics.T}}").text == str(td["T"]["w"])
    assert r.resolve("{{sc:threats_dynamics.R}}").text == str(td["R"])
    with pytest.raises(ResolveError) as e:
        r.resolve("{{sc:tactics.T}}")
    assert e.value.code == "V02"


def test_line_tokens(cfg, pack):
    r = Resolver(pack, cfg.wording)
    ln = pack["filtered_lines"][2]                     # L3: ...Qxg5 after a pass (threat)
    assert ln["id"] == "L3" and ln["plies"][0] == "Qxg5"
    assert r.resolve("{{pv:L3:2}}").text == "6...Qxg5 7.Bxd5"
    assert r.resolve("{{ev:L3}}").value == (ln["eval_end_user_cp"], ln["mate_user"])
    assert r.resolve("{{loss:L3}}").value == ln["impact_cp"]
    for bad in ("{{pv:L3:99}}", "{{pv:L9:2}}", "{{ev:L9}}"):
        with pytest.raises(ResolveError) as e:
            r.resolve(bad)
        assert e.value.code == "V02"


def test_category_advice(cfg, pack):
    r = Resolver(pack, cfg.wording)
    td = next(c for c in pack["categories"] if c["id"] == "threats_dynamics")
    ok = {"kind": "category_advice", "id": "threats_dynamics", "advice": td["advice"]}
    assert check_assertion(ok, pack, r, cfg.wording) is None
    assert "è «critical»" in check_assertion(dict(ok, advice="no_worry"), pack, r, cfg.wording)
    assert "inesistente" in check_assertion(dict(ok, id="tactics"), pack, r, cfg.wording)


def test_checker_on_m3_units(cfg, pack):
    ch = Checker(cfg, pack)
    unit = Unit("S09", 1, None, "Se lasci il cavallo, {{pv:L3:12}} costa {{loss:L3}}.", "engine", [])
    codes = {e.code for e in ch._check_unit(unit, set())}
    assert codes == {"V05"}                              # 12 half-moves beyond max_pv_plies (1500)
    cites: set[str] = set()
    unit = Unit("S02", 1, None, "Tranquillità {{sc:threats_dynamics.T}}.", "engine", [])
    assert {e.code for e in ch._check_unit(unit, cites)} == {"V10"}      # sc not in an engine block
    assert "threats_dynamics" in cites
    unit = Unit("S02", 1, None, "Tranquillità {{sc:threats_dynamics.T}}.", "mixed",
                [{"kind": "category_advice", "id": "threats_dynamics", "advice": "critical"}])
    assert ch._check_unit(unit, set()) == []


def test_line_block_on_a_filtered_line(cfg, pack):
    ch = Checker(cfg, pack)
    out = {"sections": [{"id": "S09", "blocks": [{"type": "line", "pv": "L3", "plies": 2},
                                                 {"type": "line", "pv": "L7", "plies": 2}]}]}
    errs = ch._check_lines(out)
    assert [(e.code, e.block) for e in errs] == [("V02", 2)]


def test_view_of_categories_and_lines(cfg, pack):
    v = llm_view(pack, cfg.default.llm.view)
    me = pack["user"]["color"]
    for c, full in zip(v["categories"], pack["categories"]):
        assert c == {"id": full["id"], "T": full["T"][me], "R": full["R"], "balance": full["balance"],
                     "advice": full["advice"], "confidence": full["confidence"]}     # no T of the opponent (O-5)
    for ln, full in zip(v["filtered_lines"], pack["filtered_lines"]):
        assert "attacker_moves" not in ln and "p_walk" not in ln and ln["id"] == full["id"]
        assert len(ln["plies"]) <= cfg.default.llm.view.pv_plies
