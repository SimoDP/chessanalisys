"""Data plan, step 4 bis: sacrifice, bad bishop and usable weak squares (features/strategic.py) and their facts."""

from __future__ import annotations

import json
from types import SimpleNamespace

import chess
import pytest

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.features.strategic import bad_bishops, sacrifice, usable_weak_squares
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from chessanalyst.plan.outline import outline_pack
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

GREEK_GIFT = "rnbq1rk1/pppn1ppp/4p3/3pP3/1b1P4/2NB1N2/PPP2PPP/R1BQK2R w KQ - 0 7"     # Bxh7+ Kxh7
FRENCH = "r1bqkb1r/pp1n1ppp/2n1p3/2ppP3/3P4/2PB1N2/PP3PPP/RNBQK2R w KQkq - 0 7"
SVESHNIKOV = "r1bqkb1r/5ppp/p1np4/1p1Np3/4P3/N7/PPP2PPP/R2QKB1R w KQkq - 0 11"


@pytest.fixture(scope="module")
def st(cfg):
    return SimpleNamespace(**cfg.structures["strategic"])


def test_sacrifice_counts_what_the_best_recaptures_win():
    b = chess.Board(GREEK_GIFT)
    assert sacrifice(b, b.parse_san("Bxh7+")) == 2             # a bishop for a pawn
    assert sacrifice(b, b.parse_san("O-O")) == 0


def test_bishops_behind_their_own_blocked_pawns_are_bad(st):
    b = chess.Board(FRENCH)                         # both sides' bishops of the chain's colour
    assert bad_bishops(b, chess.BLACK, st) == [chess.C8]
    assert bad_bishops(b, chess.WHITE, st) == [chess.C1]
    assert bad_bishops(chess.Board(), chess.WHITE, st) == []


def test_the_hole_on_d5_is_a_usable_weak_square(cfg, st):
    b = chess.Board(SVESHNIKOV)
    assert chess.D5 in usable_weak_squares(b, chess.BLACK, cfg.thresholds.features, st)
    assert usable_weak_squares(b, chess.WHITE, cfg.thresholds.features, st) == []


def _outline(cfg, fen: str, overrides=None) -> dict:
    us = resolve_settings(cfg, "w", 1600, "fide", None, "fast", 5)
    pack = analyse_position(cfg, Position(board=chess.Board(fen), source="fen"), us,
                            CachedAnalyzer(SyntheticEngine(overrides), Cache(":memory:")),
                            MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), None, clock=FakeClock())
    return outline_pack(cfg, json.loads(pack.model_dump_json()))


def test_plan_names_the_bad_bishop_and_the_weak_square(cfg):
    plan = next(k for k in _outline(cfg, FRENCH)["key_points"] if k["type"] == "plan")
    items = plan["facts"]["items"]
    assert {"key": "bad_bishop", "of": "opp", "squares": ["c8"]} in items
    assert items[0]["key"] == "structure" and items[0]["id"] == "catena_francese"


def test_the_recommended_sacrifice_is_a_fact(cfg):
    epd = chess.Board(GREEK_GIFT).epd(en_passant="legal")
    out = _outline(cfg, GREEK_GIFT, {(epd, "d3h7"): 3000})
    rec = next(k for k in out["key_points"] if k["type"] == "recommendation")
    assert rec["facts"]["san"] == "Bxh7+" and rec["facts"]["move"]["sacrifice"] == 2
