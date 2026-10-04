"""M2: move-order levels ℓ2–ℓ3 (§3-ter.2, D-28), T2 rows and T3 nodes, with synthetic engines."""

from __future__ import annotations

import json

import chess
import pytest

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def pack_for(cfg, elo: int, profile: str = "deep") -> dict:
    us = resolve_settings(cfg, "w", elo, "fide", None, profile)
    pack = analyse_position(cfg, Position(board=chess.Board(NAJDORF), source="fen"), us,
                            CachedAnalyzer(SyntheticEngine(), Cache(":memory:")),
                            MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), None, clock=FakeClock())
    return json.loads(pack.model_dump_json())


@pytest.fixture(scope="module")
def p1900(cfg):
    return pack_for(cfg, 1900)


@pytest.fixture(scope="module")
def p2400(cfg):
    return pack_for(cfg, 2400)


def test_levels_and_side_to_move(p1900):
    nodes = {n["id"]: n for n in p1900["nodes"]}
    by_level = {lv: [e for e in p1900["engine"]["e3"] if e["level"] == lv] for lv in (1, 2, 3)}
    assert all(by_level.values())
    for lv, entries in by_level.items():
        for e in entries:
            n = nodes[e["node"]]
            assert n["phase"] == f"E3l{lv}" and len(e["path"]) == lv + 1 and n["citable"]
            assert n["side_to_move"] == ("b" if lv == 2 else "w")        # ℓ2: opponent, ℓ1/ℓ3: user
            assert n["maia"] is not None
            if lv > 1:
                parent = nodes[n["parent"]]
                assert parent["phase"] == f"E3l{lv - 1}" and n["path"][:-1] == parent["path"]
                assert n["via_san"] == parent["multipv"][0]["san"]        # the first move of the level above


def test_canonical_order_of_the_ids(p1900):
    """§6.3: E2 nodes, then E3 by level, candidate and reply, then E2b, then E2c."""
    phases = [n["phase"] for n in p1900["nodes"]]
    order = ["E0", "E1", "E2", "E3l1", "E3l2", "E3l3", "E2b", "E2c"]
    assert [p for i, p in enumerate(phases) if i == 0 or p != phases[i - 1]] == order
    assert [n["id"] for n in p1900["nodes"]] == [f"N{k}" for k in range(1, len(phases) + 1)]


def test_no_milestone_omission_nor_warning(p2400):
    assert not [o for o in p2400["omitted_phases"] if o["reason"] == "milestone"]
    assert "move_order_limited" not in p2400["warnings"]


def test_t2_rows_follow_the_branches(p2400):
    t2 = p2400["tables"]["T2"]
    after = [r["cells"]["t2_after"] for r in t2["rows"]]
    # every ℓ2 row («Dopo c r u») comes right after its ℓ1 row and before the ℓ3 row of the same branch
    l1 = [e for e in p2400["engine"]["e3"] if e["level"] == 1]
    assert len(after) > len(l1) + len({e["candidate"] for e in l1})
    plies = [len(a.replace("...", " ").split()) for a in after]
    assert max(plies) == 4 and min(plies) == 1   # «Dopo c» … «Dopo c r u r′»
    for prev, cur in zip(plies, plies[1:]):
        # a deeper row continues the previous branch; a new branch starts at ℓ1 (2) or at a new candidate (1)
        assert cur == prev + 1 or cur in (1, 2)


def test_t3_may_use_l2_nodes(p1900):
    ctx = p1900["engine"]["context_move"]
    nodes = {n["id"]: n for n in p1900["nodes"]}
    phases = {nodes[r["node"]]["phase"] for r in ctx["rows"]}
    assert phases <= {"E2", "E3l2"} and "E3l2" in phases
    assert all(nodes[r["node"]]["side_to_move"] == "b" for r in ctx["rows"])


def test_standard_profile_stops_at_l2(cfg):
    p = pack_for(cfg, 1900, "standard")
    assert {e["level"] for e in p["engine"]["e3"]} == {1, 2}
