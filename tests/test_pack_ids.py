"""Canonical IDs (§6.3) and internal consistency of the pack (synthetic engines)."""

from __future__ import annotations

import json

import chess

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.inputs.example import example_position
from chessanalyst.pipeline import analyse_position, resolve_settings
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

PHASE_ORDER = ["E0", "E1", "E2", "E3l1", "E3l2", "E3l3", "R", "E2b", "E2c"]   # §6.3


def make_pack(cfg, elo=1900, color="w", profile="standard"):
    an = CachedAnalyzer(SyntheticEngine(), Cache(":memory:"))
    maia = MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits)
    us = resolve_settings(cfg, color, elo, "fide", None, profile)
    pack = analyse_position(cfg, example_position(cfg), us, an, maia, None, clock=FakeClock())
    return json.loads(pack.model_dump_json())


def test_node_ids(cfg):
    pack = make_pack(cfg)
    ids = [n["id"] for n in pack["nodes"]]
    assert ids == [f"N{k}" for k in range(1, len(ids) + 1)]
    phases = [n["phase"] for n in pack["nodes"]]
    assert phases[:2] == ["E0", "E1"]
    assert [PHASE_ORDER.index(p) for p in phases] == sorted(PHASE_ORDER.index(p) for p in phases)
    by_id = {n["id"]: n for n in pack["nodes"]}
    for n in pack["nodes"][1:]:
        assert n["parent"] in by_id
    assert all(not n["citable"] for n in pack["nodes"] if n["phase"] in ("E2b", "E2c"))


def test_candidates_pvs_and_nodes(cfg):
    pack = make_pack(cfg)
    cands = pack["engine"]["candidates"]
    assert [c["id"] for c in cands] == [f"C{k}" for k in range(1, len(cands) + 1)]
    assert [c["eval_user_cp"] for c in cands] == sorted((c["eval_user_cp"] for c in cands), reverse=True)
    pvs = {p["id"]: p for p in pack["engine"]["pvs"]}
    nodes = {n["id"]: n for n in pack["nodes"]}
    root = chess.Board(pack["position"]["fen"])
    for c in cands:
        pv = pvs[c["pv"]]
        assert pv["plies"][0] == c["san"]
        b = root.copy()
        for san in pv["plies"]:
            b.push_san(san)                   # every PV is legal from the root
        if c["explained"]:
            assert nodes[c["node"]]["path"] == [c["san"]] and nodes[c["node"]]["phase"] == "E2"
        else:
            assert c["node"] is None and c["rec_score"] is None
    rec = pack["recommendation"]["id"]
    assert next(c for c in cands if c["id"] == rec)["explained"]
    for e in pack["engine"]["e3"]:
        assert nodes[e["node"]]["path"] == e["path"] and len(e["path"]) == e["level"] + 1


def test_tables_reference_candidates(cfg):
    pack = make_pack(cfg, elo=1900)
    t1 = pack["tables"]["T1"]
    ids = {c["id"] for c in pack["engine"]["candidates"] if c["explained"] or c["listed"]}
    assert {r["id"] for r in t1["rows"]} == ids
    assert [c["key"] for c in t1["columns"]] == ["move", "eval", "p_user", "line", "idea"]
    rec = pack["recommendation"]["id"]
    assert "★" in next(r for r in t1["rows"] if r["id"] == rec)["cells"]["move"]
    assert all(r["cells"]["idea"] is None for r in t1["rows"])


def test_black_user(cfg):
    pack = make_pack(cfg, elo=2400, color="b")      # White to move: opponent mode
    assert pack["user"]["color"] == "b" and not pack["position"]["user_to_move"]
    for r in pack["engine"]["replies"]:
        node = next(n for n in pack["nodes"] if n["id"] == r["node"])
        assert node["side_to_move"] == "b"
        assert all(l["eval_user_cp"] == -l["eval_white_cp"] for l in node["multipv"])
