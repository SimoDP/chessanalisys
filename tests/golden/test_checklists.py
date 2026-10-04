"""Checklists of the non-Najdorf positions (§8-bis.6, M2) on the recorded answers of the real model."""

from __future__ import annotations

import re

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.pack.section_plan import fill_opp
from chessanalyst.render.report import REPORT_TITLE
from tests.checklists import body, checklist_ids, cited_moves, final_output, load_checklist


def test_two_non_najdorf_checklists_at_least():
    assert len(checklist_ids()) >= 2


@pytest.mark.parametrize("name", checklist_ids())
def test_checklist_matches_the_pack(cfg, name):
    cl = load_checklist(name)
    pack = load_frozen_pack(cfg, name)
    assert pack["profile"]["matrix_column"] == cl["matrix_column"]
    assert [s["id"] for s in pack["section_plan"] if s["required"]] == cl["sections"]
    assert len(cl["moves"]) == 3 and len(cl["typical_errors"]) == 2


@pytest.mark.parametrize("name", checklist_ids())
def test_checklist_on_the_model_answer(cfg, name):
    from tests.real_llm import replay

    cl = load_checklist(name)
    pack, res = replay(cfg, name)
    opp = cfg.wording["colors"]["b" if pack["user"]["color"] == "w" else "w"]
    anchor = pack["user"]["anchor"]
    titles = [h for h in re.findall(r"^## (.+)$", res.document, re.M) if h != REPORT_TITLE]
    assert titles == [fill_opp(cfg.section_titles[s][anchor], opp) for s in cl["sections"]]
    moves = cited_moves(cfg, pack, final_output(res.raw))
    missing = [m for m in cl["moves"] if m not in moves]
    for err in cl["typical_errors"]:
        if isinstance(err, str):                         # a move: cited by a token
            if err not in moves:
                missing.append(err)
        elif not re.search(err["pattern"], body(res.document), re.IGNORECASE):   # a concept: named in the text
            missing.append(err["concept"])
    assert not missing, (missing, sorted(moves))
