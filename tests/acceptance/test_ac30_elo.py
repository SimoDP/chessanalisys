"""AC-30: Elo conversion, bands and anchors (§3-bis)."""

from __future__ import annotations

import pytest

from chessanalyst import elo


@pytest.mark.parametrize("fide,lichess", [(1500, 1700), (1900, 2025), (2400, 2400), (900, 1200)])
def test_reference_values(cfg, fide, lichess):
    assert elo.fide_to_lichess(fide, cfg) == lichess


def test_inverse_and_lichess_scale(cfg):
    assert elo.lichess_to_fide(2025, cfg) == 1900
    e = elo.resolve(2025, "lichess", cfg)
    assert (e.ref_fide, e.maia) == (1900, 2025)


@pytest.mark.parametrize("v,band,anchor", [
    (1199, "lt1200", "1500"), (1200, "1200_1600", "1500"), (1599, "1200_1600", "1500"), (1600, "1600_2000", "1500"),
    (1749, "1600_2000", "1500"), (1750, "1600_2000", "1900"), (2149, "2000_2400", "1900"),
    (2150, "2000_2400", "2400"), (2399, "2000_2400", "2400"), (2400, "ge2400", "2400"),
])
def test_boundaries(cfg, v, band, anchor):
    assert elo.band_of(v, cfg) == band
    assert elo.anchor_of(v, cfg) == anchor
