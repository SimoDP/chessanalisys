"""``pytest -m engines --record``: regenerate the recorded engine fixtures (Appendix G)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.engines


def test_record_fixtures(cfg, request):
    if not request.config.getoption("--record"):
        pytest.skip("usa --record per rigenerare le registrazioni")
    from chessanalyst.golden.record import record_fixtures

    import os

    groups = os.environ.get("CHESSANALYST_RECORD_GROUPS")       # e.g. "najdorf" (comma separated)
    written = record_fixtures(cfg, groups=groups.split(",") if groups else None,
                              extend=bool(os.environ.get("CHESSANALYST_RECORD_EXTEND")))
    assert all(p.stat().st_size > 0 for p in written)
