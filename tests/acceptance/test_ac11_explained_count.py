"""AC-11: explained candidates between explained_min and K of the band; with
the opponent to move at most K replies."""

from __future__ import annotations

import pytest

from tests.recorded import recorded_pack


@pytest.mark.parametrize("elo", [1500, 1900, 2400])
def test_explained_count(cfg, root, elo):
    pack, _, _ = recorded_pack(cfg, root, "najdorf", "w", elo)
    bp = cfg.thresholds.band_params[pack["user"]["band"]]
    n = sum(c["explained"] for c in pack["engine"]["candidates"])
    assert bp.explained_min <= n <= bp.K
    assert sum(c["listed"] for c in pack["engine"]["candidates"]) <= bp.listed_max


def test_replies_at_most_k(cfg, root):
    pack, _, _ = recorded_pack(cfg, root, "najdorf_after_be3", "w", 1900)
    bp = cfg.thresholds.band_params[pack["user"]["band"]]
    assert 1 <= len(pack["engine"]["replies"]) <= bp.K
