"""§3-bis reference values (full AC-30 in M1a)."""

from __future__ import annotations

import pytest

from chessanalyst import elo


@pytest.mark.parametrize("fide,lichess", [(1500, 1700), (1900, 2025), (2400, 2400), (900, 1200), (2700, 2700)])
def test_fide_to_lichess(cfg, fide, lichess):
    assert elo.fide_to_lichess(fide, cfg) == lichess


def test_inverse(cfg):
    assert elo.lichess_to_fide(2025, cfg) == 1900


@pytest.mark.parametrize("value,band", [(1199, "lt1200"), (1200, "1200_1600"), (1599, "1200_1600"),
                                        (1600, "1600_2000"), (2399, "2000_2400"), (2400, "ge2400")])
def test_bands(cfg, value, band):
    assert elo.band_of(value, cfg) == band


@pytest.mark.parametrize("value,anchor", [(1749, "1500"), (1750, "1900"), (2149, "1900"), (2150, "2400")])
def test_anchors(cfg, value, anchor):
    assert elo.anchor_of(value, cfg) == anchor
