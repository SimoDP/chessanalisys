"""Fault injection: a candidate that mates (or stalemates) leaves no node to analyse after it (book bench,
grooten-095 crashed the pipeline in E2)."""

from __future__ import annotations

import json

import chess

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

FEN = "5rk1/7p/8/5N2/8/8/8/B6K w - - 0 1"        # Nh6 is mate


def test_mating_candidate_is_explained_without_an_e2_node(cfg):
    epd = chess.Board(FEN).epd(en_passant="legal")
    engine = SyntheticEngine(overrides={(epd, "f5h6"): 5000})
    us = resolve_settings(cfg, "w", 1600, "fide", None, "deep")
    pack = analyse_position(cfg, Position(board=chess.Board(FEN), source="fen"), us,
                            CachedAnalyzer(engine, Cache(":memory:")),
                            MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), None, clock=FakeClock())
    data = json.loads(pack.model_dump_json())
    assert any(n["phase"] == "E2" for n in data["nodes"])
    assert not any(n["phase"] == "E2" and n["path"][0] == "Nh6#" for n in data["nodes"])
