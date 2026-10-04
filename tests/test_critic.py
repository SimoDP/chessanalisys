"""Optional critic (§10.2, M4, OQ-M4-3): marks the flagged blocks, never removes them; failures are warnings."""

from __future__ import annotations

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.client import FakeLLM
from chessanalyst.llm.critic import CRITIC_TOOL, critic_message
from chessanalyst.llm.cycle import run_model
from tests.llm_helpers import recorded


def review(findings):
    return {"stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "t", "name": CRITIC_TOOL, "input": {"findings": findings}}]}


@pytest.fixture
def ccfg(cfg):
    return cfg.model_copy(update={"default": cfg.default.model_copy(
        update={"llm": cfg.default.llm.model_copy(update={"critic": True})})})


def test_critic_marks_blocks(ccfg):
    pack = load_frozen_pack(ccfg, "najdorf_w_1900")
    llm = FakeLLM([recorded("good_najdorf_1900.json"),
                   review([{"section": "S01", "block": 1, "kind": "data", "explanation": "esempio"},
                           {"section": "S13", "block": 1, "kind": "internal", "explanation": "x"}])])
    res = run_model(ccfg, pack, llm)
    first = res.document.split("## Sintesi", 1)[1].split("\n\n")[1]
    assert first.endswith("⚠ non verificato")
    assert res.verification["critic"]["marked"] == ["S01 · blocco 1 (critico)"]     # S13 is not in the analysis
    assert "il critico ha controllato frasi, dati e asserzioni: 2 segnalazioni" in res.document
    assert "esempio" not in res.document                     # explanations stay in verification.json
    assert len(res.raw) == 2 and len(llm.requests) == 2
    msg = llm.requests[1]["messages"][0]["content"]
    assert "S01 · blocco 1:" in msg and "{{" not in msg.split("<analisi>")[1]        # tokens resolved


def test_critic_failure_is_a_warning(ccfg):
    pack = load_frozen_pack(ccfg, "najdorf_w_1900")
    res = run_model(ccfg, pack, FakeLLM([recorded("good_najdorf_1900.json")]))     # no response left
    assert res.verification["critic"]["error"] and "la corrispondenza tra frase e asserzione non è controllata" in res.document
    bad = {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "t", "name": CRITIC_TOOL,
                                                    "input": {"findings": [{"section": "S01"}]}}]}
    res = run_model(ccfg, pack, FakeLLM([recorded("good_najdorf_1900.json"), bad]))
    assert res.verification["critic"]["error"] == "risposta del critico non valida"


def test_critic_off_by_default(cfg):
    assert cfg.default.llm.critic is False
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    res = run_model(cfg, pack, FakeLLM([recorded("good_najdorf_1900.json")]))
    assert "critic" not in res.verification


def test_critic_message_has_assertions(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = recorded("good_najdorf_1900.json")["content"][0]["input"]
    msg = critic_message(cfg, pack, out)
    assert "asserzioni:" in msg and "<pacchetto>" in msg and "S02 · blocco 1:" in msg


def test_real_critic_response_replays(cfg, root):
    """A real response of the development model (DeepSeek, D-67): it uses the tool correctly but flags blocks
    that it then calls consistent (M4_REPORT): the marks are applied as they come."""
    import json

    from chessanalyst.llm.critic import run_critic

    data = json.loads((root / "fixtures" / "recorded" / "llm" / "real_critic_najdorf_w_1900.json").read_text(encoding="utf-8"))
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = json.loads((root / "examples" / "golden" / "fewshot" / "najdorf_w_1900.json").read_text(encoding="utf-8"))
    marked_out, res = run_critic(cfg, pack, out, FakeLLM([data["response"]]))
    assert res.error is None and len(res.findings) == 5 and len(res.marked) == 5
    assert marked_out["sections"] != out["sections"]
