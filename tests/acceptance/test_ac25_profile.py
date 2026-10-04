"""AC-25: matrix_column() and the definitions of tactical, quiet, hanging_piece,
unresolved_capture on the positions of Appendix G.1, plus the §5.1 features on
the Najdorf (root and after 6.Be3 e5 7.Nb3)."""

from __future__ import annotations

import chess
import pytest

from chessanalyst.engines.types import EngineLine
from chessanalyst.explore.select import quiet_spread
from chessanalyst.features.profile import compute_profile, extract_features, matrix_column


def fen(root, name):
    return (root / "fixtures" / "positions" / f"{name}.fen").read_text().strip()


def lines(board, evals_white):
    """Synthetic E0 rows on the first legal moves."""
    moves = list(board.legal_moves)
    return [EngineLine(i + 1, board.san(moves[i]), moves[i].uci(), e, None, None, [board.san(moves[i])],
                       [moves[i].uci()]) for i, e in enumerate(evals_white)]


def profile(cfg, board, evals, in_book=False, quiet=False, spread=0):
    ls = lines(board, evals)
    feats = extract_features(board, cfg, ls)
    return compute_profile(board, cfg, ls, 5, feats, in_book, quiet, spread), feats


def keys(feats, key):
    return [(f.side, f.squares, f.value) for f in feats if f.key == key]


def test_opening_pawn_attacked_is_not_tactical(cfg, root):
    b = chess.Board(fen(root, "opening_pawn_attacked"))
    prof, feats = profile(cfg, b, [20, 10, 0], in_book=True)
    assert not prof["tactical"] and prof["matrix_column"] == 1 and prof["phase"] == "opening"
    assert not keys(feats, "unresolved_capture")   # exd5 has SEE 0


def test_knight_attacked_by_pawn(cfg, root):
    b = chess.Board(fen(root, "knight_attacked_by_pawn"))
    prof, feats = profile(cfg, b, [-300, -20])
    assert keys(feats, "hanging_piece") == [("w", ["e5"], None)]
    assert keys(feats, "unresolved_capture") == [("b", ["d6", "e5"], 3)]
    assert prof["tactical"] and prof["matrix_column"] == 2
    assert {"hanging_piece", "unresolved_capture", "gap"} <= set(prof["tactical_reasons"])


def test_in_check(cfg, root):
    b = chess.Board(fen(root, "in_check"))
    prof, _ = profile(cfg, b, [0, -10])
    assert "in_check" in prof["tactical_reasons"] and prof["matrix_column"] == 2


def test_rook_endgame(cfg, root):
    prof, _ = profile(cfg, chess.Board(fen(root, "rook_endgame")), [0, -5])
    assert prof["phase"] == "endgame" and prof["matrix_column"] == 3


def test_kpk_without_tablebase_in_m1(cfg, root):
    prof, _ = profile(cfg, chess.Board(fen(root, "kpk")), [500, 0])
    assert prof["tablebase"] is False and prof["matrix_column"] == 3
    assert matrix_column({**prof, "tablebase": True}) == 4


def test_quiet_and_tactical_by_engine_values(cfg, root):
    b = chess.Board(fen(root, "najdorf"))
    assert quiet_spread([37, 37, 35, 29, 25], 5, 25) == (True, 12)
    assert quiet_spread([60, 40, 30, 25, 20], 5, 25) == (False, 40)
    prof, _ = profile(cfg, b, [60, 0, -10], in_book=True, quiet=False, spread=40)   # gap 60
    assert not prof["tactical"] and prof["matrix_column"] == 1
    prof, _ = profile(cfg, b, [200, 0, -10], in_book=True)                         # gap 200
    assert prof["tactical_reasons"] == ["gap"] and prof["matrix_column"] == 2


def test_mate_reason(cfg, root):
    b = chess.Board(fen(root, "najdorf"))
    ls = lines(b, [9997, 0])
    ls[0].mate_white = 3                                       # mate in 3 = 5 plies ≤ 8
    feats = extract_features(b, cfg, ls)
    prof = compute_profile(b, cfg, ls, 5, feats, True, False, 0)
    assert "mate" in prof["tactical_reasons"]
    assert keys(feats, "mate_in_n") == [("w", [], 3)]


def test_najdorf_features(cfg, root):
    b = chess.Board(fen(root, "najdorf"))
    feats = extract_features(b, cfg, [])
    assert not keys(feats, "backward_pawn")
    assert keys(feats, "material_balance") == [(None, [], 0)]
    assert ("w", ["e1"], None) in keys(feats, "can_castle_short")
    for san in ("Be3", "e5", "Nb3"):
        b.push_san(san)
    feats = extract_features(b, cfg, [])
    assert keys(feats, "backward_pawn") == [("b", ["d6"], None)]
    assert ("b", ["d5"], None) in keys(feats, "weak_square")
    assert keys(feats, "outpost") == [("w", ["d5"], None)]


def test_profile_fields_on_najdorf(cfg, root):
    b = chess.Board(fen(root, "najdorf"))
    prof, _ = profile(cfg, b, [37, 37, 35], in_book=True, quiet=True, spread=12)
    assert prof["castling"] == {"w": "can_both", "b": "can_both"}
    assert prof["material"] == {"w": 38, "b": 38, "balance": 0}
    assert prof["closed"] is False and prof["quiet"] is True
