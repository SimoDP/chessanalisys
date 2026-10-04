"""The claim table matches the raws: every node is legal and every move is
legal in its node."""

from __future__ import annotations

import chess

from chessanalyst.golden import raw_claims as rc
from chessanalyst.golden.data import board_at, path_label


def test_claims_are_legal():
    for c in rc.CLAIMS:
        board = board_at(c.path)
        if c.move is not None:
            board.parse_san(c.move)


def test_labels():
    assert path_label(("Be3", "e5", "Nb3")) == "6.Be3 e5 7.Nb3"
    assert path_label(()) == "radice"
    assert board_at(("--",)).turn == chess.BLACK
