"""AC-15: ``rerun`` regenerates analysis and verification from the same ``pack.json`` without
engines; the previous files become ``*.prev.*``."""

from __future__ import annotations

import json
import shutil

import pytest

import chessanalyst.run as run_mod
from chessanalyst.cli import main
from chessanalyst.golden.packs import pack_path
from chessanalyst.llm.client import FakeLLM
from tests.llm_helpers import recorded


@pytest.fixture
def folder(cfg, tmp_path):
    d = tmp_path / "out"
    d.mkdir()
    shutil.copy(pack_path(cfg, "najdorf_w_1900"), d / "pack.json")
    return d


def _llm(monkeypatch, responses):
    llm = FakeLLM(responses)
    monkeypatch.setattr("chessanalyst.llm.client.make_client", lambda _cfg: llm)
    return llm


def _no_engines(_cfg):
    raise AssertionError("rerun non deve avviare i motori")


def test_rerun_twice(folder, monkeypatch):
    monkeypatch.setattr(run_mod, "open_engines", _no_engines)
    pack_before = (folder / "pack.json").read_bytes()
    _llm(monkeypatch, [recorded("good_najdorf_1900.json")])
    assert main(["rerun", str(folder)]) == 0
    first = (folder / "analysis.md").read_text(encoding="utf-8")
    _llm(monkeypatch, [recorded("bad_chain.json"), recorded("good_najdorf_1900.json")])
    assert main(["rerun", str(folder)]) == 0
    names = {p.name for p in folder.iterdir()}
    assert {"analysis.prev.md", "llm_raw.prev.json", "verification.prev.json", "analysis.md", "llm_raw.json",
            "verification.json", "run.log", "pack.json",
            "render.json", "render.prev.json", "analysis.html", "analysis.prev.html"} == names     # M6: the page
    assert (folder / "analysis.prev.md").read_text(encoding="utf-8") == first
    assert (folder / "pack.json").read_bytes() == pack_before          # never modified
    v = json.loads((folder / "verification.json").read_text(encoding="utf-8"))
    assert len(v["attempts"]) == 2 and v["attempts"][1]["errors"] == []
    assert "rerun di" in (folder / "run.log").read_text(encoding="utf-8")


def test_config_hash_warning(folder, monkeypatch):
    pack = json.loads((folder / "pack.json").read_text(encoding="utf-8"))
    pack["config_hash"] = "0" * 40
    (folder / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
    _llm(monkeypatch, [recorded("good_najdorf_1900.json")])
    assert main(["rerun", str(folder)]) == 0                           # a warning, not a block
    assert "config_hash diverso" in (folder / "analysis.md").read_text(encoding="utf-8")
