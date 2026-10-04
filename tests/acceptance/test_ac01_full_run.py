"""AC-01: example position, FakeEngine, FakeMaia and FakeLLM (``good_najdorf_1900.json``):
``analyze --yes --elo 1900 --budget deep`` writes the five files and exits with 0."""

from __future__ import annotations

import json

import pytest

import chessanalyst.run as run_mod
from chessanalyst.cli import main
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.fake import FakeEngine, FakeMaiaBackend
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.client import FakeLLM
from tests.llm_helpers import recorded


@pytest.fixture
def recorded_stack(cfg, root, monkeypatch):
    rec = root / "fixtures" / "recorded"
    calls = {}

    def opener(_cfg):
        cache = Cache(":memory:")
        eng = FakeEngine.from_dir(rec / "engine")
        calls["engine"] = eng
        return run_mod.Engines(CachedAnalyzer(eng, cache),
                               MaiaEngine(FakeMaiaBackend.from_dir(rec / "maia"), cfg.maia2_limits, cache), lambda: None)

    def client(responses):
        llm = FakeLLM(responses)
        monkeypatch.setattr("chessanalyst.llm.client.make_client", lambda _cfg: llm)
        return llm

    monkeypatch.setattr(run_mod, "open_engines", opener)
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(root / "nonexistent_profile_dir"))
    return client


def test_full_run(cfg, tmp_path, recorded_stack):
    llm = recorded_stack([recorded("good_najdorf_1900.json")])
    assert main(["analyze", "--yes", "--elo", "1900", "--budget", "deep", "--out", str(tmp_path)]) == 0
    [outdir] = list(tmp_path.iterdir())
    assert {p.name for p in outdir.iterdir()} == {"analysis.md", "pack.json", "llm_raw.json", "verification.json",
                                                  "run.log"}
    pack = json.loads((outdir / "pack.json").read_text(encoding="utf-8"))
    frozen = load_frozen_pack(cfg, "najdorf_w_1900")
    for k in ("engine", "nodes", "section_plan", "tables", "features", "recommendation", "maia"):
        assert pack[k] == frozen[k], k                    # same pack as the frozen one (OQ-M1b-1)
    v = json.loads((outdir / "verification.json").read_text(encoding="utf-8"))
    assert [a["errors"] for a in v["attempts"]] == [[]]
    assert len(json.loads((outdir / "llm_raw.json").read_text(encoding="utf-8"))) == 1
    doc = (outdir / "analysis.md").read_text(encoding="utf-8")
    assert doc.startswith("# Analisi della posizione: Sicilian Defense: Najdorf Variation")
    assert "modello di linguaggio: fake-llm" in doc and "Retry: 0" in doc
    assert len(llm.requests) == 1


def test_model_failure_is_exit_5_and_keeps_the_pack(tmp_path, recorded_stack, capsys):
    recorded_stack([recorded("max_tokens.json")] * 3)
    assert main(["analyze", "--yes", "--elo", "1900", "--budget", "deep", "--out", str(tmp_path)]) == 5
    [outdir] = list(tmp_path.iterdir())
    assert (outdir / "pack.json").is_file() and not (outdir / "analysis.md").exists()
    assert len(json.loads((outdir / "llm_raw.json").read_text(encoding="utf-8"))) == 3
    assert f"chessanalyst rerun {outdir}" in capsys.readouterr().err
