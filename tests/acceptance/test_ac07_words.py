"""AC-07: word count of §9-bis.8 (Appendix G.5), V07(d) and the budgets of the three fewshots."""

from __future__ import annotations

import copy

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import verify_response
from chessanalyst.verify.wordcount import count_words
from tests.llm_helpers import fewshot


@pytest.mark.parametrize("text,n", [
    ("Il cavallo va in d5.", 5),
    ("l'alfiere {{m:Nb3@N4}} è **forte**", 5),
    ("{{pv:PV1:6}}", 1),
    ("Tre sistemi: Inglese, Classico.", 4),
])
def test_g5(cfg, text, n):
    assert count_words(text, cfg.verify["word"]) == n


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_fewshots_respect_budgets(cfg, anchor):
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    res = verify_response(cfg, pack, fewshot(anchor))
    tol = cfg.verify["word_tolerance"]
    for sid, w in res.words_by_section.items():
        assert abs(w["actual"] - w["budget"]) <= max(tol["relative"] * w["budget"], tol["absolute"]), sid
    assert not [e for e in res.errors if e.code == "V07"]


def test_overflow_is_flagged(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = copy.deepcopy(fewshot("1900"))
    s10 = next(s for s in out["sections"] if s["id"] == "S10")
    s10["blocks"].append({"type": "p", "source": "theory", "text": " ".join(["parola"] * 200)})
    res = verify_response(cfg, pack, out)
    d = [e for e in res.errors if e.code == "V07" and e.sub == "d"]
    assert [e.section for e in d] == ["S10"]
    assert not res.has_retry_errors()           # V07(d) alone: at most one retry, then a warning (§9.3)


def test_tolerance_absolute_minimum(cfg):
    from chessanalyst.verify.wordcount import tolerance

    assert tolerance(40, cfg.verify["word_tolerance"]) == 15      # max(25% of 40, 15)
    assert tolerance(200, cfg.verify["word_tolerance"]) == 50
