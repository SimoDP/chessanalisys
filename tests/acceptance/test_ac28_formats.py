"""AC-28: number formats of §9-bis.7 and the evaluation bands of §6.4."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.render.format_it import fmt_eval, fmt_loss, fmt_pct, fmt_wdl, numbered
from chessanalyst.verify.assertions import eval_band_of, maia_band_of


@pytest.mark.parametrize("cp,text", [(37, "+0,37"), (-15, "-0,15"), (0, "0,00"), (4, "+0,04"), (250, "+2,50"),
                                     (-250, "-2,50"), (1, "+0,01"), (-1, "-0,01")])
def test_eval(cp, text):
    assert fmt_eval(cp) == text


def test_mate():
    assert fmt_eval(0, 3, opp_name="il Nero") == "matto in 3 per te"
    assert fmt_eval(0, -2, opp_name="il Nero") == "matto in 2 per il Nero"
    assert fmt_eval(0, 3, table=True) == "#3" and fmt_eval(0, -3, table=True) == "-#3"


def test_loss():
    assert fmt_loss(15) == "0,15" and fmt_loss(0) == "0,00" and fmt_loss(186) == "1,86"
    assert fmt_loss(30, mate=True) == "decisiva"


@pytest.mark.parametrize("p,text", [(0.183, "18%"), (0.004, "<1%"), (0, "0%"), (0.0049, "<1%"), (0.005, "1%"),
                                    (0.996, ">99%"), (1.0, "100%"), (0.125, "13%"), (0.5, "50%")])
def test_pct(p, text):
    assert fmt_pct(p) == text


def test_wdl():
    assert fmt_wdl(920) == "92%" and fmt_wdl(5) == "1%" and fmt_wdl(950) == "95%"


def test_numbered():
    b = chess.Board("rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6")
    assert numbered(b, ["Be3", "e5", "Nb3"]) == "6.Be3 e5 7.Nb3"
    b.push_san("Be3")
    assert numbered(b, ["e5", "Nb3"]) == "6...e5 7.Nb3"


BOUNDS = [(14, "equal"), (-14, "equal"), (15, "slight_plus"), (-15, "slight_minus"), (49, "slight_plus"),
          (-49, "slight_minus"), (50, "small_plus"), (-50, "small_minus"), (99, "small_plus"), (-99, "small_minus"),
          (100, "clear_plus"), (-100, "clear_minus"), (199, "clear_plus"), (-199, "clear_minus"),
          (200, "decisive_plus"), (-200, "decisive_minus"), (0, "equal")]


@pytest.mark.parametrize("cp,band", BOUNDS)
def test_eval_band_bounds(cfg, cp, band):
    assert eval_band_of(cp, None, cfg.wording["eval_bands"]) == band


def test_eval_bands_have_no_holes_or_overlaps(cfg):
    for cp in range(-1000, 1001):
        eval_band_of(cp, None, cfg.wording["eval_bands"])          # exactly one band, never raises
    assert eval_band_of(0, 4, cfg.wording["eval_bands"]) == "mate_plus"
    assert eval_band_of(0, -1, cfg.wording["eval_bands"]) == "mate_minus"


@pytest.mark.parametrize("p,band", [(0.0, "very_unlikely"), (0.0299, "very_unlikely"), (0.03, "unlikely"),
                                    (0.1, "possible"), (0.25, "frequent"), (0.45, "very_frequent"),
                                    (1.0, "very_frequent")])
def test_maia_bands(cfg, p, band):
    assert maia_band_of(p, cfg.wording["maia_bands"]) == band
