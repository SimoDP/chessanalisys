"""Opening index from ``lichess-org/chess-openings`` (CC0, D-59, §3.3).

At setup the TSV files ``a.tsv`` … ``e.tsv`` (columns ``eco``, ``name``,
``pgn``) are replayed and ``data/openings_index.json`` maps
``EPD → {eco, name, plies}``. When several rows reach the same EPD the one
with more plies wins, ties by file order. Lookup by exact EPD (M1) and, from
M2, by sequence for a game with history from the standard start: the longest
row whose PGN is a prefix of the game's moves. The sequences (UCI from the
standard start) are written next to the index in ``openings_sequences.json``.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from pathlib import Path

import chess
import chess.pgn

TSV_FILES = ("a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv")
SEQUENCES_FILE = "openings_sequences.json"


def epd_of(board: chess.Board) -> str:
    return board.epd(en_passant="legal")


def parse_tsv(text: str) -> Iterable[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for row in reader:
        yield row


def build_index(rows: Iterable[dict[str, str]], sequences: dict[str, dict] | None = None) -> dict[str, dict]:
    """EPD index; when ``sequences`` is given it is filled with ``"uci uci …" → entry``
    (first row wins on identical sequences, i.e. file order)."""
    index: dict[str, dict] = {}
    for row in rows:
        game = chess.pgn.read_game(io.StringIO(row["pgn"]))
        if game is None or game.errors:
            raise ValueError(f"PGN non valido nell'indice delle aperture: {row}")
        board = game.board()
        plies = 0
        ucis = []
        for mv in game.mainline_moves():
            board.push(mv)
            ucis.append(mv.uci())
            plies += 1
        epd = epd_of(board)
        entry = {"eco": row["eco"], "name": row["name"], "plies": plies}
        if sequences is not None:
            sequences.setdefault(" ".join(ucis), entry)
        old = index.get(epd)
        if old is None or plies > old["plies"]:
            index[epd] = entry
    return index


def build_index_from_dir(directory: Path, sequences: dict[str, dict] | None = None) -> dict[str, dict]:
    rows: list[dict[str, str]] = []
    for name in TSV_FILES:
        rows.extend(parse_tsv((directory / name).read_text(encoding="utf-8")))
    return build_index(rows, sequences)


def write_index(index: dict[str, dict], path: Path, sequences: dict[str, dict] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True, indent=0), encoding="utf-8")
    if sequences is not None:
        (path.parent / SEQUENCES_FILE).write_text(
            json.dumps(sequences, ensure_ascii=False, sort_keys=True, indent=0), encoding="utf-8")


def opening_entry(openings: "OpeningIndex | None", board: chess.Board) -> dict | None:
    """The entry shown to the user (confirmation, folder name), or None."""
    found = openings.lookup(board) if openings is not None else None
    return found[0] if found else None


class OpeningIndex:
    def __init__(self, index: dict[str, dict], sequences: dict[str, dict] | None = None,
                 structure_max_piece_diff: int | None = None) -> None:
        self.index = index
        self.sequences = sequences or {}
        self.structure_max_piece_diff = structure_max_piece_diff
        self._by_pawns: dict[tuple[int, int], list[tuple[set, dict]]] | None = None

    @classmethod
    def load(cls, path: Path, structure_max_piece_diff: int | None = None) -> "OpeningIndex":
        path = Path(path)
        seq_path = path.parent / SEQUENCES_FILE
        seqs = json.loads(seq_path.read_text(encoding="utf-8")) if seq_path.is_file() else None
        return cls(json.loads(path.read_text(encoding="utf-8")), seqs, structure_max_piece_diff)

    def __len__(self) -> int:
        return len(self.index)

    def lookup_epd(self, board: chess.Board) -> dict | None:
        return self.index.get(epd_of(board))

    def lookup_sequence(self, board: chess.Board) -> dict | None:
        """Longest row whose moves are a prefix of the game (history from the standard start)."""
        if not board.move_stack or not self.sequences:
            return None
        start = board.copy()
        while start.move_stack:
            start.pop()
        if start.fen() != chess.STARTING_FEN:
            return None
        ucis = [m.uci() for m in board.move_stack]
        for n in range(len(ucis), 0, -1):
            entry = self.sequences.get(" ".join(ucis[:n]))
            if entry is not None:
                return entry
        return None

    def lookup_structure(self, board: chess.Board) -> dict | None:
        """D-76: a position past the book takes the name of a book position with exactly the same pawns and at
        most ``structure_max_piece_diff`` piece squares different (a piece moved elsewhere counts twice); the
        closest wins, then the one with more plies, then file order. None when disabled or nothing is close."""
        if self.structure_max_piece_diff is None:
            return None
        if self._by_pawns is None:
            self._by_pawns = {}
            for epd, entry in self.index.items():
                b = chess.Board(epd + " 0 1")
                self._by_pawns.setdefault(_pawns(b), []).append((_pieces(b), entry))
        mine = _pieces(board)
        best = None
        for pieces, entry in self._by_pawns.get(_pawns(board), []):
            key = (len(mine ^ pieces), -entry["plies"])
            if key[0] <= self.structure_max_piece_diff and (best is None or key < best[0]):
                best = (key, entry)
        return best[1] if best else None

    def lookup(self, board: chess.Board) -> tuple[dict, str] | None:
        """(entry, matched_by): by sequence when the game has a history (M2), else by EPD, else by the pawn
        structure (D-76)."""
        entry = self.lookup_sequence(board)
        if entry is not None:
            return entry, "sequence"
        entry = self.lookup_epd(board)
        if entry is not None:
            return entry, "epd"
        entry = self.lookup_structure(board)
        return (entry, "structure") if entry is not None else None


def _pawns(board: chess.Board) -> tuple[int, int]:
    return int(board.pieces(chess.PAWN, chess.WHITE)), int(board.pieces(chess.PAWN, chess.BLACK))


def _pieces(board: chess.Board) -> set[tuple[int, str]]:
    return {(sq, p.symbol()) for sq, p in board.piece_map().items() if p.piece_type != chess.PAWN}
