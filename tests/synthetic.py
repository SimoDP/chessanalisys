"""Deterministic synthetic engine and Maia-2 for planning tests (AC-25, AC-32, AC-33).

Evaluations come from ``overrides[(epd, uci)]`` (centipawns, point of view of
the side to move) or from a hash of the position and the move in [-30, 29].
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import chess

from chessanalyst.engines.types import EngineLine, NodeResult, san_line


def _h(text: str, mod: int) -> int:
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) % mod


class SyntheticEngine:
    version = "Synthetic 1"

    def __init__(self, overrides: dict[tuple[str, str], int] | None = None, clock=None, cost: float = 1.0,
                 pv_len: int = 8) -> None:
        self.overrides = overrides or {}
        self.clock = clock
        self.cost = cost
        self.pv_len = pv_len
        self.calls = 0
        self.requests: list[tuple[str, int, int, tuple]] = []

    def mover_cp(self, board: chess.Board, mv: chess.Move) -> int:
        epd = board.epd(en_passant="legal")
        return self.overrides.get((epd, mv.uci()), _h(epd + mv.uci(), 60) - 30)

    def _pv(self, board: chess.Board, first: chess.Move) -> list[chess.Move]:
        b = board.copy(stack=False)
        pv = [first]
        b.push(first)
        while len(pv) < self.pv_len and not b.is_game_over():
            mv = max(b.legal_moves, key=lambda m: (self.mover_cp(b, m), m.uci()))
            pv.append(mv)
            b.push(mv)
        return pv

    def analyse_node(self, board: chess.Board, multipv: int, t_target: float, d_min: int, t_cap: float,
                     root_moves: Sequence[chess.Move] | None = None) -> NodeResult:
        self.calls += 1
        moves = list(root_moves) if root_moves else list(board.legal_moves)
        k = min(multipv, len(moves))
        if k <= 0:                      # like engines/stockfish.py: a mate or stalemate cannot be analysed
            raise ValueError("analyse_node: nessuna mossa da analizzare")
        self.requests.append((board.epd(en_passant="legal"), k, d_min, tuple(m.uci() for m in root_moves or [])))
        if self.clock is not None:
            self.clock.advance(self.cost)
        ranked = sorted(moves, key=lambda m: (-self.mover_cp(board, m), m.uci()))[:k]
        lines = []
        for i, mv in enumerate(ranked, 1):
            cp = self.mover_cp(board, mv)
            white = cp if board.turn == chess.WHITE else -cp
            sans, ucis = san_line(board, self._pv(board, mv))
            lines.append(EngineLine(i, sans[0], ucis[0], white, None, None, sans, ucis))
        return NodeResult(board.fen(en_passant="legal"), k, d_min, d_min, 1000, 0.01, False, self.version,
                          [m.uci() for m in root_moves] if root_moves else None, lines)


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class SyntheticMaiaBackend:
    package_version = "synthetic"
    model_type = "rapid"
    device = "cpu"

    def __init__(self, overrides: dict[str, dict[str, float]] | None = None) -> None:
        self.overrides = overrides or {}

    def infer(self, fen: str, elo_self: int, elo_oppo: int) -> tuple[dict[str, float], float]:
        b = chess.Board(fen)
        epd = b.epd(en_passant="legal")
        if epd in self.overrides:
            return dict(self.overrides[epd]), 0.5
        w = {m.uci(): 1 + _h(epd + m.uci() + str(elo_self), 20) for m in b.legal_moves}
        tot = sum(w.values())
        return {u: v / tot for u, v in w.items()}, 0.5
