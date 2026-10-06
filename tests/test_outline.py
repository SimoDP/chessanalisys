"""D-72: the document of the key points (plan/outline.py, llm/prompt_kp.py, V13). Frozen bench packs, FakeLLM."""

from __future__ import annotations

import re

from chessanalyst import bench
from chessanalyst.llm.client import FakeLLM
from chessanalyst.llm.cycle import run_model
from chessanalyst.llm.fewshot import example_for
from chessanalyst.llm.prompt import SYSTEM_PROMPT, build_user_message
from chessanalyst.llm.prompt_kp import SYSTEM_PROMPT_KP, build_user_message_kp
from chessanalyst.plan.outline import outline_pack
from chessanalyst.verify.checker import Checker
from chessanalyst.verify.degrade import degrade
from chessanalyst.verify.resolve import Resolver

TOKEN = re.compile(r"\{\{[^}]+\}\}")


def _pack(cfg, name):
    return bench.load_pack(cfg, bench.load_spec(cfg, name))


def _kp_cfg(cfg, **update):
    llm = cfg.default.llm.model_copy(update={"document": "keypoints", **update})
    return cfg.model_copy(update={"default": cfg.default.model_copy(update={"llm": llm})})


def test_sections_follow_the_key_points(cfg):
    pack = _pack(cfg, "e4_wins_w_1700")
    out = outline_pack(cfg, pack)
    assert outline_pack(cfg, out) is out                                     # idempotent
    req = [s for s in out["section_plan"] if s["required"]]
    assert [s["id"] for s in req] == [k["section"] for k in out["key_points"]]
    assert [s["key_point"] for s in req] == [k["id"] for k in out["key_points"]]
    assert all(s["omitted"] == "keypoints" for s in out["section_plan"] if not s["required"])
    likely = next(s for s in req if s["id"] == "S07")                        # opponent to move: T1 with the replies
    assert likely["auto_tables"] == ["T1"] and likely["tables"] == []
    assert sum(len(s["auto_tables"]) for s in req) == 1
    assert "R5" not in next(s for s in req if s["id"] == "S01")["cites_allowed"]   # told in «Il pericolo»
    kpc = cfg.thresholds.keypoints
    assert all(kpc.words_min <= s["word_budget"] <= kpc.words_max for s in req)
    assert pack["section_plan"] != out["section_plan"]                       # the pack itself is unchanged


def test_prompt_sends_only_the_facts_as_tokens(cfg):
    for name in bench.bench_cfg(cfg)["positions"]:
        pack = _pack(cfg, name)
        old = len(SYSTEM_PROMPT) + len(build_user_message(cfg, pack, example_for(cfg, pack)))
        out = outline_pack(cfg, pack)
        msg = build_user_message_kp(cfg, out)
        assert len(SYSTEM_PROMPT_KP) + len(msg) < old / 3, name
        assert "eval_user_cp" not in msg and '"p_opp"' not in msg and '"san"' not in msg
        plan = {s["id"]: s for s in out["section_plan"]}
        r = Resolver(out, cfg.wording)
        for sid, body in re.findall(r'<punto id="(S\d+)"(.*?)</punto>', msg, re.S):
            for tok in TOKEN.findall(body):
                r.resolve(tok)
                if tok.startswith("{{diag:"):                                   # squares, not a fact of the pack
                    continue                                               # every offered token resolves
                ref = tok[2:-2].split(":")[1]
                ref = ref if ref in plan[sid]["cites_allowed"] else ref.rsplit(".", 1)[0]
                assert ref in plan[sid]["cites_allowed"], (name, sid, tok)


def _sections(text_by_section: dict[str, str]) -> dict:
    return {"schema_version": "1", "notes": [], "sections": [
        {"id": sid, "blocks": [{"type": "p", "source": src, "text": text, "assertions": a}]}
        for sid, (src, text, a) in text_by_section.items()]}


def test_v13_a_fact_of_another_section(cfg):
    out = outline_pack(cfg, _pack(cfg, "rook_checks_b_1700"))
    resp = _sections({"S01": ("mixed", "La partita è equilibrata ({{ev:N1}}) e dopo {{mv:R1}} resta patta.",
                              [{"kind": "eval_band", "ref": "N1", "band": "equal"}])})
    res = Checker(cfg, out).check(resp)
    v13 = [e for e in res.errors if e.code == "V13"]
    assert v13 and v13[0].section == "S01" and "R1" in v13[0].text
    d = degrade(out, res.output, res.errors, "mark")
    assert any("V13" in x for x in d.removed)


def test_cycle_with_the_key_points_document(cfg):
    kcfg = _kp_cfg(cfg)
    pack = _pack(cfg, "rook_checks_b_1700")
    good = _sections({
        "S01": ("mixed", "La partita è equilibrata ({{ev:N1}}): il finale è patta.",
                [{"kind": "eval_band", "ref": "N1", "band": "equal"}]),
        "S07": ("mixed", "L'avversario gioca spesso {{mv:R1}} ({{pct:R1.p_opp}}) e tu rispondi {{mv:R1.u1}}; "
                         "contro {{mv:R2}} ({{pct:R2.p_opp}}) rispondi {{mv:R2.u1}}.",
                [{"kind": "maia_band", "ref": "R1.p_opp", "band": "frequent"}]),
        "S05": ("theory", "Spingi il pedone passato con calma e tieni il re vicino.", []),
        "S10": ("theory", "Prima di muovere controlla gli scacchi dell'avversario.", [])})
    client = FakeLLM([good, good])
    res = run_model(kcfg, pack, client)
    assert len(client.requests) <= 2
    req = client.requests[0]
    assert req["system"][0]["text"] == SYSTEM_PROMPT_KP
    assert "<pacchetto>" not in req["messages"][0]["content"][0]["text"]
    errs = [e for a in res.verification["attempts"] for e in a["errors"]]
    assert not [e for e in errs if e["code"] not in ("V07(d)",)], errs
    titles = re.findall(r"^## (.+)$", res.document, re.M)
    assert titles[:4] == ["Verdetto", "Cosa giocherà il Bianco e come rispondere", "Il piano", "Come ragionare"]
    assert res.info.document == "keypoints"
    from chessanalyst.plan.outline import document_pack
    from chessanalyst.render.html import render_html_part

    part = render_html_part(kcfg, document_pack(kcfg, pack, res.info.document), res.output, res.info)
    assert "Come ragionare" in part.body


def test_feature_assertions_on_facts_are_pruned(cfg):
    from chessanalyst.llm.prompt_kp import prune_assertions

    pack = _pack(cfg, "knight_a4_w_1700")
    good = {"kind": "feature", "key": "isolated_pawn", "side": "b", "squares": ["c5"]}
    resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "id": "t", "input": {"sections": [
        {"id": "S05", "blocks": [{"type": "p", "text": "x", "source": "mixed", "assertions": [
            good, {"kind": "feature", "key": "pinned", "side": "b", "squares": ["c5"]}]}]}]}}]}
    assert prune_assertions(pack, resp) == 1
    assert resp["content"][0]["input"]["sections"][0]["blocks"][0]["assertions"] == [good]
    # a malformed answer (seen with gemini-2.5-flash-lite: a null section) is left to V01
    for bad in ([None], [{"id": "S01", "blocks": [None, {"items": "x"}]}], "x"):
        resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "id": "t", "input": {"sections": bad}}]}
        assert prune_assertions(pack, resp) == 0


def test_default_is_keypoints(root):
    """D-72: the document of the key points is the default of the app (the suite runs with sections)."""
    import yaml

    raw = yaml.safe_load((root / "config/default.yaml").read_text(encoding="utf-8"))
    assert raw["llm"]["document"] == "keypoints"


# --- D-74: the word budget is enforced by the code -------------------------------------------------


def _rook_sections(s10: str) -> dict:
    return _sections({
        "S01": ("mixed", "La partita è equilibrata ({{ev:N1}}): il finale è patta.",
                [{"kind": "eval_band", "ref": "N1", "band": "equal"}]),
        "S07": ("mixed", "L'avversario gioca spesso {{mv:R1}} ({{pct:R1.p_opp}}) e tu rispondi {{mv:R1.u1}}; "
                         "contro {{mv:R2}} ({{pct:R2.p_opp}}) rispondi {{mv:R2.u1}}.",
                [{"kind": "maia_band", "ref": "R1.p_opp", "band": "frequent"}]),
        "S05": ("theory", "Spingi il pedone passato con calma e tieni il re vicino.", []),
        "S10": ("theory", s10, [])})


def _run_once(cfg, response):
    kcfg = _kp_cfg(cfg)
    client = FakeLLM([response] * (kcfg.default.llm.max_retries + 1))
    res = run_model(kcfg, _pack(cfg, "rook_checks_b_1700"), client)
    return res, client


def test_long_section_is_cut_by_the_code(cfg):
    long = " ".join(["Prima di muovere controlla con calma gli scacchi che restano all'avversario."] * 30)
    res, client = _run_once(cfg, _rook_sections(long))
    assert "S10" in res.verification["trimmed_sections"]
    first = res.verification["attempts"][0]["errors"]
    assert not [e for e in first if e["code"] == "V07(d)"], first        # cut before any retry
    w = res.verification["words_by_section"]["S10"]
    assert w["actual"] <= w["budget"] + max(0.25 * w["budget"], 15)


def test_a_cut_never_drops_a_must_cover_id(cfg):
    """Fault injection: a section too long only with the sentences of must_cover is left to the retry."""
    from chessanalyst.verify.trim import trim_response

    out = outline_pack(cfg, _pack(cfg, "rook_checks_b_1700"))
    plan = {s["id"]: s for s in out["section_plan"]}
    s07 = plan["S07"]
    cited = " ".join(f"Dopo {{{{mv:{x}}}}} la posizione resta tranquilla e il re torna al centro con calma."
                     for x in s07["must_cover"]) * 1
    long = " ".join([cited] * 12)
    resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "id": "t", "input": {"sections": [
        {"id": "S07", "blocks": [{"type": "p", "source": "mixed", "text": long, "assertions": []}]}]}}]}
    assert trim_response(resp, plan, {"S07"}, cfg.verify["word"], lambda b: 0) is None


def test_a_short_section_is_accepted(cfg):
    res, _ = _run_once(cfg, _rook_sections("Controlla gli scacchi."))
    errs = [e for a in res.verification["attempts"] for e in a["errors"]]
    assert not errs, errs
