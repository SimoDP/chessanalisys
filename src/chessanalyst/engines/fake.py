"""Fakes used by the test-suite: no engine, no weights, no network (§12.1).

* :class:`FakeEngine` answers from recorded :class:`NodeResult` files
  (``fixtures/recorded/engine/*.json``) indexed by cache key, applying the
  same satisfaction rule as the cache (§3.3).
* :class:`FakeMaiaBackend` answers from recorded Maia-2 outputs
  (``fixtures/recorded/maia/*.json``) and plugs into :class:`MaiaEngine`.
* ``FakeUCI`` (a real UCI process replaying scripted lines) lives in
  :mod:`chessanalyst.engines.fake_uci`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import chess

from chessanalyst.engines.cache import satisfies, sf_key
from chessanalyst.engines.types import NodeResult


class MissingRecording(LookupError):
    pass


class FakeEngine:
    """Drop-in replacement for :class:`StockfishEngine` in tests."""

    def __init__(self, version: str = "Stockfish 16", records: Iterable[dict[str, Any]] = ()) -> None:
        self.version = version
        self._store: dict[str, NodeResult] = {}
        self.calls = 0
        for rec in records:
            self._store[rec["key"]] = NodeResult.from_dict(rec["result"])

    @classmethod
    def from_dir(cls, directory: Path, version: str = "Stockfish 16") -> "FakeEngine":
        records: list[dict[str, Any]] = []
        for f in sorted(Path(directory).glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            records.extend(data if isinstance(data, list) else [data])
        return cls(version, records)

    def add(self, board: chess.Board, result: NodeResult, root_moves: Sequence[str] | None = None) -> None:
        self._store[sf_key(self.version, board, root_moves)] = result

    def open(self) -> "FakeEngine":
        return self

    def close(self) -> None:
        pass

    def __enter__(self) -> "FakeEngine":
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def analyse_node(
        self,
        board: chess.Board,
        multipv: int,
        t_target: float,
        d_min: int,
        t_cap: float,
        root_moves: Sequence[chess.Move] | None = None,
    ) -> NodeResult:
        self.calls += 1
        k = min(multipv, len(root_moves) if root_moves else board.legal_moves.count())
        rm = [m.uci() for m in root_moves] if root_moves else None
        rec = self._store.get(sf_key(self.version, board, rm))
        if rec is None or not satisfies(rec, k, d_min):
            raise MissingRecording(
                f"Nessuna registrazione adatta per {board.fen()} (multipv {k}, d_min {d_min}, root_moves {rm})"
            )
        return rec.truncated(k)


class FakeMaiaBackend:
    """Recorded Maia-2 answers keyed by ``(epd, elo_self, elo_oppo)``."""

    def __init__(
        self,
        table: dict[tuple[str, int, int], tuple[dict[str, float], float]] | None = None,
        package_version: str = "0.11.0",
        model_type: str = "rapid",
        device: str = "cpu",
    ) -> None:
        self.table = dict(table or {})
        self.package_version = package_version
        self.model_type = model_type
        self.device = device

    @classmethod
    def from_dir(cls, directory: Path) -> "FakeMaiaBackend":
        table: dict[tuple[str, int, int], tuple[dict[str, float], float]] = {}
        for f in sorted(Path(directory).glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            for rec in data if isinstance(data, list) else [data]:
                table[(rec["epd"], rec["elo_self"], rec["elo_oppo"])] = (rec["move_probs"], rec["win_prob_white"])
        return cls(table)

    def infer(self, fen: str, elo_self: int, elo_oppo: int) -> tuple[dict[str, float], float]:
        epd = chess.Board(fen).epd(en_passant="legal")
        try:
            return self.table[(epd, elo_self, elo_oppo)]
        except KeyError as e:
            raise MissingRecording(f"Maia-2 non registrata per {epd} ({elo_self}/{elo_oppo})") from e
