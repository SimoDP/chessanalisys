from __future__ import annotations

import json

import chess

from chessanalyst.engines.openings import OpeningIndex, build_index, parse_tsv

TSV = (
    "eco\tname\tpgn\n"
    "B90\tSicilian Defense: Najdorf Variation\t1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6\n"
    "B20\tSicilian Defense\t1. e4 c5\n"
    "B20\tSicilian Defense: Alias\t1. e4 c5\n"
    "B50\tSicilian Defense: Longer\t1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6\n"
)


def test_index_by_epd_and_ties():
    idx = OpeningIndex(build_index(parse_tsv(TSV)))
    najdorf = chess.Board("rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6")
    assert idx.lookup_epd(najdorf)["eco"] == "B90"     # equal plies: file order wins
    b = chess.Board(); b.push_san("e4"); b.push_san("c5")
    assert idx.lookup_epd(b)["name"] == "Sicilian Defense"
    assert idx.lookup_epd(chess.Board()) is None


def test_real_index_knows_najdorf(cfg):
    path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    if not path.is_file():
        import pytest
        pytest.skip("indice delle aperture non costruito (scripts/setup_engines.py)")
    idx = OpeningIndex.load(path)
    entry = idx.lookup_epd(chess.Board("rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"))
    assert entry["eco"] == "B90" and "Najdorf" in entry["name"]
