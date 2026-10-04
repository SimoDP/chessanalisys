"""AC-09 on fixtures/golden_nodes.json (produced by `chessanalyst golden --data`)."""

from __future__ import annotations

import json

import pytest

from chessanalyst.golden import raw_claims as rc
from chessanalyst.golden.data import _node_index, ac09


@pytest.mark.parametrize("name", ["golden_nodes.json", "golden_nodes_sf19.json"])   # M0 (Stockfish 16), D-66
def test_ac09(root, cfg, name):
    path = root / "fixtures" / name
    if not path.is_file():
        pytest.skip("fixtures/golden_nodes.json assente: eseguire `chessanalyst golden --data`")
    data = json.loads(path.read_text(encoding="utf-8"))
    idx = _node_index(data)
    assert idx[()]["result"].multipv >= cfg.thresholds.golden.ac09_top_n
    result = ac09(cfg, idx)
    assert result["passed"], result["rows"]


@pytest.mark.parametrize("name", ["golden_nodes.json", "golden_nodes_sf19.json"])
def test_all_golden_nodes_present(root, name):
    path = root / "fixtures" / name
    if not path.is_file():
        pytest.skip("fixtures/golden_nodes.json assente")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert [tuple(n["path"]) for n in data["nodes"]] == [p for p, _ in rc.GOLDEN_NODES]
