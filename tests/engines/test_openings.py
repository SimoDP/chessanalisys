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


# -- M2: lookup by sequence (§3.3) -------------------------------------------------------

SEQ_TSV = (
    "eco\tname\tpgn\n"
    "C55\tItalian Game: Two Knights Defense\t1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6\n"
    "C57\tItalian Game: Two Knights Defense, Knight Attack\t1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5\n"
    "C57\tItalian Game: Two Knights Defense, Fried Liver Attack\t1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 6. Nxf7\n"
    "C50\tTransposed name\t1. Nf3 Nc6 2. e4 e5 3. Bc4 Nf6\n"
)


def _seq_index():
    seqs: dict = {}
    idx = build_index(parse_tsv(SEQ_TSV), seqs)
    return OpeningIndex(idx, seqs)


def _play(*sans):
    b = chess.Board()
    for s in sans:
        b.push_san(s)
    return b


def test_longest_prefix_of_the_game():
    idx = _seq_index()
    b = _play("e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5", "d5", "exd5", "Nxd5")
    entry, how = idx.lookup(b)
    assert how == "sequence" and entry["name"] == "Italian Game: Two Knights Defense, Knight Attack"
    assert idx.lookup_epd(b) is None          # the position itself is not the end of a line


def test_sequence_follows_the_move_order_not_the_position():
    idx = _seq_index()
    b = _play("Nf3", "Nc6", "e4", "e5", "Bc4", "Nf6")
    entry, how = idx.lookup(b)
    assert (entry["name"], how) == ("Transposed name", "sequence")
    # without history (FEN) the same position is found by EPD: the row with more plies, ties by file order
    entry, how = idx.lookup(chess.Board(b.fen()))
    assert how == "epd" and entry["name"] == "Italian Game: Two Knights Defense"


def test_custom_start_falls_back_to_epd():
    idx = _seq_index()
    start = _play("e4", "e5", "Nf3", "Nc6")
    b = chess.Board(start.fen())
    b.push_san("Bc4"); b.push_san("Nf6")
    assert idx.lookup_sequence(b) is None
    assert idx.lookup(b)[1] == "epd"


def test_sequences_written_next_to_the_index(tmp_path):
    from chessanalyst.engines.openings import write_index

    seqs: dict = {}
    idx = build_index(parse_tsv(SEQ_TSV), seqs)
    write_index(idx, tmp_path / "openings_index.json", seqs)
    loaded = OpeningIndex.load(tmp_path / "openings_index.json")
    assert loaded.lookup(_play("e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5", "h6"))[1] == "sequence"


# -- D-76: name from the pawn structure, for positions past the book --------------------

NAJDORF_BE2 = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP1BPPP/R1BQK2R b KQkq - 1 6"


def test_structure_names_a_position_just_past_the_book():
    idx = OpeningIndex(build_index(parse_tsv(TSV)), structure_max_piece_diff=4)
    entry, by = idx.lookup(chess.Board(NAJDORF_BE2))
    assert (entry["eco"], by) == ("B90", "structure")


def test_structure_needs_the_same_pawns_and_few_piece_moves():
    idx = OpeningIndex(build_index(parse_tsv(TSV)), structure_max_piece_diff=1)
    assert idx.lookup(chess.Board(NAJDORF_BE2)) is None                    # the bishop move counts twice
    idx = OpeningIndex(build_index(parse_tsv(TSV)), structure_max_piece_diff=4)
    pawn_moved = chess.Board(NAJDORF_BE2)
    pawn_moved.push_san("e6")
    assert idx.lookup_structure(pawn_moved) is None
    assert OpeningIndex(build_index(parse_tsv(TSV))).lookup(chess.Board(NAJDORF_BE2)) is None   # disabled
