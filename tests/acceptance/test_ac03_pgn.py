"""AC-03: PGN cases of Appendix G.3 (pasted text and file)."""

from __future__ import annotations

import pytest

from chessanalyst.cli import main
from chessanalyst.errors import InputError, UsageError
from chessanalyst.inputs.load import load_position
from chessanalyst.inputs.pgn import truncated_pgn
from chessanalyst.inputs.read_source import read_source
from chessanalyst.interactive import IO, interactive

NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def pgn(root, name):
    return root / "fixtures" / "pgn" / name


def load(cfg, root, name, **kw):
    return load_position(cfg, "pgn", read_source(str(pgn(root, name))), **kw)


@pytest.mark.parametrize("name", ["single.pgn", "single_bom.pgn", "annotated.pgn"])
def test_final_position_is_najdorf(cfg, root, name):
    pos = load(cfg, root, name)
    assert pos.fen == NAJDORF and pos.plies == 10 and pos.last_move_san == "a6"


def test_pasted_text_equals_file(cfg, root):
    text = pgn(root, "single.pgn").read_text(encoding="utf-8")
    assert load_position(cfg, "pgn", text).fen == NAJDORF


def test_two_games(cfg, root):
    with pytest.raises(InputError, match="2 partite"):
        load(cfg, root, "two_games.pgn")
    pos = load(cfg, root, "two_games.pgn", game_no=2)
    assert pos.board.move_stack[0].uci() == "d2d4"
    assert main(["analyze", "--input", "pgn", "--file", str(pgn(root, "two_games.pgn")), "--yes"]) == 3


def test_setup_fen(cfg, root):
    assert load(cfg, root, "setup_fen.pgn", ply=0).fen == "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"
    end = load(cfg, root, "setup_fen.pgn")
    assert end.plies == 2 and end.start_fen == "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"
    assert "[SetUp \"1\"]" in truncated_pgn(end)


def test_illegal_move(cfg, root):
    with pytest.raises(InputError) as e:
        load(cfg, root, "illegal.pgn")
    assert str(e.value) == "semimossa 3 (mossa 2 del Bianco): `Nf6` non è legale"


def test_mate(cfg, root):
    with pytest.raises(InputError, match="--at"):
        load(cfg, root, "mate.pgn")
    pos = load(cfg, root, "mate.pgn", at="2w")
    assert not pos.board.turn  # Black to move


@pytest.mark.parametrize("at,ply,ok,expected", [
    ("3w", None, True, 5), ("5b", None, True, 10), (None, 0, True, 0), ("6w", None, False, None),
])
def test_at_cases(cfg, root, at, ply, ok, expected):
    if ok:
        assert load(cfg, root, "single.pgn", at=at, ply=ply).plies == expected
    else:
        with pytest.raises(InputError, match="La partita ha solo 10 semimosse"):
            load(cfg, root, "single.pgn", at=at, ply=ply)


def test_fen_given_as_pgn(cfg, root):
    with pytest.raises(UsageError, match="sembra un FEN"):
        load(cfg, root, "fen_as_pgn.txt")
    assert main(["analyze", "--input", "pgn", "--file", str(pgn(root, "fen_as_pgn.txt")), "--yes"]) == 2


def test_fen_given_as_pgn_interactive(cfg, root, tmp_path, monkeypatch):
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path))
    answers = iter(["", "", "", "", "pgn", str(pgn(root, "fen_as_pgn.txt")), "s", "s"])
    got = []
    code = interactive(cfg, IO(ask=lambda p: next(answers), say=lambda s: None),
                       lambda pos, v: got.append(pos.fen) or 0)
    assert code == 0 and got == [NAJDORF]


def test_garbage(cfg, root):
    with pytest.raises(InputError, match="Formato non riconosciuto"):
        load(cfg, root, "garbage.txt")


def test_truncated_game_pgn(cfg, root):
    pos = load(cfg, root, "annotated.pgn", at="3w")
    out = truncated_pgn(pos)
    assert "{" not in out and "(" not in out and "$" not in out
    assert out.strip().endswith("1. e4 c5 2. Nf3 d6 3. d4 *")
    assert "WhiteElo" not in truncated_pgn(load(cfg, root, "single.pgn"))
