"""SQLite cache for Stockfish and Maia-2 results (§3.3, D-60)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chess
import platformdirs

from chessanalyst.engines.types import NodeResult


def default_cache_path() -> Path:
    return Path(platformdirs.user_cache_dir("chessanalyst")) / "cache.sqlite"


def history_key(board: chess.Board) -> str:
    """UCI of the moves since the last irreversible move (capture or pawn
    move), or ``""`` when the board has no history (D-60)."""
    if not board.move_stack:
        return ""
    b = board.copy()
    tail: list[str] = []
    while b.move_stack:
        mv = b.pop()
        irreversible = b.is_capture(mv) or b.piece_type_at(mv.from_square) == chess.PAWN
        if irreversible:
            break
        tail.append(mv.uci())
    return " ".join(reversed(tail))


def sf_key(engine_version: str, board: chess.Board, root_moves: Sequence[str] | None = None) -> str:
    fen = board.fen(en_passant="legal")
    rm = ",".join(sorted(root_moves)) if root_moves else ""
    raw = f"{engine_version}|{fen}|{history_key(board)}|{rm}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def maia_key(epd: str, elo_self: int, elo_oppo: int, model_type: str, package_version: str) -> str:
    raw = f"{epd}|{elo_self}|{elo_oppo}|{model_type}|{package_version}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def satisfies(stored: NodeResult, multipv: int, d_min: int) -> bool:
    """A stored result serves a request with ``multipv`` ≤ stored lines and
    ``d_min`` ≤ stored depth, unless it is ``unstable_depth`` (§3.3)."""
    return (not stored.unstable_depth) and stored.multipv >= multipv and stored.depth >= d_min


def better(new: NodeResult, old: NodeResult) -> bool:
    """A new result replaces the cached one only if deeper (tie: more MultiPV)."""
    if new.depth != old.depth:
        return new.depth > old.depth
    return new.multipv > old.multipv


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Cache:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_cache_path()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path))
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS sf(key TEXT PRIMARY KEY, engine_version TEXT, multipv INTEGER,"
            " depth INTEGER, result_json TEXT, created_utc TEXT)"
        )
        self.db.execute("CREATE TABLE IF NOT EXISTS maia(key TEXT PRIMARY KEY, result_json TEXT, created_utc TEXT)")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    # -- Stockfish -----------------------------------------------------------

    def get_sf(self, key: str, multipv: int, d_min: int) -> NodeResult | None:
        row = self.db.execute("SELECT result_json FROM sf WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        stored = NodeResult.from_dict(json.loads(row[0]))
        if not satisfies(stored, multipv, d_min):
            return None
        return stored.truncated(multipv)

    def put_sf(self, key: str, result: NodeResult) -> bool:
        """Store ``result``; return False if a better result was kept."""
        row = self.db.execute("SELECT result_json FROM sf WHERE key = ?", (key,)).fetchone()
        if row is not None:
            old = NodeResult.from_dict(json.loads(row[0]))
            if not better(result, old):
                return False
        self.db.execute(
            "INSERT OR REPLACE INTO sf VALUES (?, ?, ?, ?, ?, ?)",
            (key, result.engine_version, result.multipv, result.depth, json.dumps(result.to_dict()), _now()),
        )
        self.db.commit()
        return True

    # -- Maia-2 --------------------------------------------------------------

    def get_maia(self, key: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT result_json FROM maia WHERE key = ?", (key,)).fetchone()
        return None if row is None else json.loads(row[0])

    def put_maia(self, key: str, result: dict[str, Any]) -> None:
        self.db.execute("INSERT OR REPLACE INTO maia VALUES (?, ?, ?)", (key, json.dumps(result), _now()))
        self.db.commit()


class CachedAnalyzer:
    """Stockfish (or :class:`~chessanalyst.engines.fake.FakeEngine`) behind the cache.

    ``engine`` needs ``version`` and ``analyse_node``. ``calls`` counts the
    searches actually run (AC-14 in M1a)."""

    def __init__(self, engine: Any, cache: Cache) -> None:
        self.engine = engine
        self.cache = cache
        self.calls = 0

    def analyse(
        self,
        board: chess.Board,
        multipv: int,
        t_target: float,
        d_min: int,
        t_cap: float,
        root_moves: Sequence[chess.Move] | None = None,
    ) -> NodeResult:
        k = min(multipv, len(root_moves) if root_moves else board.legal_moves.count())
        rm = [m.uci() for m in root_moves] if root_moves else None
        key = sf_key(self.engine.version, board, rm)
        hit = self.cache.get_sf(key, k, d_min)
        if hit is not None:
            return hit
        self.calls += 1
        res = self.engine.analyse_node(board, multipv, t_target, d_min, t_cap, root_moves=root_moves)
        self.cache.put_sf(key, res)
        return res
