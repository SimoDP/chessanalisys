"""Cards from the chess books: engine-free checks and verdict agreement."""

from __future__ import annotations

from chessanalyst import books
from tests.conftest import ROOT

S = books.load_settings(ROOT)
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_check_card_finds_side_and_illegal_moves():
    card = {"fen": START, "lato": "Nero", "mosse_chiave": [{"san": "e4"}, {"san": "e5"}]}
    out = books.check_card(card)
    assert out["fen_ok"] and not out["side_ok"] and out["bad_moves"] == ["e5"]
    assert books.check_card({"fen": "rubbish"})["fen_ok"] is False


def test_eval_classes_and_agreement():
    assert [books.eval_class(cp, None, S) for cp in (-300, -60, 0, 49, 50, 250)] == [-2, -1, 0, 0, 1, 2]
    assert books.eval_class(0, -3, S) == -2
    assert books.agreement("meglio Bianco", 0, S) == "ok"
    assert books.agreement("vince Bianco", 0, S) == "diverso"
    assert books.agreement("meglio Bianco", -1, S) == "contrario"
    assert books.agreement("poco chiara", 2, S) == "n/a"


def test_sample_is_fixed():
    cards = [{"id": f"x-{i:03d}"} for i in range(100)]
    a = books.sample(cards, S)
    assert len(a) == S["sample"]["size"] and a == books.sample(list(reversed(cards)), S)
