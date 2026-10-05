"""AC-20: «entrambi» mode (§2-bis.6, D-16): Stockfish analyses every node once (shared cache), two analyses
in the same file, the color to move first."""

from __future__ import annotations

import json
from collections import Counter

import chess
import pytest

import chessanalyst.run as run_mod
from chessanalyst.cli import main
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.inputs.example import example_position
from chessanalyst.llm.client import FakeLLM
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.llm_helpers import recorded
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend


def _both(cfg):
    return [resolve_settings(cfg, "w", 1900, "fide", 1500, "fast"),
            resolve_settings(cfg, "b", 1500, "fide", 1900, "fast")]


def test_stockfish_once_per_node(cfg):
    eng = SyntheticEngine()
    cache = Cache(":memory:")
    an = CachedAnalyzer(eng, cache)
    maia = MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits, cache)
    pos = example_position(cfg)
    packs = [analyse_position(cfg, pos, us, an, maia, None, clock=FakeClock()) for us in _both(cfg)]
    keys = Counter((epd, roots) for epd, _k, _d, roots in eng.requests)
    assert keys and max(keys.values()) == 1, [k for k, n in keys.items() if n > 1]
    w, b = (json.loads(p.model_dump_json()) for p in packs)
    assert w["user"]["color"] == "w" and w["position"]["user_to_move"]
    assert b["user"]["color"] == "b" and not b["position"]["user_to_move"]
    assert w["user"]["elo_declared"] == b["user"]["opp_elo_declared"] == 1900
    assert w["engine"]["root"]["eval_user_cp"] == -b["engine"]["root"]["eval_user_cp"]


@pytest.fixture
def synthetic_stack(cfg, root, monkeypatch):
    eng = SyntheticEngine()

    def opener(_cfg):
        cache = Cache(":memory:")
        return run_mod.Engines(CachedAnalyzer(eng, cache), MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits, cache),
                               lambda: None)

    monkeypatch.setattr(run_mod, "open_engines", opener)
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(root / "nonexistent_profile_dir"))
    llm = FakeLLM([recorded("good_najdorf_1900.json")] * 6)
    monkeypatch.setattr("chessanalyst.llm.client.make_client", lambda _cfg: llm)
    return eng, llm


def test_two_analyses_in_one_file(tmp_path, synthetic_stack):
    eng, llm = synthetic_stack
    code = main(["analyze", "--yes", "--color", "both", "--elo-white", "1900", "--elo-black", "1500",
                 "--budget", "fast", "--out", str(tmp_path)])
    assert code == 0
    out = next(tmp_path.iterdir())
    names = {p.name for p in out.iterdir()}
    assert {"analysis.md", "pack_white.json", "pack_black.json", "llm_raw_white.json", "llm_raw_black.json",
            "verification_white.json", "verification_black.json", "run.log"} <= names
    assert "pack.json" not in names and "analysis_white.md" not in names
    doc = (out / "analysis.md").read_text(encoding="utf-8")
    assert doc.count("# Analisi della posizione") == 2
    second = doc.index("# Analisi della posizione", 1)
    assert "Giochi con: il Bianco" in doc[:second] and "Giochi con: il Nero" in doc[second:]   # White to move first
    assert doc[:second].endswith(run_mod.BOTH_SEPARATOR)
    w = json.loads((out / "pack_white.json").read_text(encoding="utf-8"))
    b = json.loads((out / "pack_black.json").read_text(encoding="utf-8"))
    assert w["user"]["elo_declared"] == 1900 and b["user"]["elo_declared"] == 1500
    assert w["user"]["opp_elo_declared"] == 1500 and b["user"]["opp_elo_declared"] == 1900
    keys = Counter((epd, roots) for epd, _k, _d, roots in eng.requests)
    assert max(keys.values()) == 1
    page = (out / "analysis.html").read_text(encoding="utf-8")      # M6: one page, the two perspectives
    assert page.count('<section class="part">') == 2 and page.index("il Bianco") < page.index("Giochi con: il Nero")
    # rerun of both perspectives from the two packs
    assert main(["rerun", str(out)]) in (0, 5)


@pytest.mark.parametrize("argv,message", [
    (["--color", "both", "--opp-elo", "1500"], "--elo-white e --elo-black"),
    (["--color", "white", "--elo-white", "1500"], "solo con --color both"),
])
def test_both_mode_options(argv, message, capsys, tmp_path):
    assert main(["analyze", "--yes", "--out", str(tmp_path)] + argv) == 2
    assert message in capsys.readouterr().err


def test_color_to_move_first(cfg):
    from chessanalyst.run import both_order

    b = chess.Board()
    assert both_order(b) == ["w", "b"]
    b.push_san("e4")
    assert both_order(b) == ["b", "w"]
