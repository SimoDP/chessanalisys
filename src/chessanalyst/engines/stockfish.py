"""Stockfish adapter: the only module that drives the UCI process (CLAUDE.md).

API verified in M0 on ``chess`` 1.11.2 with Stockfish 16 (unchanged with Stockfish 19, M2):
``SimpleEngine.analysis(board, multipv=k, root_moves=[...])`` returns a
``SimpleAnalysisResult`` with ``would_block()``, ``get()`` (raises
``chess.engine.AnalysisComplete`` once the search has ended) and ``stop()``;
every ``info`` carries ``depth``, ``seldepth``, ``multipv``, ``score``
(``PovScore``), ``wdl`` (``PovWdl``, with ``UCI_ShowWDL``), ``nodes``,
``time``, ``pv`` and, on aspiration-window fails, ``lowerbound``/``upperbound``.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Sequence
from pathlib import Path

import chess
import chess.engine
import psutil

from chessanalyst.engines.types import EngineLine, NodeResult, line_from_info
from chessanalyst.errors import EnvironmentProblem

log = logging.getLogger(__name__)


def default_threads() -> int:
    phys = psutil.cpu_count(logical=False)
    if phys is None:
        phys = (os.cpu_count() or 2) // 2
    return max(1, phys - 1)


def default_hash_mb(hash_mb: int, ram_fraction: float) -> int:
    """``min(hash_mb, fraction of RAM)`` rounded down to a power of two (§3.1.1)."""
    cap = int(psutil.virtual_memory().total * ram_fraction) // (1024 * 1024)
    h = max(1, min(hash_mb, cap))
    return 1 << (h.bit_length() - 1)


class StockfishEngine:
    """One Stockfish process per run; always closed with :meth:`close`."""

    def __init__(
        self,
        command: str | Path | Sequence[str],
        hash_mb: int,
        poll_s: float,
        threads: int | None = None,
        ram_fraction: float | None = None,
        syzygy_path: str | Path | None = None,
    ) -> None:
        self.command = [str(c) for c in command] if isinstance(command, (list, tuple)) else str(command)
        self.hash_mb = default_hash_mb(hash_mb, ram_fraction) if ram_fraction is not None else hash_mb
        self.threads = threads if threads is not None else default_threads()
        self.poll_s = poll_s
        self.syzygy_path = str(syzygy_path) if syzygy_path else None
        self._engine: chess.engine.SimpleEngine | None = None

    # -- lifecycle ---------------------------------------------------------

    def open(self) -> "StockfishEngine":
        if self._engine is not None:
            return self
        try:
            eng = chess.engine.SimpleEngine.popen_uci(self.command)
        except (FileNotFoundError, PermissionError, OSError, chess.engine.EngineError) as e:
            raise EnvironmentProblem(f"Impossibile avviare Stockfish ({self.command}): {e}") from e
        opts: dict[str, object] = {}
        if "Threads" in eng.options:
            opts["Threads"] = self.threads
        if "Hash" in eng.options:
            opts["Hash"] = self.hash_mb
        if "UCI_ShowWDL" in eng.options:
            opts["UCI_ShowWDL"] = True
        if self.syzygy_path and "SyzygyPath" in eng.options:      # from M2 (D-62)
            opts["SyzygyPath"] = self.syzygy_path
        if opts:
            eng.configure(opts)
        self._engine = eng
        return self

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.quit()
            except (chess.engine.EngineError, chess.engine.EngineTerminatedError, OSError):
                pass
            self._engine = None

    def __enter__(self) -> "StockfishEngine":
        return self.open()

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def engine(self) -> chess.engine.SimpleEngine:
        if self._engine is None:
            self.open()
        assert self._engine is not None
        return self._engine

    @property
    def version(self) -> str:
        return str(self.engine.id.get("name", "unknown"))

    # -- analysis primitive (§3.1.3) ----------------------------------------

    def analyse_node(
        self,
        board: chess.Board,
        multipv: int,
        t_target: float,
        d_min: int,
        t_cap: float,
        root_moves: Sequence[chess.Move] | None = None,
    ) -> NodeResult:
        """Search until (``t_target`` elapsed and a complete iteration reached
        ``d_min``) or ``t_cap`` elapsed. Only complete MultiPV iterations are
        kept; bound-only lines are ignored."""
        if any(not mv for mv in board.move_stack):
            # A null move cannot be sent to Stockfish as "0000" inside the move
            # list: analyse the resulting position from its FEN instead.
            board = chess.Board(board.fen())
        legal = board.legal_moves.count()
        k = min(multipv, len(root_moves) if root_moves else legal)
        if k <= 0:
            raise ValueError("analyse_node: nessuna mossa da analizzare")
        start = time.monotonic()
        lines: dict[int, dict] = {}
        snapshot: dict[int, dict] | None = None
        snap_depth = 0
        kwargs: dict[str, object] = {"multipv": k}
        if root_moves:
            kwargs["root_moves"] = list(root_moves)
        with self.engine.analysis(board, **kwargs) as an:
            while True:
                elapsed = time.monotonic() - start
                if elapsed >= t_cap:
                    break
                if snapshot is not None and elapsed >= t_target and snap_depth >= d_min:
                    break
                if an.would_block():
                    time.sleep(self.poll_s)
                    continue
                try:
                    info = an.get()
                except chess.engine.AnalysisComplete:
                    break
                if info.get("lowerbound") or info.get("upperbound"):
                    continue
                if "multipv" not in info or "pv" not in info or "depth" not in info or "score" not in info:
                    continue
                if not info["pv"]:
                    continue
                lines[info["multipv"]] = info
                if info["multipv"] == k and all(
                    i in lines and lines[i]["depth"] == info["depth"] for i in range(1, k + 1)
                ):
                    snapshot = {i: lines[i] for i in range(1, k + 1)}
                    snap_depth = int(info["depth"])
            an.stop()
        elapsed = time.monotonic() - start
        used = snapshot if snapshot is not None else dict(sorted(lines.items()))
        unstable = snapshot is None or snap_depth < d_min
        result_lines: list[EngineLine] = [line_from_info(board, used[i]) for i in sorted(used)]
        last = used[max(used)] if used else {}
        depth = snap_depth if snapshot is not None else int(max((v["depth"] for v in used.values()), default=0))
        return NodeResult(
            fen=board.fen(en_passant="legal"),
            multipv=k,
            depth=depth,
            seldepth=last.get("seldepth"),
            nodes=last.get("nodes"),
            time_s=round(elapsed, 3),
            unstable_depth=unstable,
            engine_version=self.version,
            root_moves=[m.uci() for m in root_moves] if root_moves else None,
            lines=result_lines,
        )
