"""AC-33: node cap and deadline discard in the order of §3-ter.2; E2b reuses
E3-ℓ1 nodes; complexity_partial set when needed."""

from __future__ import annotations

import chess

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.explore.runner import UserCtx, explore
from tests.helpers import with_profile
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def run(cfg, profile="standard", clock=None, cost=1.0, **changes):
    cfg2 = with_profile(cfg, profile, **changes) if changes else cfg
    eng = SyntheticEngine(clock=clock, cost=cost)
    an = CachedAnalyzer(eng, Cache(":memory:"))
    maia = MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits)
    bp = cfg.thresholds.band_params["1600_2000"]
    ctx = UserCtx(chess.WHITE, 1700, 1700, "1600_2000", bp, profile)
    exp = explore(cfg2, chess.Board(NAJDORF), ctx, an, maia, clock=clock or FakeClock())
    return exp, eng


def test_full_run_without_cap(cfg):
    exp, eng = run(cfg, max_nodes=1000)
    assert not exp.omitted_nodes
    assert len(exp.e2) == 5 and exp.e3 and exp.e2b
    assert exp.omitted_phases == []                                    # M2: standard runs ℓ1–ℓ2
    assert {lv for lv, _, _ in exp.e3} == {1, 2}


def test_e2b_reuses_e3_l1_nodes(cfg):
    exp, eng = run(cfg, max_nodes=1000)
    analysed = [r[0] for r in eng.requests]
    assert len(analysed) == len(set((r[0], r[3]) for r in eng.requests))   # never the same search twice
    e3_epds = {n.board.epd(en_passant="legal") for _, _, n in exp.e3}
    e2b_epds = {n.board.epd(en_passant="legal") for lst in exp.e2b.values() for n in lst}
    shared = e3_epds & e2b_epds
    assert shared, "a node of E2b coincides with one of E3-ℓ1"
    for epd in shared:
        assert analysed.count(epd) == 1


def test_node_cap_discards_in_order(cfg):
    full, _ = run(cfg, max_nodes=1000)
    base = 1 + 1 + 1 + len(full.e2)          # E0, E4, E1, E2: never discarded
    exp, eng = run(cfg, max_nodes=base + 2)
    assert eng.calls == base + 2
    phases = [o["phase"] for o in exp.omitted_nodes]
    # E3-ℓ1 keeps its two best pairs, then E2b and E2c are discarded entirely
    assert len(exp.e3) == 2
    assert phases.index("E3l1") < phases.index("E2b")
    assert all(o["reason"] == "node_cap" for o in exp.omitted_nodes)
    kept = [(u, n.path[-1]) for _, u, n in exp.e3]
    assert kept == [(u, n.path[-1]) for _, u, n in full.e3][:2]
    assert any(partial for _, partial in exp.complexity.values())


def test_deadline_drops_discardable_nodes(cfg):
    clock = FakeClock()
    prof = cfg.exploration.profiles["fast"]
    # every search costs B: after E0 the deadline (factor × B) is exceeded
    exp, eng = run(cfg, "fast", clock=clock, cost=prof.B_s * prof.deadline_factor, max_nodes=1000)
    assert len(exp.e2) == 5 and all(n.result is not None for n in exp.e2.values())   # E0–E2 continue
    assert not exp.e3 and not any(exp.e2b.values())
    assert exp.omitted_nodes and all(o["reason"] == "deadline" for o in exp.omitted_nodes)
    assert {o["phase"] for o in exp.omitted_nodes} >= {"E3l1", "E2b"}
