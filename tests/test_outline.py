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
                r.resolve(tok)                                               # every offered token resolves
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


def test_one_call_per_section(cfg):
    kcfg = _kp_cfg(cfg, calls="per_section", max_parallel=1)
    pack = _pack(cfg, "rook_checks_b_1700")
    texts = {
        "S01": ("mixed", "La partita è equilibrata ({{ev:N1}}): il finale è patta.",
                [{"kind": "eval_band", "ref": "N1", "band": "equal"}]),
        "S07": ("mixed", "Contro {{mv:R1}} rispondi {{mv:R1.u1}}; contro {{mv:R2}} rispondi {{mv:R2.u1}}.", []),
        "S05": ("theory", "Spingi il pedone passato con calma e tieni il re vicino.", []),
        "S10": ("theory", "Prima di muovere controlla gli scacchi dell'avversario.", [])}

    class BySection(FakeLLM):                  # the answer of the section the message asks for
        def create(self, **kw):
            super().create(**kw)
            sid = re.search(r'<punto id="(S\d+)"', kw["messages"][0]["content"]).group(1)
            return _sections({sid: texts[sid]})

    client = BySection([{}] * 20)
    res = run_model(kcfg, pack, client)
    first = [r["messages"][0]["content"] for r in client.requests]
    assert all(m.count("<punto ") == 1 for m in first)
    assert {re.search(r'<punto id="(S\d+)"', m).group(1) for m in first} == set(texts)
    assert [s["id"] for s in res.output["sections"]] == list(texts)
