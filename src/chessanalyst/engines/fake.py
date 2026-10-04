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

from chessanalyst.engines.cache import better, satisfies, sf_key
from chessanalyst.engines.types import NodeResult


class MissingRecording(LookupError):
    pass


class FakeEngine:
    """Drop-in replacement for :class:`StockfishEngine` in tests."""

    def __init__(self, version: str = "Stockfish 16", records: Iterable[dict[str, Any]] = ()) -> None:
        self.version = version
        # every recorded search of a position (the same key can hold e.g. an E2b search with MultiPV 2
        # and a deeper-level search with MultiPV 8, or the searches of two recording groups)
        self._store: dict[str, list[NodeResult]] = {}
        self.calls = 0
        for rec in records:
            res = NodeResult.from_dict(rec["result"])
            lst = self._store.setdefault(rec["key"], [])
            if res not in lst:
                lst.append(res)

    @classmethod
    def from_dir(cls, directory: Path, version: str | None = None) -> "FakeEngine":
        """``version`` defaults to the engine that produced the recordings (it is part of the key)."""
        records: list[dict[str, Any]] = []
        for f in sorted(Path(directory).glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            records.extend(data if isinstance(data, list) else [data])
        if version is None:
            version = next((r["result"]["engine_version"] for r in records), "Stockfish 16")
        return cls(version, records)

    def add(self, board: chess.Board, result: NodeResult, root_moves: Sequence[str] | None = None) -> None:
        self._store.setdefault(sf_key(self.version, board, root_moves), []).append(result)

    def _pick(self, key: str, k: int, d_min: int) -> NodeResult | None:
        """The best recorded search that satisfies the request (cache rule, §3.3); otherwise the
        exact replay of a search with enough lines (even if unstable)."""
        recs = self._store.get(key, [])
        ok = [r for r in recs if satisfies(r, k, d_min)]
        if ok:
            best = ok[0]
            for r in ok[1:]:
                if better(r, best):
                    best = r
            return best
        return next((r for r in recs if r.multipv >= k), None)

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
        rec = self._pick(sf_key(self.version, board, rm), k, d_min)
        if rec is None and rm:
            rec = self._from_superset(board, rm, k)
        if rec is None:
            raise MissingRecording(
                f"Nessuna registrazione adatta per {board.fen()} (multipv {k}, d_min {d_min}, root_moves {rm})"
            )
        return rec.truncated(k)

    def _from_superset(self, board: chess.Board, root_moves: list[str], k: int) -> NodeResult | None:
        """A restricted search (E4/E2c) answered from any recording of the same
        position that contains all the requested moves."""
        fen = board.fen(en_passant="legal")
        wanted = set(root_moves)
        for rec in (r for lst in self._store.values() for r in lst):
            if rec.fen != fen:
                continue
            lines = [ln for ln in rec.lines if ln.uci in wanted]
            if {ln.uci for ln in lines} == wanted:
                d = rec.to_dict()
                d["lines"] = [{**ln.__dict__, "rank": i} for i, ln in enumerate(lines, 1)]
                d["multipv"] = len(lines)
                d["root_moves"] = sorted(wanted)
                return NodeResult.from_dict(d).truncated(k)
        return None


class RecordingMaiaBackend:
    """Wraps a backend and keeps every raw answer (fixtures/recorded/maia)."""

    def __init__(self, inner) -> None:
        self.inner = inner
        self.package_version = inner.package_version
        self.model_type = inner.model_type
        self.device = inner.device
        self.records: dict[tuple[str, int, int], dict[str, Any]] = {}

    def infer(self, fen: str, elo_self: int, elo_oppo: int) -> tuple[dict[str, float], float]:
        probs, win = self.inner.infer(fen, elo_self, elo_oppo)
        epd = chess.Board(fen).epd(en_passant="legal")
        self.records[(epd, elo_self, elo_oppo)] = {"epd": epd, "elo_self": elo_self, "elo_oppo": elo_oppo,
                                                   "move_probs": dict(probs), "win_prob_white": float(win)}
        return probs, win


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
