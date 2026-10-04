"""AC-18 (pack): saturated Elo → confidence low, p_up null, no improbable_error."""

from __future__ import annotations

import pytest

from tests.recorded import recorded_pack


@pytest.mark.parametrize("elo", [1900, 2400])
def test_saturated(cfg, root, elo):
    pack, _, _ = recorded_pack(cfg, root, "najdorf", "w", elo)
    m = pack["maia"]
    assert m["saturated"] and m["confidence"] == "low" and m["bucket_user"] == 10
    assert m["p_up_elo"] is None and m["p_up_bucket"] is None
    cands = pack["engine"]["candidates"]
    assert all(c["p_up"] is None for c in cands)
    assert all(c["category"] != "improbable_error" for c in cands)
    assert "maia_low_confidence_header" in pack["warnings"]
    assert pack["tables"]["T1"]["footnote"] == cfg.wording["fixed"]["maia_low_confidence_table"]
    assert any(c["header"].endswith("*") for c in pack["tables"]["T1"]["columns"])
    plan = {s["id"]: s for s in pack["section_plan"]}
    for sid in ("S06", "S08"):
        assert plan[sid]["maia_low_confidence"] == plan[sid]["required"]


def test_not_saturated_at_1500(cfg, root):
    pack, _, _ = recorded_pack(cfg, root, "najdorf", "w", 1500)
    m = pack["maia"]
    assert not m["saturated"] and m["confidence"] == "normal"
    assert m["p_up_elo"] == 2000 and m["p_up_bucket"] == "top"
    assert all(c["p_up"] is not None for c in pack["engine"]["candidates"])
    assert pack["tables"]["T1"]["footnote"] is None
