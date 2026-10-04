"""Pipeline on the recorded engine fixtures (fixtures/recorded, Appendix G)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.fake import FakeEngine, FakeMaiaBackend
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.engines.openings import OpeningIndex
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.synthetic import FakeClock


def recorded_engines(root: Path, cfg, cache: Cache | None = None):
    edir = root / "fixtures" / "recorded" / "engine"
    mdir = root / "fixtures" / "recorded" / "maia"
    if not any(edir.glob("*.json")):
        pytest.skip("registrazioni assenti: pytest -m engines --record")
    eng = FakeEngine.from_dir(edir)
    cache = cache or Cache(":memory:")
    return eng, CachedAnalyzer(eng, cache), MaiaEngine(FakeMaiaBackend.from_dir(mdir), cfg.maia2_limits, cache)


def openings(cfg):
    path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    return OpeningIndex.load(path) if path.is_file() else None


def recorded_pack(cfg, root: Path, fen_name: str, color: str, elo: int, profile: str = "deep",
                  cache: Cache | None = None) -> tuple[dict, FakeEngine, MaiaEngine]:
    eng, an, maia = recorded_engines(root, cfg, cache)
    board = parse_fen((root / "fixtures" / "positions" / f"{fen_name}.fen").read_text(), cfg.wording["errors"])
    us = resolve_settings(cfg, color, elo, "fide", None, profile)
    pack = analyse_position(cfg, Position(board=board, source="fen"), us, an, maia, openings(cfg), clock=FakeClock())
    return json.loads(pack.model_dump_json()), eng, maia
