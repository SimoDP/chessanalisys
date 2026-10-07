"""Usefulness test, phase 2: a pin is a fact only when it matters (the user's rule), and «il tuo alfiere in f7»
is checked against the user's color (V12). Positions from the test (02, 06) and the trap of 03."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.features.motifs import pin_matters
from chessanalyst.verify.board_claims import BoardClaims, pinned

BLACKBURNE = "r1b1kbnr/pppp1ppp/8/4N1q1/2BnP3/8/PPPP1PPP/RNBQK2R w KQkq - 1 5"
IQP = "r1bq1rk1/pp2bppp/2n1pn2/8/2BP4/2N2N2/PP3PPP/R1BQR1K1 b - - 4 10"
QGD = "r1bqkb1r/pppn1ppp/5n2/3p2B1/3P4/2N5/PP2PPPP/R2QKBNR w KQkq - 0 6"


@pytest.mark.parametrize("fen,pinner,behind,matters", [
    (BLACKBURNE, "g5", "c1", False),   # d2: the bishop behind is defended, nobody else hits it
    (BLACKBURNE, "c4", "g8", False),   # f7: the knight behind is defended by the rook
    (IQP, "e1", "e7", False),          # e6: the bishop behind is defended
    (IQP, "d8", "d1", False),          # d4: queen behind a queen's pin, defended: only a trade
    (QGD, "g5", "d8", True),           # f6: the queen behind is worth more than the bishop
])
def test_pin_matters(fen, pinner, behind, matters):
    assert pin_matters(chess.Board(fen), chess.parse_square(pinner), chess.parse_square(behind)) is matters


def test_pin_matters_undefended_or_outnumbered():
    b = chess.Board("4k3/8/8/8/1b6/8/3N4/4K3 w - - 0 1")          # Nd2 in front of the king: always
    assert pin_matters(b, chess.B4, chess.E1)
    b = chess.Board("4k3/8/8/b7/8/2N5/8/4R1K1 w - - 0 1")         # Nc3 in front of an undefended rook
    assert pin_matters(b, chess.A5, chess.E1)


def test_v12_pinned_uses_the_rule():
    pins = pinned(chess.Board(BLACKBURNE))
    assert (chess.WHITE, chess.PAWN, chess.D2) not in pins and (chess.BLACK, chess.PAWN, chess.F7) not in pins
    assert (chess.BLACK, chess.KNIGHT, chess.F6) in pinned(chess.Board(QGD))


def _claims(cfg, fen, user, text):
    pack = {"position": {"fen": fen}, "user": {"color": user}, "nodes": [], "filtered_lines": [],
            "engine": {"pvs": [], "replies": [], "candidates": []}}
    return BoardClaims(pack, cfg.wording["pieces"], cfg.verify["v12"]).check(text)


def test_possessive_gives_the_color(cfg):
    fen = "r1bqkb1r/pppp1p1p/2n2np1/4p3/2B1P3/1Q6/PPPP1PPP/RNB1K1NR b KQkq - 3 5"     # test 04, user Black
    assert _claims(cfg, fen, "b", "Il tuo alfiere in c4 è forte.")
    assert not _claims(cfg, fen, "b", "L'alfiere bianco in c4 è forte.")
    assert not _claims(cfg, fen, "b", "Il tuo cavallo in c6 è attivo.")
