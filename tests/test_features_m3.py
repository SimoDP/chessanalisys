"""The «M3» features of §5.1, one position per definition."""

from __future__ import annotations

import chess

from chessanalyst.features.profile import m3_features


def feats(cfg, fen, pv=()):
    return [(f.key, f.side, f.squares, f.value) for f in m3_features(chess.Board(fen), cfg, list(pv))]


def keyed(cfg, fen, key, pv=()):
    return [f for f in feats(cfg, fen, pv) if f[0] == key]


def test_king_zone(cfg):
    # black king e8: the white knight on c7 attacks e8; the rook a8 defends d8
    assert keyed(cfg, "r3k3/2N5/8/8/8/8/8/4K3 b - - 0 1", "king_zone_attackers") == [
        ("king_zone_attackers", "b", ["c7"], 1)]
    assert keyed(cfg, "r3k3/2N5/8/8/8/8/8/4K3 b - - 0 1", "king_zone_defenders") == [
        ("king_zone_defenders", "b", ["a8"], 1)]


def test_mobility_and_inactive(cfg):
    # the knight a1 has b3 and c2; c2 is attacked by the black pawn b3? no: by d3. Mobility counts
    # pseudo-legal moves to squares not attacked by enemy pawns
    fen = "4k3/8/8/8/8/3p4/8/N3K3 w - - 0 1"
    mob = keyed(cfg, fen, "piece_mobility")
    assert mob == [("piece_mobility", "w", ["a1"], {"a1": 1})]
    assert keyed(cfg, fen, "inactive_piece") == [("inactive_piece", "w", ["a1"], None)]


def test_bishop_diagonal_open(cfg):
    assert keyed(cfg, "4k3/8/8/8/8/8/8/B3K3 w - - 0 1", "bishop_diagonal_open") == [
        ("bishop_diagonal_open", "w", ["a1"], None)]
    assert keyed(cfg, "4k3/8/8/8/8/8/1P6/B3K3 w - - 0 1", "bishop_diagonal_open") == []


def test_skewer(cfg):
    # the bishop b2 checks the king d4 with the rook h8 behind, undefended
    assert keyed(cfg, "7r/8/8/8/3k4/8/1B6/4K3 w - - 0 1", "skewer") == [
        ("skewer", "b", ["b2", "d4", "h8"], None)]
    # defended rook: no skewer
    assert keyed(cfg, "6rr/8/8/8/3k4/8/1B6/4K3 w - - 0 1", "skewer") == []


def test_fork(cfg):
    assert keyed(cfg, "r3k3/2N5/8/8/8/8/8/4K3 b - - 0 1", "fork") == [("fork", "b", ["c7", "a8", "e8"], None)]
    # the king can take the knight: no fork
    assert keyed(cfg, "r7/2N1k3/8/8/8/8/8/4K3 b - - 0 1", "fork") == []


def test_overloaded(cfg):
    # the black queen d8 is the only defender of the attacked rook d6 and knight c7... both attacked
    fen = "3qk3/2n5/3r4/8/8/8/2R5/3RK3 w - - 0 1"
    assert keyed(cfg, fen, "overloaded_piece") == [("overloaded_piece", "b", ["d8", "c7", "d6"], None)]


def test_tempo_count(cfg):
    fen = "4k3/8/8/8/8/8/3q4/R3K3 w - - 0 1"
    # Kxd2 is a capture (white), then a quiet king move by black
    assert keyed(cfg, fen, "tempo_count", ["Kxd2", "Kd7"]) == [("tempo_count", "w", [], 1)]


def test_minority_attack(cfg):
    fen = "4k3/ppp5/8/8/8/8/1P1P4/1R2K3 w - - 0 1"
    # white has b2 only on a-c: one pawn, not two
    assert keyed(cfg, fen, "minority_attack") == []
    fen = "4k3/ppp5/8/8/8/8/PP6/1R2K3 w - - 0 1"
    assert keyed(cfg, fen, "minority_attack") == [("minority_attack", "w", ["b1"], None)]


def test_space_advantage(cfg):
    fen = "4k3/8/8/2PPP3/8/8/8/4K3 w - - 0 1"
    # c5 d5 e5 attack b6 d6 c6 e6 d6 f6 -> {b6, c6, d6, e6, f6} = 5 squares in Black's half
    assert keyed(cfg, fen, "space_advantage") == [("space_advantage", "w", [], 5)]


def test_file_control(cfg):
    assert keyed(cfg, "4k3/8/8/8/8/8/8/3RK3 w - - 0 1", "file_control") == [("file_control", "w", ["d1"], "d")]
    assert keyed(cfg, "3rk3/8/8/8/8/8/8/3RK3 w - - 0 1", "file_control") == []


def test_pawn_chain(cfg):
    fen = "4k3/8/8/4P3/3P4/2P5/8/4K3 w - - 0 1"
    assert keyed(cfg, fen, "pawn_chain") == [("pawn_chain", "w", ["c3", "d4", "e5"], None)]
    assert keyed(cfg, "4k3/8/8/8/3P4/2P5/8/4K3 w - - 0 1", "pawn_chain") == []


def test_najdorf_root(cfg, root):
    fen = (root / "fixtures" / "positions" / "najdorf.fen").read_text().strip()
    keys = {f[0] for f in feats(cfg, fen)}
    assert {"piece_mobility", "king_zone_defenders", "inactive_piece"} <= keys
    assert not keys & {"fork", "skewer", "overloaded_piece", "king_zone_attackers"}
