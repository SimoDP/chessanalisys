"""Usefulness test, phase 4 (D-77): in pawn and rook endings the facts are the ending's (key squares,
opposition, king moves that keep the result, the rook in front of its pawn), not the middlegame's; with the
tablebase the verdict is the exact result («vinta», «patta»), never «matto forzato» or «vantaggio».
Packs from the test: 10 (only 60.Kd6 wins) and 11 (the Black king must stay on h7 or f6)."""

from __future__ import annotations

import json

import chess

from chessanalyst import bench
from chessanalyst.features.endgame import endgame_kind, has_opposition, key_squares
from chessanalyst.llm.prompt_kp import _legend
from chessanalyst.plan.keypoints import key_points
from chessanalyst.plan.outline import outline_pack
from chessanalyst.verify.checker import Checker
from chessanalyst.verify.resolve import Resolver


def _names(sqs):
    return sorted(chess.square_name(s) for s in sqs)


def test_kind():
    assert endgame_kind(chess.Board("8/5k2/8/3K4/4P3/8/8/8 w - - 0 60")) == "pawn"
    assert endgame_kind(chess.Board("R7/P4pk1/6p1/7p/7P/6P1/r4PK1/8 b - - 0 45")) == "rook"
    assert endgame_kind(chess.Board("8/8/4r3/8/5k2/R4p2/8/5K2 w - - 2 92")) == "rook"
    assert endgame_kind(chess.Board("8/5k2/8/3K4/4P3/8/5n2/8 w - - 0 60")) is None
    assert endgame_kind(chess.Board()) is None


def test_key_squares():
    assert _names(key_squares(chess.E4, chess.WHITE)) == ["d6", "e6", "f6"]
    assert _names(key_squares(chess.E5, chess.WHITE)) == ["d6", "d7", "e6", "e7", "f6", "f7"]
    assert _names(key_squares(chess.E5, chess.BLACK)) == ["d3", "e3", "f3"]
    assert _names(key_squares(chess.A4, chess.WHITE)) == ["b7", "b8"]
    assert _names(key_squares(chess.H6, chess.BLACK)) == ["g1", "g2"]


def test_opposition():
    b = chess.Board("8/4k3/8/4K3/4P3/8/8/8 b - - 0 1")
    assert has_opposition(b, chess.WHITE) and not has_opposition(b, chess.BLACK)
    assert not has_opposition(chess.Board("8/4k3/8/4K3/4P3/8/8/8 w - - 0 1"), chess.WHITE)


def _pack(root, name):
    return json.loads((root / "fixtures" / "prova" / f"{name}.pack.json").read_text(encoding="utf-8"))


def _kp(cfg, pack):
    return {k["type"]: k for k in key_points(cfg, pack)}


def test_pawn_ending_facts(cfg, root):
    kp = _kp(cfg, _pack(root, "pawn_ending_kd6_w_1400"))
    rec = kp["recommendation"]["facts"]
    assert rec["san"] == "Kd6" and rec["only_move"] and rec["key_square"]["square"] == "d6"
    items = kp["plan"]["facts"]["items"]
    assert {"key": "key_squares", "of": "user", "pawn": "pedone bianco in e4", "squares": ["d6", "e6", "f6"],
            "king_on_it": False} in items
    moves = next(i for i in items if i["key"] == "king_moves")
    assert moves["hold"] == ["d6"] and "d4" in moves["lose"]
    assert not {i["key"] for i in items} & {"outpost", "pawn_majority", "open_file_to_king", "pinned",
                                             "king_square", "pawn_island_count"}
    assert "opposizione" in kp["reasoning"]["facts"]["topics"]


def test_rook_ending_facts(cfg, root):
    kp = _kp(cfg, _pack(root, "rook_a7_b_1600"))
    items = kp["plan"]["facts"]["items"]
    assert {"key": "rook_in_front", "of": "opp", "pawn": "pedone bianco in a7", "rook": "torre bianca in a8"} in items
    moves = next(i for i in items if i["key"] == "king_moves")
    assert set(moves["hold"]) == {"h7", "f6"} and moves["lose"] == ["h6"]
    assert not {i["key"] for i in items} & {"pinned", "pawn_island_count", "isolated_pawn", "key_squares"}


def test_tablebase_words(cfg, root):
    pack = _pack(root, "pawn_ending_kd6_w_1400")
    r = Resolver(pack, cfg.wording)
    second = _kp(cfg, pack)["recommendation"]["facts"]["second"]["ref"]
    assert r.resolve("{{loss:%s}}" % second).text == "la vittoria"          # «60.Kd4 perde la vittoria»
    legend = " ".join(_legend(cfg, '"mate_plus"', pack["tablebase"]))
    assert "posizione vinta per te" in legend and "matto" not in legend


def _verdict_errors(cfg, pack, text):
    resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "input": {
        "schema_version": "1", "notes": [], "sections": [{"id": "S01", "blocks": [
            {"type": "p", "source": "mixed", "text": text, "assertions": []}]}]}}]}
    return [e.text for e in Checker(cfg, pack, words_floor=False).check(resp).errors if e.code == "V12"]


def test_v12_on_the_tablebase_verdict(cfg, root):
    draw = outline_pack(cfg, bench.load_pack(cfg, bench.load_spec(cfg, "rook_checks_b_1700")))
    assert "vantaggio" in _verdict_errors(cfg, draw, "La posizione è patta ({{ev:N1}}), ma hai un piccolo vantaggio.")
    assert not _verdict_errors(cfg, draw, "La posizione è patta ({{ev:N1}}): gli scacchi della torre bastano.")
    win = outline_pack(cfg, _pack(root, "pawn_ending_kd6_w_1400"))
    assert "matto" in _verdict_errors(cfg, win, "Hai un matto forzato ({{ev:N1}}).")


def test_v12_on_an_invented_opposition(cfg, root):
    pack = outline_pack(cfg, _pack(root, "pawn_ending_kd6_w_1400"))
    sec = next(k["section"] for k in pack["key_points"] if k["type"] == "recommendation")
    resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "input": {
        "schema_version": "1", "notes": [], "sections": [{"id": sec, "blocks": [
            {"type": "p", "source": "mixed", "text": "Gioca {{mv:C1}} ({{ev:C1}}) e prendi l'opposizione.",
             "assertions": []}]}]}}]}
    errs = [e.text for e in Checker(cfg, pack, words_floor=False).check(resp).errors if e.code == "V12"]
    assert errs == ["prendi l'opposizione"]                  # after Kd6 the kings are on d6 and f7
