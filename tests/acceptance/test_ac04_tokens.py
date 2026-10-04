"""AC-04: every token of the output is valid and resolved (V02 on valid and defective responses)."""

from __future__ import annotations

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.render.markdown import render_markdown
from chessanalyst.verify.checker import iter_units
from chessanalyst.verify.resolve import ResolveError, Resolver
from chessanalyst.verify.tokens import find_tokens
from tests.llm_helpers import check_recorded, codes, fewshot


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_all_tokens_of_valid_outputs_resolve(cfg, anchor):
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    r = Resolver(pack, cfg.wording)
    out = fewshot(anchor)
    tokens = [t for u in iter_units(out) for t in find_tokens(u.text)]
    assert tokens
    for t in tokens:
        r.resolve(t)                     # raises on any error
    doc = render_markdown(cfg, pack, out)
    assert "{{" not in doc and "}}" not in doc


EXAMPLES_1900 = {   # token → rendered text on the frozen 1900 pack
    "{{mv:C1}}": "6.f3", "{{mv:C1:bare}}": "f3", "{{m:Nb3@N8}}": "Nb3", "{{m:Nc6@N4}}": "...Nc6",
    "{{m:Nc6@N4:num}}": "6...Nc6", "{{m:Nb3@N8:num}}": "7.Nb3", "{{ev:C1}}": "+0,39", "{{ev:N4}}": "+0,35",
    "{{ev:Nc6@N4}}": "+0,54", "{{loss:C2}}": "0,05", "{{loss:Nc6@N4}}": "0,19", "{{pct:C1.p_user}}": "13%",
    "{{pct:root.draw}}": "95%", "{{pct:root.win}}": "5%", "{{pv:PV2:6}}": "6.Be3 e5 7.Nb3 Be6 8.h3 Nbd7",
    "{{plan:w:f3,Qd2,O-O-O@N4}}": "f3 → Qd2 → O-O-O", "{{plan:b:b5,b4@N4}}": "...b5 → ...b4",
    "{{diag:a7-g1}}": "a7–g1", "{{elo:user}}": "1900", "{{elo:opp:full}}": "1900 FIDE", "{{opening:eco}}": "B90",
    "{{opening:name}}": "Sicilian Defense: Najdorf Variation", "{{txt:opp}}": "il Nero", "{{txt:me}}": "il Bianco",
    "{{m:Nb3+@N8}}": "Nb3", "{{ev:e5@N7}}": "+1,07",
}


@pytest.mark.parametrize("token,text", sorted(EXAMPLES_1900.items()))
def test_token_rendering(cfg, token, text):
    assert Resolver(load_frozen_pack(cfg, "najdorf_w_1900"), cfg.wording).resolve(token).text == text


def test_opponent_tokens(cfg):
    r = Resolver(load_frozen_pack(cfg, "najdorf_after_be3_w_1900"), cfg.wording)
    assert r.resolve("{{mv:R1}}").text == "6...e5"
    assert r.resolve("{{mv:R1.u1}}").text == "7.Nb3"
    assert r.resolve("{{pct:R1.p_opp}}").text == "69%"
    assert r.resolve("{{loss:R2.u3}}").text == "0,40"
    with pytest.raises(ResolveError):
        r.resolve("{{mv:C1}}")          # no candidates with the opponent to move


@pytest.mark.parametrize("token", [
    "{{ev:C99}}", "{{pct:C1.p_up}}", "{{txt:p_up_group}}", "{{ev: C1}}", "{{ev:C1:x}}", "{{foo:C1}}",
    "{{pv:PV1:99}}", "{{ev:Nc6@N99}}", "{{ev:h5@N4}}", "{{pct:Nc6@N2}}", "{{sc:space.T}}", "{{ev:N17}}",
    "{{mv:R1}}", "{{loss:C1.p_user}}",
])
def test_v02_cases(cfg, token):
    with pytest.raises(ResolveError) as e:
        Resolver(load_frozen_pack(cfg, "najdorf_w_1900"), cfg.wording).resolve(token)
    assert e.value.code == "V02"


@pytest.mark.parametrize("name", ["bad_unknown_id.json", "bad_null_value.json"])
def test_v02_on_recorded_responses(cfg, name):
    assert codes(check_recorded(cfg, name)) == {"V02"}


def test_valid_recorded_response(cfg):
    assert check_recorded(cfg, "good_najdorf_1900.json").errors == []
