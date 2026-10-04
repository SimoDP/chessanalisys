"""Real Stockfish / Maia-2 (``pytest -m engines``)."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.cache import Cache
from chessanalyst.errors import EnvironmentProblem

pytestmark = pytest.mark.engines
NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def test_stockfish_primitive_real(cfg):
    from chessanalyst.engines.factory import make_stockfish

    with make_stockfish(cfg) as sf:
        assert sf.version == cfg.default.engines.stockfish.version_pin
        res = sf.analyse_node(chess.Board(NAJDORF), multipv=4, t_target=0.5, d_min=12, t_cap=30)
    assert not res.unstable_depth and res.depth >= 12
    assert len(res.lines) == 4
    assert all(ln.wdl_white is not None and sum(ln.wdl_white) == 1000 for ln in res.lines)


def test_null_move_node_real(cfg):
    from chessanalyst.engines.factory import make_stockfish

    b = chess.Board(NAJDORF)
    b.push(chess.Move.null())
    with make_stockfish(cfg) as sf:
        res = sf.analyse_node(b, multipv=2, t_target=0.2, d_min=10, t_cap=30)
    assert res.fen.split()[1] == "b"
    assert all(chess.Board(res.fen).is_legal(chess.Move.from_uci(ln.uci)) for ln in res.lines)


@pytest.mark.parametrize("fen", [NAJDORF, "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N1B3/PPP2PPP/R2QKB1R b KQkq - 1 6"])
def test_maia_real(cfg, fen):
    """§3.2 M0 checks: legal keys, sum 1, clocks ignored."""
    from chessanalyst.engines.factory import make_maia

    try:
        maia = make_maia(cfg, Cache(":memory:"))
    except EnvironmentProblem as e:
        pytest.skip(str(e))
    pol = maia.policy(fen, 1700, 1700)
    board = chess.Board(fen)
    assert set(pol) == {m.uci() for m in board.legal_moves}
    assert abs(sum(pol.values()) - 1) < 1e-6
    other = " ".join(fen.split()[:4] + ["7", "30"])
    maia2 = make_maia(cfg, None)
    assert maia2.policy(other, 1700, 1700) == maia2.policy(fen, 1700, 1700)
    assert 0.0 <= maia.expected_score(fen, 1700, 1700) <= 1.0
