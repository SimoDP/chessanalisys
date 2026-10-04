"""AC-21 (pack): Najdorf after 6.Be3, user White, Black to move."""

from __future__ import annotations

import re

from tests.recorded import recorded_pack


def test_opponent_pack(cfg, root):
    pack, _, _ = recorded_pack(cfg, root, "najdorf_after_be3", "w", 1900)
    assert pack["position"]["user_to_move"] is False
    assert pack["recommendation"] is None and pack["engine"]["candidates"] == []
    replies = pack["engine"]["replies"]
    assert [r["id"] for r in replies] == [f"R{k}" for k in range(1, len(replies) + 1)]
    assert [r["p_opp"] for r in replies] == sorted((r["p_opp"] for r in replies), reverse=True)
    sel = cfg.thresholds.selection
    for r in replies:
        assert r["user_best"] and all(re.fullmatch(rf"{r['id']}\.u[123]", u["id"]) for u in r["user_best"])
        assert r["user_best"][0]["loss_cp"] == 0
    # the two best replies for Stockfish are always included
    root_node = pack["nodes"][0]
    best2 = {ln["uci"] for ln in root_node["multipv"][: sel.replies_best_sf]}
    assert best2 <= {r["uci"] for r in replies}
    phases = {p["phase"]: p["reason"] for p in pack["omitted_phases"]}
    assert phases["E2b"] == phases["E3"] == "opponent_to_move"
    assert {n["phase"] for n in pack["nodes"]} == {"E0", "E1", "R"}
    reasons = {o["id"]: o["reason"] for o in pack["omitted_sections"]}
    assert reasons["S03"] == reasons["S08"] == "opponent_to_move"
    plan = {s["id"]: s for s in pack["section_plan"]}
    assert plan["S07"]["title"] == "Risposte probabili del Bianco e come prepararsi".replace("Bianco", "Nero")
    assert plan["S07"]["must_cover"] == [r["id"] for r in replies]
    t1 = pack["tables"]["T1"]
    assert [c["key"] for c in t1["columns"]] == ["reply", "p_opp", "eval", "user_best", "prepare"]
    assert [row["id"] for row in t1["rows"]] == [r["id"] for r in replies]


# -- M1b: the document --------------------------------------------------------------------

def test_opponent_document(cfg, root):
    """Frozen AC-21 pack + the ``_s07_alt.json`` fragment: missing sections get the fixed
    text (degraded mode), S03/S08 are omitted with reason, S07 has the alternative title and T1."""
    import json

    from chessanalyst.golden.packs import load_frozen_pack
    from chessanalyst.render.markdown import RenderInfo, render_markdown
    from chessanalyst.render.report import REPORT_TITLE
    from chessanalyst.verify.checker import verify_response
    from chessanalyst.verify.degrade import degrade

    pack = load_frozen_pack(cfg, "najdorf_after_be3_w_1900")
    frag = json.loads((root / "examples" / "golden" / "fewshot" / "_s07_alt.json").read_text(encoding="utf-8"))
    res = verify_response(cfg, pack, frag)
    assert {e.code + (e.sub or "") for e in res.errors} == {"V07a"}       # only the missing sections
    d = degrade(pack, res.output, res.errors)
    doc = render_markdown(cfg, pack, d.output, RenderInfo(removed=d.removed))
    titles = re.findall(r"^## (.+)$", doc, re.M)
    assert "Risposte probabili del Nero e come prepararsi" in titles
    assert "Le tre cose da fare adesso" not in titles and "I sistemi che puoi scegliere" not in titles
    s07 = doc.split("## Risposte probabili del Nero e come prepararsi")[1].split("\n## ")[0]
    assert "| Risposta | Probabilità a 1900* | Valutazione | La tua risposta migliore | Come prepararsi |" in s07
    assert "| 6...e5 | 69% | +0,33 | 7.Nb3 (+0,34) |" in s07
    report = doc.split(f"## {REPORT_TITLE}")[1]
    assert "S03 (opponent_to_move)" in report and "S08 (opponent_to_move)" in report
    assert "E2b (opponent_to_move)" in report and "E3 (opponent_to_move)" in report
    s01 = doc.split("## Sintesi")[1].split("\n## ")[0]
    assert cfg.wording["fixed"]["section_unavailable"] in s01


# -- M1c: a recorded response of the real model --------------------------------------------

def test_real_model_opponent_mode(cfg):
    from chessanalyst.render.report import REPORT_TITLE
    from tests.real_llm import replay

    pack, res = replay(cfg, "najdorf_after_be3_w_1900")
    doc = res.document
    assert "## Risposte probabili del Nero e come prepararsi" in doc
    assert "## Le tre cose da fare adesso" not in doc and "## I sistemi che puoi scegliere" not in doc
    assert "| Risposta | Probabilità a 1900* |" in doc
    report = doc.split(f"## {REPORT_TITLE}")[1]
    assert "S03 (opponent_to_move)" in report and "S08 (opponent_to_move)" in report
