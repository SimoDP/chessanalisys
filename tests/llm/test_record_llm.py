"""Recording of real model responses (AC-10, AC-21 «modello»; from M2 also AC-13, AC-17 and the checklists): ``pytest -m llm --record``.

Needs the key of ``llm.provider`` (``OPENROUTER_API_KEY`` by default, D-64). For each pack the full cycle (prompt, verification
retries) runs against the real API and every response is saved in
``fixtures/recorded/llm/real_<pack>.json``; the acceptance tests replay them
with ``FakeLLM``. Only the reduced view of the frozen packs is sent (§11.5).
"""

from __future__ import annotations

import json
import os

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.client import API_KEY_ENV, make_client
from chessanalyst.llm.cycle import run_model
from tests.fault_fixtures import OUT

REAL_PACKS = ("najdorf_w_1500", "najdorf_w_1900", "najdorf_w_2400", "najdorf_after_be3_w_1900",
              # M2: non-Najdorf positions with a checklist (AC-13, AC-17, §8-bis.6)
              "fried_liver_w_1500", "rook_endgame_w_1900", "lucena_w_1900")


def real_fixture(name: str):
    return OUT / f"real_{name}.json"


@pytest.mark.llm
@pytest.mark.parametrize("name", REAL_PACKS)
def test_record_real_responses(cfg, request, name):
    if not request.config.getoption("--record"):
        pytest.skip("registrazione solo con --record")
    var = API_KEY_ENV[cfg.default.llm.provider]
    if not os.environ.get(var):
        pytest.skip(f"{var} assente")
    client = make_client(cfg)
    raw: list[dict] = []
    try:
        res = run_model(cfg, load_frozen_pack(cfg, name), client, raw=raw)
    finally:
        if raw:
            data = {"model": client.model, "responses": raw}
            real_fixture(name).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    assert res.document
