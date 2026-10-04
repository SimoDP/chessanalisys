"""AC-31: candidate selection (§3-ter.3, D-63)."""

from __future__ import annotations

from chessanalyst.explore.select import BandSel, RootRow, select_candidates

EVALS = [40, 38, 36, 34, 30, 25, 20, 10]
UCIS = [f"m{i}" for i in range(1, 9)]


def rows(evals=EVALS):
    return [RootRow(u, u, e, "e0", i + 1) for i, (u, e) in enumerate(zip(UCIS, evals))]


def bs(cfg, band):
    bp = cfg.thresholds.band_params[band]
    return BandSel(bp.K, bp.explained_min, bp.listed_max, bp.L_max, bp.A)


def test_mt_inside_first_k(cfg):
    sel = select_candidates(rows(), [], {"m1": 0.5, "m2": 0.1}, bs(cfg, "ge2400"))
    assert sel.mt == "m1" and sel.explained == ["m1", "m2", "m3", "m4", "m5"]


def test_mt_outside_k_within_lmax_replaces_last(cfg):
    sel = select_candidates(rows(), [], {"m6": 0.6}, bs(cfg, "ge2400"))   # loss 15 ≤ 25
    assert sel.explained == ["m1", "m2", "m3", "m4", "m6"]


def test_mt_beyond_lmax_still_enters(cfg):
    sel = select_candidates(rows(), [], {"m8": 0.6}, bs(cfg, "ge2400"))   # loss 30 > 25
    assert len(sel.explained) == 5 and "m8" in sel.explained and "m5" not in sel.explained


def test_mt_without_evaluation(cfg):
    sel = select_candidates(rows(), [], {"zz": 0.9}, bs(cfg, "ge2400"))
    assert "maia_top_unevaluated" in sel.warnings
    assert sel.explained == ["m1", "m2", "m3", "m4", "m5"]


def test_mt_from_e4(cfg):
    e4 = [RootRow("x9", "x9", 12, "e4", None)]
    sel = select_candidates(rows(), e4, {"x9": 0.7}, bs(cfg, "ge2400"))
    assert "x9" in sel.explained and sel.order[-2:] == ["x9", "m8"]


def test_fill_up_to_explained_min(cfg):
    # only m1 within L_max (others lose > 40): K = 3, explained_min = 2 at 1200_1600
    sel = select_candidates(rows([40, -10, -20, -30, -40, -50, -60, -70]), [], {"m1": 0.9}, bs(cfg, "1200_1600"))
    assert sel.explained == ["m1", "m2"]


def test_natural_seventh_move_by_band(cfg):
    pol = {"m1": 0.30, "m7": 0.40}   # m7: loss 20, seventh by evaluation
    low = select_candidates(rows(), [], {**pol, "m1": 0.45}, bs(cfg, "1200_1600"))
    # mt = m1; m7 enters through pre = -20 + 0.5*100*0.40 = 0 (top K=3 by pre)
    assert "m7" in low.explained
    high = select_candidates(rows(), [], {**pol, "m1": 0.45}, bs(cfg, "ge2400"))
    assert "m7" not in high.explained          # A = 0: pre = -loss


def test_tie_on_pre_uses_evaluation_then_rank(cfg):
    sel = select_candidates(rows([40, 40, 40, 30, 30, 30, 20, 10]), [], {}, bs(cfg, "lt1200"))
    assert sel.explained == ["m1", "m2"]


def test_ids_by_evaluation(cfg):
    sel = select_candidates(rows([30, 40, 35, 10, 5, 0, -5, -10]), [], {"m1": 0.2}, bs(cfg, "1600_2000"))
    assert sel.cid("m2") == "C1" and sel.cid("m3") == "C2" and sel.cid("m1") == "C3"
    assert sel.listed == ["m2", "m3", "m1", "m4", "m5", "m6", "m7", "m8"]
