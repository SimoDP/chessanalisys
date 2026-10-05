"""Helpers of the M6 tests: a complete analysis folder made with synthetic engines and a recorded response."""

from __future__ import annotations

import chessanalyst.run as run_mod
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.llm.client import FakeLLM
from tests.llm_helpers import recorded
from tests.synthetic import SyntheticEngine, SyntheticMaiaBackend


def synthetic_stack(cfg, monkeypatch, tmp_path, responses: int = 6):
    eng = SyntheticEngine()

    def opener(_cfg):
        cache = Cache(":memory:")
        return run_mod.Engines(CachedAnalyzer(eng, cache), MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits, cache),
                               lambda: None)

    monkeypatch.setattr(run_mod, "open_engines", opener)
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path / "conf"))
    llm = FakeLLM([recorded("good_najdorf_1900.json")] * responses)
    monkeypatch.setattr("chessanalyst.llm.client.make_client", lambda _cfg: llm)
    return eng, llm
