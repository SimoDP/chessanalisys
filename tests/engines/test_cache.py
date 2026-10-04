from __future__ import annotations

import chess

from chessanalyst.engines.cache import Cache, CachedAnalyzer, history_key, sf_key
from chessanalyst.engines.fake import FakeEngine
from chessanalyst.engines.types import EngineLine, NodeResult

FEN = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def result(depth: int, k: int, unstable: bool = False) -> NodeResult:
    sans = ["Be3", "f3", "h3", "Bg5", "Nb3", "Bd3", "Bc4", "a4"][:k]
    board = chess.Board(FEN)
    lines = [EngineLine(i + 1, s, board.parse_san(s).uci(), 40 - i, None, None, [s], [board.parse_san(s).uci()])
             for i, s in enumerate(sans)]
    return NodeResult(FEN, k, depth, depth + 5, 1000, 1.0, unstable, "Stockfish 16", None, lines)


def test_satisfaction_rule_and_truncation():
    c = Cache(":memory:")
    key = sf_key("Stockfish 16", chess.Board(FEN))
    c.put_sf(key, result(20, 8))
    hit = c.get_sf(key, 5, 18)
    assert hit is not None and len(hit.lines) == 5 and hit.depth == 20
    assert c.get_sf(key, 12, 18) is None   # needs more lines
    assert c.get_sf(key, 5, 22) is None    # needs more depth


def test_shallower_result_does_not_replace_deeper():
    c = Cache(":memory:")
    key = "k"
    assert c.put_sf(key, result(20, 8))
    assert not c.put_sf(key, result(18, 12))
    assert c.get_sf(key, 8, 20).depth == 20
    assert c.put_sf(key, result(20, 12))      # same depth, more MultiPV
    assert c.get_sf(key, 12, 20) is not None


def test_unstable_result_never_satisfies():
    c = Cache(":memory:")
    c.put_sf("k", result(25, 8, unstable=True))
    assert c.get_sf("k", 1, 1) is None


def test_history_key():
    b = chess.Board()
    assert history_key(b) == ""
    for uci in ("g1f3", "g8f6", "f3g1", "f6g8"):
        b.push_uci(uci)
    assert history_key(b) == "g1f3 g8f6 f3g1 f6g8"
    b.push_uci("e2e4")
    assert history_key(b) == ""
    # same FEN, different history → different key
    b1 = chess.Board()
    b1.push_uci("g1f3"); b1.push_uci("g8f6"); b1.push_uci("f3g1"); b1.push_uci("f6g8")
    assert sf_key("v", b1) != sf_key("v", chess.Board())


def test_cached_analyzer_reuses_results():
    fake = FakeEngine()
    board = chess.Board(FEN)
    fake.add(board, result(20, 8))
    an = CachedAnalyzer(fake, Cache(":memory:"))
    r1 = an.analyse(board, 8, 1.0, 18, 2.0)
    r2 = an.analyse(board, 5, 1.0, 16, 2.0)
    assert an.calls == 1 and fake.calls == 1
    assert len(r1.lines) == 8 and len(r2.lines) == 5
