"""AC-29: minimum-depth analysis primitive (§3.1.3) against FakeUCI."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.stockfish import StockfishEngine
from tests.conftest import uci_iterations

LINES = [("cp 30", "e2e4 e7e5"), ("cp 20", "d2d4 d7d5")]


def engine(cmd: list[str]) -> StockfishEngine:
    return StockfishEngine(cmd, hash_mb=16, poll_s=0.01, threads=1)


def test_stops_on_time_and_depth(fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 60), LINES, delay=0.02))
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.3, d_min=5, t_cap=5.0)
    assert not res.unstable_depth
    assert res.depth >= 5
    assert 0.3 <= res.time_s < 2.0
    assert [ln.san for ln in res.lines] == ["e4", "d4"]
    assert res.lines[0].pv == ["e4", "e5"]
    assert res.lines[0].eval_white_cp == 30 and res.lines[0].wdl_white == [100, 850, 50]
    assert res.engine_version == "Stockfish 19"


def test_stops_as_soon_as_min_depth_when_target_reached(fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 60), LINES, delay=0.05))
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.0, d_min=4, t_cap=5.0)
    assert not res.unstable_depth
    assert 4 <= res.depth <= 6


def test_cap_marks_unstable_depth(fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 4), LINES, delay=0.01))
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.1, d_min=10, t_cap=0.5)
    assert res.unstable_depth
    assert res.depth == 3
    assert 0.5 <= res.time_s < 1.5
    assert len(res.lines) == 2


def test_bound_lines_are_ignored(fake_uci):
    events = uci_iterations(range(1, 5), LINES, delay=0.01)
    events.append({"delay": 0.01, "line": "info depth 5 seldepth 6 multipv 1 score cp 999 lowerbound "
                                           "nodes 9 time 9 pv e2e4 e7e5"})
    events.append({"delay": 0.0, "line": "info depth 5 seldepth 6 multipv 2 score cp -999 upperbound "
                                          "nodes 9 time 9 pv d2d4 d7d5"})
    cmd = fake_uci(events)
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.0, d_min=10, t_cap=0.4)
    assert res.depth == 4
    assert [ln.eval_white_cp for ln in res.lines] == [30, 20]


def test_snapshot_only_on_complete_iteration(fake_uci):
    events = uci_iterations(range(1, 5), LINES, delay=0.01)
    events.append({"delay": 0.01, "line": "info depth 5 seldepth 6 multipv 1 score cp 77 nodes 9 time 9 pv e2e4 c7c5"})
    cmd = fake_uci(events)
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.0, d_min=10, t_cap=0.4)
    assert res.depth == 4
    assert res.lines[0].eval_white_cp == 30
    assert res.lines[0].pv == ["e4", "e5"]


def test_no_complete_iteration_falls_back_to_latest_lines(fake_uci):
    events = [{"delay": 0.01, "line": "info depth 1 seldepth 1 multipv 1 score cp 15 nodes 5 time 1 pv e2e4"}]
    cmd = fake_uci(events)
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=2, t_target=0.0, d_min=1, t_cap=0.3)
    assert res.unstable_depth
    assert len(res.lines) == 1 and res.lines[0].san == "e4"


@pytest.mark.parametrize("score,cp,mate", [("mate 3", 9997, 3), ("mate -2", -9998, -2), ("cp 12000", 9999, None)])
def test_score_conversion(fake_uci, score, cp, mate):
    cmd = fake_uci(uci_iterations(range(1, 3), [(score, "e2e4")], delay=0.01))
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=1, t_target=0.0, d_min=2, t_cap=2.0)
    assert res.lines[0].eval_white_cp == cp
    assert res.lines[0].mate_white == mate


def test_root_moves_limit_k(fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 4), [("cp 5", "g1f3")], delay=0.01))
    with engine(cmd) as sf:
        res = sf.analyse_node(chess.Board(), multipv=8, t_target=0.0, d_min=2, t_cap=2.0,
                              root_moves=[chess.Move.from_uci("g1f3")])
    assert res.multipv == 1
    assert res.root_moves == ["g1f3"]
    assert res.lines[0].san == "Nf3"
