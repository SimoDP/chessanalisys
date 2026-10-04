"""Interactive flow (§2-bis.1): answers, defaults, profile saved only after confirmation; from M4 «entrambi»,
detail 1–5 and the Elo of the PGN tags (§2-bis.4 point 8)."""

from __future__ import annotations

import yaml

from chessanalyst.interactive import IO, interactive

NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def drive(cfg, answers, monkeypatch, tmp_path):
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path))
    it = iter(answers)
    said, ran = [], []

    def ask(prompt):
        said.append(prompt)
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    code = interactive(cfg, IO(ask=ask, say=said.append), lambda pos, v: ran.append((pos, v)) or 0)
    return code, said, ran


def test_defaults_example_and_profile(cfg, monkeypatch, tmp_path):
    code, said, ran = drive(cfg, ["", "", "", "", "", "s"], monkeypatch, tmp_path)
    assert code == 0 and ran[0][0].fen == NAJDORF
    assert ran[0][1]["color"] == "w" and ran[0][1]["elo"] == 1900 and ran[0][1]["budget"] == "standard"
    assert ran[0][1]["detail"] == 4 and any("Dettaglio [1-5, 4]" in s for s in said)
    prof = yaml.safe_load((tmp_path / "profile.yaml").read_text())
    assert prof == {"color": "w", "elo": 1900, "elo_scale": "fide", "budget": "standard", "detail": 4}
    assert any("Apertura" in s for s in said)


def test_answers_are_parsed_and_proposed_next_time(cfg, monkeypatch, tmp_path):
    code, _, ran = drive(cfg, ["NERO", "abc", "1700", "deep", "7", "2", "esempio", "s"], monkeypatch, tmp_path)
    assert code == 0 and ran[0][1]["color"] == "b" and ran[0][1]["elo"] == 1700 and ran[0][1]["budget"] == "deep"
    assert ran[0][1]["detail"] == 2
    code, said, ran = drive(cfg, ["", "", "", "", "", "s"], monkeypatch, tmp_path)
    assert ran[0][1]["elo"] == 1700 and any("Elo [1700]" in s for s in said) and ran[0][1]["detail"] == 2


def test_refusal_does_not_save_profile(cfg, monkeypatch, tmp_path):
    code, _, ran = drive(cfg, ["bianco", "1500", "fast", "", "", "n"], monkeypatch, tmp_path)
    assert code == 0 and not ran and not (tmp_path / "profile.yaml").exists()


def test_correggi_goes_back_to_position(cfg, root, monkeypatch, tmp_path):
    pgn = str(root / "fixtures" / "pgn" / "single.pgn")
    code, _, ran = drive(cfg, ["", "", "", "", "", "correggi", "pgn", pgn, "3w", "s"], monkeypatch, tmp_path)
    assert code == 0 and ran[0][0].plies == 5


def test_pasted_pgn_until_dot(cfg, monkeypatch, tmp_path):
    lines = ['[Event "x"]', "", "1.e4 c5 2.Nf3 d6 3.d4 cxd4", "4.Nxd4 Nf6 5.Nc3 a6 *", "."]
    code, _, ran = drive(cfg, ["", "", "", "", "pgn"] + lines + ["", "s"], monkeypatch, tmp_path)
    assert code == 0 and ran[0][0].fen == NAJDORF


def test_too_many_invalid_answers(cfg, monkeypatch, tmp_path):
    code, _, ran = drive(cfg, ["verde", "rosso", "blu"], monkeypatch, tmp_path)
    assert code == 3 and not ran


def test_both_colors_with_one_elo_each(cfg, monkeypatch, tmp_path):
    code, said, ran = drive(cfg, ["entrambi", "2000", "", "", "5", "", "s"], monkeypatch, tmp_path)
    v = ran[0][1]
    assert code == 0 and v["color"] == "both" and v["elo_white"] == v["elo_black"] == 2000 and v["detail"] == 5
    assert any("Elo del Nero [2000]" in s for s in said)


def test_elo_from_pgn_tags(cfg, monkeypatch, tmp_path):
    lines = ['[Event "x"]', '[WhiteElo "2210"]', '[BlackElo "1980"]', "",
             "1.e4 c5 2.Nf3 d6 3.d4 cxd4", "4.Nxd4 Nf6 5.Nc3 a6 *", "."]
    answers = ["nero", "", "", "", "pgn"] + lines + ["", "s", "lichess", "s"]
    code, said, ran = drive(cfg, answers, monkeypatch, tmp_path)
    v = ran[0][1]
    assert code == 0 and v["elo"] == 1980 and v["opp_elo"] == 2210 and v["elo_scale"] == "lichess"
    assert any("Elo Bianco 2210 e Nero 1980" in s for s in said)
    prof = yaml.safe_load((tmp_path / "profile.yaml").read_text())
    assert prof["elo"] == 1900 and prof["elo_scale"] == "fide"        # the tags are not the user's profile


def test_elo_tags_refused(cfg, monkeypatch, tmp_path):
    lines = ['[WhiteElo "2210"]', '[BlackElo "1980"]', "", "1.e4 c5 2.Nf3 d6 3.d4 cxd4", "4.Nxd4 Nf6 5.Nc3 a6 *", "."]
    code, _, ran = drive(cfg, ["", "", "", "", "pgn"] + lines + ["", "n", "s"], monkeypatch, tmp_path)
    assert code == 0 and ran[0][1]["elo"] == 1900 and ran[0][1].get("opp_elo") is None
