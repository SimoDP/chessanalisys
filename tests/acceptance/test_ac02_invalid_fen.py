"""AC-02: the 12 invalid FENs of Appendix G.2; no silent fallback to the
example; interactive flow exits with code 3 after max_attempts."""

from __future__ import annotations

import pytest

from chessanalyst.cli import main
from chessanalyst.errors import InputError
from chessanalyst.inputs.load import load_position
from chessanalyst.interactive import IO, interactive

CASES = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP", "FEN malformata"),
    ("rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "FEN malformata"),
    ("rnbq1bnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQ - 0 1", "Manca il re nero"),
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1", "FEN malformata"),
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKPNR w KQkq - 0 1", "Pedone in prima o ottava traversa"),
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1", "Casa di en passant non valida"),
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1", "Diritti di arrocco incoerenti"),
    ("4k3/8/8/8/8/8/8/r3K3 b - - 0 1", "Il lato che non muove è sotto scacco"),
    ("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3", "Posizione terminale (matto)"),
    ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "Posizione terminale (stallo)"),
    ("8/8/4k3/8/8/4K3/8/8 w - - 0 1", "Posizione terminale (materiale insufficiente)"),
    ("4k3/8/8/8/8/8/8/3KK3 w - - 0 1", "Troppi re"),
]


@pytest.mark.parametrize("fen,message", CASES)
def test_message(cfg, fen, message):
    with pytest.raises(InputError) as e:
        load_position(cfg, "fen", fen)
    assert str(e.value).startswith(message)


@pytest.mark.parametrize("fen,message", CASES[:3])
def test_analyze_exits_3_without_fallback(fen, message, capsys, tmp_path):
    assert main(["analyze", "--input", "fen", "--text", fen, "--yes", "--out", str(tmp_path)]) == 3
    assert message in capsys.readouterr().err
    assert not any(tmp_path.iterdir())          # nothing analysed, no example used


def test_interactive_exits_3_after_max_attempts(cfg, tmp_path, monkeypatch):
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path))
    answers = iter(["bianco", "1900", "fast", "fen"] + [CASES[2][0]] * cfg.default.input.max_attempts)
    said: list[str] = []
    ran: list = []

    def ask(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None

    code = interactive(cfg, IO(ask=ask, say=said.append), lambda pos, v: ran.append(pos) or 0)
    assert code == 3 and not ran
    assert sum("Manca il re nero" in s for s in said) == cfg.default.input.max_attempts
