"""Replay of the recorded real-model responses (``pytest -m llm --record``)."""

from __future__ import annotations

import json

import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.client import FakeLLM
from chessanalyst.llm.cycle import run_model
from tests.llm.test_record_llm import real_fixture


def replay(cfg, name: str):
    path = real_fixture(name)
    if not path.is_file():
        pytest.skip(f"risposta registrata del modello reale assente: {path.name} (pytest -m llm --record)")
    data = json.loads(path.read_text(encoding="utf-8"))
    pack = load_frozen_pack(cfg, name)
    res = run_model(cfg, pack, FakeLLM(data["responses"], model=data["model"]))
    return pack, res
