"""The position chosen for analysis, with its history."""

from __future__ import annotations

from dataclasses import dataclass, field

import chess
import chess.pgn


@dataclass
class Position:
    board: chess.Board                  # move_stack = history from the start of the game (PGN only)
    source: str                         # "example" | "fen" | "pgn"
    start_fen: str | None = None        # PGN: initial position of the game
    plies: int = 0                      # half-moves played from the start of the game
    game: chess.pgn.Game | None = field(default=None, repr=False)

    @property
    def fen(self) -> str:
        return self.board.fen(en_passant="legal")

    @property
    def last_move_san(self) -> str | None:
        if not self.board.move_stack:
            return None
        b = self.board.copy()
        mv = b.pop()
        return b.san(mv)

    def repetitions(self) -> int:
        """How many times the current position already occurred before (PGN)."""
        if not self.board.move_stack:
            return 0
        key = self.board._transposition_key()
        b = self.board.copy()
        n = 0
        while b.move_stack:
            b.pop()
            if b._transposition_key() == key:
                n += 1
        return n
