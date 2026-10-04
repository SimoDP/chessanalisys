"""Detail 1–5 through the whole pipeline (§7.2, M4): explained candidates, E3, line length, opponent's T."""

from __future__ import annotations

import json

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.inputs.example import example_position
from chessanalyst.pack.llm_view import llm_view
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend


def pack(cfg, elo, detail):
    cache = Cache(":memory:")
    an = CachedAnalyzer(SyntheticEngine(), cache)
    maia = MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits, cache)
    us = resolve_settings(cfg, "w", elo, "fide", None, "fast", detail)
    return json.loads(analyse_position(cfg, example_position(cfg), us, an, maia, None, clock=FakeClock()).model_dump_json())


def test_detail_2_below_2150(cfg):
    p = pack(cfg, 1900, 2)
    bp = cfg.thresholds.band_params["1600_2000"]
    assert sum(c["explained"] for c in p["engine"]["candidates"]) == bp.explained_min
    assert {"phase": "E3", "reason": "detail"} in p["omitted_phases"] and not p["engine"]["e3"]
    assert p["constraints"]["max_pv_plies"] == bp.plies_max - 1 and p["user"]["detail_level"] == 2
    assert "T4" in p["tables"]


def test_detail_3_and_e3_mandatory_from_2150(cfg):
    p = pack(cfg, 2200, 3)
    assert not any(o["phase"] == "E3" for o in p["omitted_phases"]) and p["engine"]["e3"]   # mandatory from 2150


def test_detail_5_opponent_t(cfg):
    p = pack(cfg, 1900, 5)
    t4 = p["tables"]["T4"]
    keys = [c["key"] for c in t4["columns"]]
    assert keys[:4] == ["category", "T", "T_opp", "R"]
    cats = {c["id"]: c for c in p["categories"]}
    assert all(r["cells"]["T_opp"] == str(cats[r["id"]]["T"]["b"]) for r in t4["rows"])
    v = llm_view(p, cfg.default.llm.view)
    assert all("T_opp" in c for c in v["categories"])
    assert all("T_opp" not in c for c in llm_view(pack(cfg, 1900, 4), cfg.default.llm.view)["categories"])
    assert p["constraints"]["max_pv_plies"] == cfg.thresholds.band_params["1600_2000"].plies_max + 2
