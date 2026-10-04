"""Recording of real model responses (AC-10 and AC-21 «modello»): ``pytest -m llm --record``.

Needs ``ANTHROPIC_API_KEY``. For each pack the full cycle (prompt, verification
retries) runs against the real API and every response is saved in
``fixtures/recorded/llm/real_<pack>.json``; the acceptance tests replay them
with ``FakeLLM``. Only the reduced view of the frozen packs is sent (§11.5).
"""

from __future__ import annotations

import json
import os

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.client import AnthropicClient
from chessanalyst.llm.cycle import run_model
from tests.fault_fixtures import OUT

REAL_PACKS = ("najdorf_w_1500", "najdorf_w_1900", "najdorf_after_be3_w_1900")


def real_fixture(name: str):
    return OUT / f"real_{name}.json"


@pytest.mark.llm
@pytest.mark.parametrize("name", REAL_PACKS)
def test_record_real_responses(cfg, request, name):
    if not request.config.getoption("--record"):
        pytest.skip("registrazione solo con --record")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY assente")
    client = AnthropicClient(cfg)
    raw: list[dict] = []
    try:
        res = run_model(cfg, load_frozen_pack(cfg, name), client, raw=raw)
    finally:
        if raw:
            data = {"model": client.model, "responses": raw}
            real_fixture(name).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    assert res.document
