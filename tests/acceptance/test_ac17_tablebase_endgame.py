"""AC-17 (M2): endgame with tablebase (Lucena, 5 pieces): S12 with the exact result, no numeric
evaluation in the text (OQ-M2-4)."""

from __future__ import annotations

import re

from chessanalyst.golden.packs import load_frozen_pack
from tests.checklists import body

NAME = "lucena_w_1900"
# an evaluation in pawns (``+0,37``, ``99,99``) or a mate count (``#3``, ``matto in 3``); Maia-2 percentages
# are probabilities, not evaluations
NUMERIC_EVAL = re.compile(r"[+-]?\d+,\d\d|-?#\d|matto in \d")


def test_pack_has_the_exact_result(cfg):
    pack = load_frozen_pack(cfg, NAME)
    assert pack["profile"]["tablebase"] is True and pack["profile"]["matrix_column"] == 4
    assert pack["tablebase"] == {"wdl": 2, "dtz": pack["tablebase"]["dtz"], "result_text_key": "win"}
    assert pack["tablebase"]["dtz"] > 0
    plan = {s["id"]: s for s in pack["section_plan"]}
    assert plan["S12"]["required"] and plan["S12"]["must_cover"] == ["N1"]
    assert not plan["S08"]["required"] and not plan["S03"]["required"]


def test_tables_without_numbers(cfg):
    pack = load_frozen_pack(cfg, NAME)
    t1 = pack["tables"]["T1"]
    evals = {r["cells"]["eval"] for r in t1["rows"]}
    assert evals <= set(cfg.wording["tablebase"]["table"].values())


def test_s12_with_the_exact_result_and_no_numeric_evaluation(cfg):
    from tests.real_llm import replay

    pack, res = replay(cfg, NAME)
    text = body(res.document)
    s12_title = cfg.section_titles["S12"][pack["user"]["anchor"]]
    assert f"## {s12_title}" in text
    s12 = text.split(f"## {s12_title}")[1].split("\n## ")[0]
    assert cfg.wording["tablebase"]["results"][pack["tablebase"]["result_text_key"]] in s12
    # no evaluation in pawns nor mate count anywhere in the sections (text and tables)
    sections = text.split("\n## ", 1)[1]
    assert not NUMERIC_EVAL.search(sections), NUMERIC_EVAL.search(sections)
