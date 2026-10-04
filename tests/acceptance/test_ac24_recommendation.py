"""AC-24: rec_score and complexity with the numbers of §4.3."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.types import EngineLine, NodeResult
from chessanalyst.explore.pvwalk import complexity, e2b_plies
from chessanalyst.scoring.recommend import Cand, rec_score, recommend

A, B = 0.3, 0.5   # band 1600_2000


def test_numbers_of_section_4_3(cfg):
    bp = cfg.thresholds.band_params["1600_2000"]
    assert (bp.A, bp.B) == (A, B)
    X = Cand("C1", 0, 0.18, 0, 1)
    Y = Cand("C2", 15, 0.12, 0, 2)
    assert rec_score(X, A, B) == pytest.approx(5.4)
    assert rec_score(Y, A, B) == pytest.approx(-11.4)
    assert recommend([X, Y], bp.L_max, A, B, 5)[0] == "C1"
    X1 = Cand("C1", 0, 0.18, 1, 1)
    assert rec_score(X1, A, B) == pytest.approx(-19.6)
    rec, scores = recommend([X1, Y], bp.L_max, A, B, 5)
    assert rec == "C2" and scores == {"C1": -19.6, "C2": -11.4}


def test_tie_within_five_points():
    # 3.0 vs 0.0: tied (< 5) → lower complexity wins, then lower loss, then E0 order
    a = Cand("C1", 0, 0.10, 0, 1)        # 3.0
    b = Cand("C2", 0, 0.0, 0, 2)         # 0.0
    assert recommend([a, b], 35, A, B, 5)[0] == "C1"   # same complexity and loss → E0 order
    a2 = Cand("C1", 10, 0.10, 0, 1)      # -7.0 (vs -0.0 → tie, lower loss wins)
    b2 = Cand("C2", 0, 0.0, 0, 2)
    assert recommend([a2, b2], 35, A, B, 5)[0] == "C2"
    c = Cand("C1", 0, 0.5, 1, 1)         # 15 - 25 = -10
    d = Cand("C2", 0, 0.0, 0, 2)         # 0 → not tied (10 ≥ 5)
    assert recommend([c, d], 35, A, B, 5)[0] == "C2"


def test_no_eligible_candidate_falls_back_to_c1():
    rec, scores = recommend([Cand("C4", 120, 0.4, 0, 4)], 35, A, B, 5)
    assert rec == "C1" and scores == {"C4": None}


def _line(rank, san, cp):
    return EngineLine(rank, san, "", cp, None, None, [san], [])


def test_complexity_counts_forced_nodes():
    b = chess.Board()
    forced = NodeResult(b.fen(), 2, 14, 14, 1, 0.1, False, "x", None, [_line(1, "e4", 150), _line(2, "d4", 40)])
    free = NodeResult(b.fen(), 2, 14, 14, 1, 0.1, False, "x", None, [_line(1, "e4", 30), _line(2, "d4", 20)])
    assert complexity([(b, forced), (b, free)], 100) == (1, False)
    assert complexity([(b, forced), (b, None)], 100) == (1, True)
    one_move = chess.Board("7k/8/8/8/8/8/6q1/7K w - - 0 1")   # Kxg2 only
    only = NodeResult(one_move.fen(), 1, 14, 14, 1, 0.1, False, "x", None, [_line(1, "Kxg2", 0)])
    assert complexity([(one_move, only)], 100) == (1, False)


def test_e2b_plies():
    assert e2b_plies(10, 8) == [2, 4, 6]
    assert e2b_plies(3, 8) == [2]
    assert e2b_plies(10, 4) == [2]
    assert e2b_plies(1, 8) == []
