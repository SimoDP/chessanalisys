"""AC-34: exit codes (§2-bis.1) and configuration precedence (D-56)."""

from __future__ import annotations

import json
import shutil

import pytest
import yaml

import chessanalyst.run as run_mod
from chessanalyst.cli import main
from chessanalyst.config import CONFIG_FILES, load_config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.errors import EnvironmentProblem
from chessanalyst.settings import effective
from chessanalyst.llm.client import FakeLLM
from tests.conftest import ROOT
from tests.fault_fixtures import envelope
from tests.synthetic import SyntheticEngine, SyntheticMaiaBackend


@pytest.fixture
def fake_engines(cfg, monkeypatch):
    def opener(_cfg):
        return run_mod.Engines(CachedAnalyzer(SyntheticEngine(), Cache(":memory:")),
                               MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), lambda: None)

    monkeypatch.setattr(run_mod, "open_engines", opener)
    # the model answers with the 1500 fewshot (degraded on the synthetic pack: still exit code 0)
    resp = envelope(json.loads((ROOT / "examples/golden/fewshot/najdorf_w_1500.json").read_text()))
    monkeypatch.setattr("chessanalyst.llm.client.make_client", lambda _cfg: FakeLLM([resp] * 3))


def test_exit_0_with_pack(fake_engines, tmp_path, monkeypatch):
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path / "conf"))
    assert main(["analyze", "--yes", "--elo", "1500", "--budget", "fast", "--out", str(tmp_path / "o")]) == 0
    [outdir] = list((tmp_path / "o").iterdir())
    assert outdir.name.endswith("_sicilian_defense_najdorf_variation") or outdir.name.split("_", 2)[2].startswith("pos_")
    assert {p.name for p in outdir.iterdir()} == {"pack.json", "run.log", "analysis.md", "llm_raw.json",
                                                  "verification.json"}
    pack = json.loads((outdir / "pack.json").read_text())
    assert pack["user"]["elo_declared"] == 1500 and pack["user"]["budget_profile"] == "fast"
    assert not (tmp_path / "conf" / "profile.yaml").exists()      # analyze never writes the profile


def test_exit_0_on_refused_confirmation(fake_engines, tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert main(["analyze", "--out", str(tmp_path)]) == 0
    assert not any(tmp_path.iterdir())


def test_exit_1_on_bug(fake_engines, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("bug")

    monkeypatch.setattr(run_mod, "analyse_position", boom)
    assert main(["analyze", "--yes", "--out", str(tmp_path)]) == 1
    [outdir] = list(tmp_path.iterdir())
    assert "RuntimeError: bug" in (outdir / "run.log").read_text()


def test_exit_2_usage(tmp_path):
    assert main(["analyze", "--input", "fen", "--yes"]) == 2                     # no text
    assert main(["analyze", "--input", "example", "--text", "x"]) == 2
    with pytest.raises(SystemExit) as e:
        main(["analyze", "--at", "3w", "--ply", "4"])
    assert e.value.code == 2
    assert main(["analyze", "--elo", "100", "--yes"]) == 2


def test_exit_3_invalid_input(tmp_path):
    assert main(["analyze", "--input", "fen", "--text", "8/8/8/8 w", "--yes", "--out", str(tmp_path)]) == 3
    assert main(["analyze", "--input", "pgn", "--file", str(tmp_path / "missing.pgn"), "--yes"]) == 3


def test_exit_4_environment(monkeypatch, tmp_path):
    def missing(_cfg):
        raise EnvironmentProblem("Stockfish non trovato")

    monkeypatch.setattr(run_mod, "open_engines", missing)
    assert main(["analyze", "--yes", "--out", str(tmp_path)]) == 4


def test_exit_4_missing_api_key_keeps_the_pack(cfg, monkeypatch, tmp_path, capsys):
    def opener(_cfg):
        return run_mod.Engines(CachedAnalyzer(SyntheticEngine(), Cache(":memory:")),
                               MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), lambda: None)

    monkeypatch.setattr(run_mod, "open_engines", opener)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["analyze", "--yes", "--budget", "fast", "--out", str(tmp_path)]) == 4
    [outdir] = list(tmp_path.iterdir())
    assert (outdir / "pack.json").is_file() and not (outdir / "analysis.md").exists()
    err = capsys.readouterr().err
    assert "OPENROUTER_API_KEY" in err and "chessanalyst rerun" in err


def test_precedence(root, tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "config").mkdir(parents=True)
    for name in CONFIG_FILES:
        shutil.copy(root / "config" / name, proj / "config" / name)
    conf = tmp_path / "conf"
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(conf))
    assert effective(load_config(proj))["elo"] == 1900                          # default.yaml
    (proj / "config" / "local.yaml").write_text(yaml.safe_dump({"user": {"elo": 1600}}))
    cfg = load_config(proj)
    assert effective(cfg)["elo"] == 1600                                        # local.yaml
    conf.mkdir()
    (conf / "profile.yaml").write_text(yaml.safe_dump({"elo": 1700, "color": "b"}))
    assert effective(cfg)["elo"] == 1700 and effective(cfg)["color"] == "b"    # profile.yaml
    assert effective(cfg, {"elo": 1800, "color": None})["elo"] == 1800        # command line
    assert effective(cfg, {"elo": 1800})["color"] == "b"
