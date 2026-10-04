"""AC-14: a second identical run makes no engine calls and gives the same
pack.json (except created_utc); reuse and replacement rules of the cache."""

from __future__ import annotations

from chessanalyst.engines.cache import Cache
from tests.recorded import recorded_pack


def strip(pack: dict) -> dict:
    return {k: v for k, v in pack.items() if k != "created_utc"}


def test_second_run_uses_only_the_cache(cfg, root):
    cache = Cache(":memory:")
    first, eng1, maia1 = recorded_pack(cfg, root, "najdorf", "w", 1900, cache=cache)
    assert eng1.calls > 0 and maia1.calls > 0
    second, eng2, maia2 = recorded_pack(cfg, root, "najdorf", "w", 1900, cache=cache)
    assert eng2.calls == 0 and maia2.calls == 0
    assert strip(first) == strip(second)


def test_lighter_profile_reuses_deeper_results(cfg, root):
    cache = Cache(":memory:")
    recorded_pack(cfg, root, "najdorf", "w", 1900, profile="deep", cache=cache)
    pack, eng, _ = recorded_pack(cfg, root, "najdorf", "w", 1900, profile="standard", cache=cache)
    root_node = pack["nodes"][0]
    assert len(root_node["multipv"]) == cfg.exploration.profiles["standard"].multipv.root
    assert root_node["depth"] >= cfg.exploration.profiles["deep"].dmin.root
