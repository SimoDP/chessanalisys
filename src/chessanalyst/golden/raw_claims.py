"""Numeric engine values quoted in the raw golden files (examples/golden/raw/).

Every value is in centipawns from White's point of view (the user is White in
all raws). ``path`` is the SAN sequence from the Najdorf root; ``"--"`` is the
null move. ``move = None`` means the evaluation of the node itself (first
line). ``sources`` lists the raw files that quote the value.
"""

from __future__ import annotations

from dataclasses import dataclass

NAJDORF_FEN = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


@dataclass(frozen=True)
class Claim:
    path: tuple[str, ...]
    move: str | None
    raw_cp: int
    sources: tuple[str, ...]
    note: str = ""


R15, R19, R24 = "1500", "1900", "2400"

# Nodes analysed by `golden --data` (§8-bis.4 step 1) with their phase.
GOLDEN_NODES: tuple[tuple[tuple[str, ...], str], ...] = (
    ((), "E0"),
    (("--",), "E1"),
    (("Be3",), "E2"),
    (("Be2",), "E2"),
    (("Bg5",), "E2"),
    (("f4",), "E2"),
    (("Be3", "Ng4"), "E3"),
    (("Be3", "e5", "Nb3"), "E3"),
    (("Be3", "e5", "Nb3", "Be6"), "E3"),
    (("Be3", "e6"), "E3"),
    (("Bg5", "e6", "f4"), "E3"),
    (("Be2", "e5", "Nb3"), "E3"),
    (("Be2", "e5", "Nb3", "Be7"), "E3"),
    (("f4", "e5", "Nb3"), "E3"),
)

CLAIMS: tuple[Claim, ...] = (
    # Root (1900 T1; 1500 T1 and text; 2400 summary)
    Claim((), "Be3", 37, (R15, R19, R24)),
    Claim((), "f3", 37, (R19,)),
    Claim((), "h3", 35, (R19,)),
    Claim((), "Bg5", 29, (R15, R19)),
    Claim((), "Nb3", 25, (R19,)),
    Claim((), "Bd3", 25, (R19,)),
    Claim((), "Bc4", 23, (R15, R19)),
    Claim((), "a4", 23, (R19,)),
    Claim((), "g3", 22, (R19,)),
    Claim((), "Be2", 22, (R15, R19)),
    Claim((), "f4", 20, (R19,)),
    Claim((), "Rg1", 17, (R19, R24)),
    # Null move: "if Black were to move ≈ 0,0 (...e5)"
    Claim(("--",), "e5", 0, (R19, R24), "valore approssimato nel raw (≈ 0,0)"),
    # After 6.Be3
    Claim(("Be3",), "Ng4", 33, (R19, R24)),
    Claim(("Be3",), "e5", 35, (R19, R24)),
    Claim(("Be3",), "Nc6", 41, (R19, R24)),
    Claim(("Be3",), "e6", 50, (R24,)),
    # After 6.Be3 Ng4
    Claim(("Be3", "Ng4"), "Bg5", 38, (R24,)),
    Claim(("Be3", "Ng4"), "Bc1", 36, (R24,)),
    Claim(("Be3", "Ng4"), "Qd2", 0, (R24,), "≈ 0,00 nel raw"),
    Claim(("Be3", "Ng4"), "Qe2", 0, (R24,), "≈ 0,00 nel raw"),
    Claim(("Be3", "Ng4"), "Qf3", 0, (R24,), "≈ 0,00 nel raw"),
    # After 6.Be3 e5 7.Nb3
    Claim(("Be3", "e5", "Nb3"), "Be6", 33, (R19,)),
    Claim(("Be3", "e5", "Nb3"), "Nc6", 86, (R19, R24)),
    # After 6.Be3 e5 7.Nb3 Be6
    Claim(("Be3", "e5", "Nb3", "Be6"), "h3", 34, (R24,)),
    Claim(("Be3", "e5", "Nb3", "Be6"), "Qd2", 32, (R24,)),
    Claim(("Be3", "e5", "Nb3", "Be6"), "f3", 28, (R24,)),
    Claim(("Be3", "e5", "Nb3", "Be6"), "Be2", 24, (R24,)),
    Claim(("Be3", "e5", "Nb3", "Be6"), "Qd3", 22, (R24,)),
    Claim(("Be3", "e5", "Nb3", "Be6"), "a3", 9, (R24,)),
    # After 6.Be3 e6
    Claim(("Be3", "e6"), "a3", 49, (R24,)),
    Claim(("Be3", "e6"), "Be2", 43, (R24,)),
    Claim(("Be3", "e6"), "f3", 43, (R24,)),
    Claim(("Be3", "e6"), "Qd2", 42, (R24,)),
    Claim(("Be3", "e6"), "g4", 40, (R24,)),
    Claim(("Be3", "e6"), "Qf3", 30, (R24,)),
    # After 6.Bg5 e6 7.f4
    Claim(("Bg5", "e6", "f4"), "Qb6", 13, (R24,)),
    Claim(("Bg5", "e6", "f4"), "h6", 20, (R24,)),
    Claim(("Bg5", "e6", "f4"), "Nbd7", 38, (R24,)),
    Claim(("Bg5", "e6", "f4"), "Be7", 38, (R24,)),
    Claim(("Bg5", "e6", "f4"), "b5", 52, (R24,)),
    # After 6.Be2 e5 7.Nb3
    Claim(("Be2", "e5", "Nb3"), "Be7", 24, (R19,)),
    Claim(("Be2", "e5", "Nb3"), "Nc6", 34, (R19, R24)),
    # After 6.Be2 e5 7.Nb3 Be7
    Claim(("Be2", "e5", "Nb3", "Be7"), None, 30, (R24,), "valutazione del nodo (D-40)"),
    Claim(("Be2", "e5", "Nb3", "Be7"), "Be3", 30, (R24,)),
    Claim(("Be2", "e5", "Nb3", "Be7"), "O-O", 30, (R24,)),
    Claim(("Be2", "e5", "Nb3", "Be7"), "Bf3", 25, (R24,)),
    Claim(("Be2", "e5", "Nb3", "Be7"), "Qd3", 24, (R24,)),
    Claim(("Be2", "e5", "Nb3", "Be7"), "h3", 12, (R24,)),
    # After 6.f4 e5 7.Nb3
    Claim(("f4", "e5", "Nb3"), "Nbd7", 6, (R19, R24)),
    Claim(("f4", "e5", "Nb3"), "Nc6", 9, (R19, R24)),
)

# Best move claimed by the raws for a node (ordering check, not numeric).
BEST_CLAIMS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    ((), ("Be3", "f3")),
    (("--",), ("e5",)),
    (("Be3",), ("Ng4",)),
    (("Be3", "Ng4"), ("Bg5",)),
    (("Be3", "e5", "Nb3"), ("Be6",)),
    (("Be3", "e5", "Nb3", "Be6"), ("h3",)),
    (("Be3", "e6"), ("a3",)),
    (("Bg5", "e6", "f4"), ("Qb6",)),
    (("Be2", "e5", "Nb3"), ("Be7",)),
    (("Be2", "e5", "Nb3", "Be7"), ("Be3", "O-O")),
    (("f4", "e5", "Nb3"), ("Nbd7",)),
)

# Root WDL quoted by the raws: "circa 92% di patta".
ROOT_DRAW_PERMILLE = 920

# AC-09: the first three candidates of the raws (1900 T1 order).
AC09_TOP3 = ("Be3", "f3", "h3")
