"""Usefulness test, phase 2: the sentence on the material of the verdict is written by the code (``lead_text``);
the model's text in that section may not count the material (V12). In the test the model wrote «l'avversario ha
un pedone in più» with the user a pawn up."""

from __future__ import annotations

from chessanalyst import bench
from chessanalyst.llm.prompt_kp import build_user_message_kp
from chessanalyst.plan.outline import material_lead, outline_pack
from chessanalyst.render.markdown import render_markdown
from chessanalyst.verify.checker import Checker


def _outlined(cfg, name="e4_wins_w_1700"):
    return outline_pack(cfg, bench.load_pack(cfg, bench.load_spec(cfg, name)))


def _verdict(pack):
    return next(s for s in pack["section_plan"] if s["required"] and s["id"] == "S01")


def test_lead_text_from_the_balance(cfg):
    kp = {"type": "verdict", "facts": {"material_balance_user": 1}}
    assert material_lead(cfg, kp) == "Hai un pedone in più."
    assert material_lead(cfg, dict(kp, facts={"material_balance_user": -3})) == "Hai tre pedoni in meno."
    assert material_lead(cfg, dict(kp, facts={"material_balance_user": 0})) == "Il materiale è pari."
    assert material_lead(cfg, {"type": "plan", "facts": {}}) is None


def test_lead_is_in_the_plan_and_not_in_the_prompt(cfg):
    pack = _outlined(cfg)
    assert _verdict(pack)["lead_text"]
    assert all(s.get("lead_text") is None for s in pack["section_plan"] if s["id"] != "S01")
    msg = build_user_message_kp(cfg, pack)
    assert '"material"' not in msg and "material_balance_user" not in msg


def _response(text):
    return {"content": [{"type": "tool_use", "name": "submit_analysis", "input": {
        "schema_version": "1", "notes": [], "sections": [
            {"id": "S01", "blocks": [{"type": "p", "source": "mixed", "text": text, "assertions": []}]}]}}]}


def test_model_may_not_count_the_material(cfg):
    pack = _outlined(cfg)
    ch = Checker(cfg, pack, words_floor=False)
    bad = ch.check(_response("Stai meglio ({{ev:N1}}): l'avversario ha un pedone in più ma è passivo."))
    assert any(e.code == "V12" and "pedone in più" in e.text for e in bad.errors)
    ok = ch.check(_response("Stai meglio ({{ev:N1}}): il vantaggio viene dall'attività dei pezzi."))
    assert not any(e.code == "V12" for e in ok.errors)


def test_render_closes_the_first_paragraph_with_the_lead(cfg):
    pack = _outlined(cfg)
    lead = _verdict(pack)["lead_text"]
    out = {"schema_version": "1", "notes": [], "sections": [
        {"id": "S01", "blocks": [{"type": "p", "source": "mixed", "text": "Stai meglio ({{ev:N1}}).",
                                  "assertions": []}]}]}
    doc = render_markdown(cfg, pack, out)
    assert f"({_fmt_n1(cfg, pack)}). {lead}" in doc


def _fmt_n1(cfg, pack):
    from chessanalyst.verify.resolve import Resolver
    return Resolver(pack, cfg.wording).resolve("{{ev:N1}}").text
