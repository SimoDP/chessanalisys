"""M2: Syzygy probe in the pack and results in words (§3.3, D-62, OQ-M2-4)."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.syzygy import RecordedTablebase, tablebase_entry
from chessanalyst.engines.types import CP_CLAMP
from chessanalyst.pack.tables import ev_cell
from chessanalyst.render.format_it import tb_outcome

LUCENA = chess.Board("1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1")


def test_entry_from_the_user_point_of_view():
    assert tablebase_entry({"wdl": 2, "dtz": 15}, True) == {"wdl": 2, "dtz": 15, "result_text_key": "win"}
    assert tablebase_entry({"wdl": 2, "dtz": 15}, False) == {"wdl": -2, "dtz": -15, "result_text_key": "loss"}
    assert tablebase_entry({"wdl": 1, "dtz": 101}, True)["result_text_key"] == "cursed_win"
    assert tablebase_entry({"wdl": 0, "dtz": 0}, False)["result_text_key"] == "draw"


def test_recorded_tablebase_covers_only_small_positions():
    tb = RecordedTablebase({LUCENA.epd(en_passant="legal"): {"wdl": 2, "dtz": 15}}, 5)
    assert tb.probe(LUCENA) == {"wdl": 2, "dtz": 15}
    assert tb.probe(chess.Board()) is None


@pytest.mark.parametrize("cp,mate,out", [(CP_CLAMP, None, "win"), (-CP_CLAMP, None, "loss"), (0, None, "draw"),
                                         (3, None, "draw"), (0, 4, "win"), (0, -2, "loss")])
def test_outcome_classes(cp, mate, out):
    assert tb_outcome(cp, mate, CP_CLAMP) == out


def test_table_cells_in_words(cfg):
    assert ev_cell(cfg, CP_CLAMP, None, True) == "vinta" and ev_cell(cfg, 0, None, True) == "patta"
    assert ev_cell(cfg, 37, None, False) == "+0,37"


def _tb_pack(key: str = "win") -> dict:
    fen = LUCENA.fen()
    line = lambda san, uci, cp: {"rank": 1, "san": san, "uci": uci, "eval_white_cp": cp, "mate_white": None,  # noqa: E731
                                 "eval_user_cp": cp, "mate_user": None, "wdl_user": [1000, 0, 0], "pv": [san]}
    return {
        "position": {"fen": fen}, "user": {"color": "w", "elo_declared": 1900, "opp_elo_declared": 1900,
                                           "elo_scale": "fide"},
        "engine": {"candidates": [
            {"id": "C1", "san": "Rc4", "uci": "c1c4", "eval_user_cp": CP_CLAMP, "mate_user": None, "loss_cp": 0,
             "p_user": 0.2, "p_up": None},
            {"id": "C2", "san": "Rh1", "uci": "c1h1", "eval_user_cp": 0, "mate_user": None, "loss_cp": CP_CLAMP,
             "p_user": 0.1, "p_up": None}],
            "replies": [], "pvs": [], "root": {"eval_user_cp": CP_CLAMP, "mate_user": None, "wdl_user": [1000, 0, 0]}},
        "nodes": [{"id": "N1", "fen": fen, "citable": True, "root_moves": None, "maia": None,
                   "multipv": [line("Rc4", "c1c4", CP_CLAMP), line("Rh1", "c1h1", 0)]}],
        "maia": {"p_up_bucket": None}, "opening": None,
        "tablebase": {"wdl": 2, "dtz": 15, "result_text_key": key},
    }


def test_tokens_render_the_result_in_words(cfg):
    from chessanalyst.verify.resolve import ResolveError, Resolver

    r = Resolver(_tb_pack(), cfg.wording)
    words = cfg.wording["tablebase"]
    assert r.resolve("{{ev:N1}}").text == words["results"]["win"]
    assert r.resolve("{{ev:C2}}").text == words["results"]["draw"]
    assert r.resolve("{{loss:C2}}").text == words["loss_decisive"]
    assert r.resolve("{{loss:C1}}").text == words["loss_none"]
    assert r.resolve("{{ev:Rh1@N1}}").text == words["results"]["draw"]
    # the root result comes from the probe, including the 50-move-rule nuances
    assert Resolver(_tb_pack("cursed_win"), cfg.wording).resolve("{{ev:N1}}").text == words["results"]["cursed_win"]
    with pytest.raises(ResolveError) as e:
        r.resolve("{{pct:root.win}}")
    assert e.value.code == "V02"
    assert not any(ch.isdigit() for ch in words["results"].values() for ch in ch)


def test_focus_squares_c5():
    from chessanalyst.features.model import Feature
    from chessanalyst.pack.builder import focus_squares

    b = chess.Board("r1bqkb1r/ppp2ppp/2n5/3np1N1/2B5/8/PPPP1PPP/RNBQK2R w KQkq - 0 6")   # Fried Liver
    feats = [Feature("hanging_piece", "b", ["d5"], None), Feature("doubled_pawn", "w", ["c2", "c3"], None)]
    sq = focus_squares(b, feats, [["Nxf7", "Kxf7", "Qf3+", "Ke6", "Nc3"], ["d4", "exd4", "O-O"]], 4)
    # d5 (witness); g5 knight, e8 king, d1 queen in the first four plies of the first line; in the
    # second one the pawns do not count and castling moves king and rook; Nc3 is the fifth ply
    assert sq == ["d1", "d5", "e1", "e8", "g5", "h1"]
