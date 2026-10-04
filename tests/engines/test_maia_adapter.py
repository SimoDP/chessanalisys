from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.cache import Cache
from chessanalyst.engines.fake import FakeMaiaBackend
from chessanalyst.engines.maia2 import MaiaEngine, bucket, entropy_bits, saturated

WHITE_FEN = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
BLACK_FEN = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N1B3/PPP2PPP/R2QKB1R b KQkq - 1 6"


def epd(fen: str) -> str:
    return chess.Board(fen).epd(en_passant="legal")


@pytest.fixture
def maia(cfg):
    table = {
        (epd(WHITE_FEN), 1700, 1700): ({"c1e3": 0.3, "f1e2": 0.2, "e1e2": 0.0, "a1a8": 0.5}, 0.56),
        (epd(BLACK_FEN), 1700, 1700): ({"e7e5": 0.4, "f6g4": 0.1}, 0.56),
    }
    return MaiaEngine(FakeMaiaBackend(table), cfg.maia2_limits, Cache(":memory:"))


def test_policy_covers_legal_moves_and_sums_to_one(maia):
    pol = maia.policy(WHITE_FEN, 1700, 1700)
    board = chess.Board(WHITE_FEN)
    assert set(pol) == {m.uci() for m in board.legal_moves}
    assert "a1a8" not in pol          # illegal key dropped
    assert abs(sum(pol.values()) - 1) < 1e-6
    assert pol["c1e3"] == pytest.approx(0.6)


def test_expected_score_is_for_side_to_move(maia):
    assert maia.expected_score(WHITE_FEN, 1700, 1700) == pytest.approx(0.56)
    assert maia.expected_score(BLACK_FEN, 1700, 1700) == pytest.approx(0.44)


def test_clocks_ignored_and_cached(maia):
    other_clock = WHITE_FEN.replace(" 0 6", " 3 40")
    assert maia.policy(other_clock, 1700, 1700) == maia.policy(WHITE_FEN, 1700, 1700)
    assert maia.calls == 1


@pytest.mark.parametrize("value,b", [(400, 0), (1099, 0), (1100, 1), (1199, 1), (1999, 9), (2000, 10), (3000, 10)])
def test_bucket(cfg, value, b):
    assert bucket(value, cfg.maia2_limits) == b


def test_saturation_rule(cfg):
    assert not saturated(1999, cfg.maia2_limits)
    assert saturated(2000, cfg.maia2_limits)
    assert saturated(2025, cfg.maia2_limits)   # anchor 1900 FIDE (D-24)


def test_entropy():
    assert entropy_bits({"a": 0.5, "b": 0.5, "c": 0.0}) == pytest.approx(1.0)
