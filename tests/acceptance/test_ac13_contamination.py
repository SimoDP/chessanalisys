"""AC-13 (M2): on at least two non-Najdorf fixtures no term of ``_terms.txt`` appears in the output
(recorded answers of the real model, ``pytest -m llm --record``)."""

from __future__ import annotations

import re

import pytest

from chessanalyst.verify.contamination import load_terms
from tests.llm_helpers import FEWSHOT_DIR

NON_NAJDORF = ("fried_liver_w_1500", "rook_endgame_w_1900", "lucena_w_1900")


@pytest.mark.parametrize("name", NON_NAJDORF)
def test_no_najdorf_term_in_the_output(cfg, name):
    from tests.real_llm import replay

    pack, res = replay(cfg, name)
    assert pack["position"]["epd"] != "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq -"
    for group in load_terms(FEWSHOT_DIR / "_terms.txt"):
        for term in group:
            assert not re.search(rf"(?<!\w){re.escape(term)}(?!\w)", res.document, re.IGNORECASE), (name, term)


def test_at_least_two_fixtures():
    assert len(NON_NAJDORF) >= 2
