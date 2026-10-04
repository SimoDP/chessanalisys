"""One analysis run: engines → pack.json in the output folder (M1a: no LLM)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.openings import OpeningIndex
from chessanalyst.inputs.pgn import truncated_pgn
from chessanalyst.inputs.position import Position
from chessanalyst.output import attach_run_log, make_output_dir
from chessanalyst.pack.builder import UserSettings
from chessanalyst.pipeline import analyse_position

log = logging.getLogger(__name__)


@dataclass
class Engines:
    analyzer: CachedAnalyzer
    maia: Any
    close: Callable[[], None]


def open_engines(cfg: Config, cache: Cache | None = None) -> Engines:
    """Real Stockfish and Maia-2 behind the SQLite cache (missing → EnvironmentProblem, exit 4)."""
    from chessanalyst.engines.factory import make_maia, make_stockfish

    cache = cache if cache is not None else Cache()
    maia = make_maia(cfg, cache)
    sf = make_stockfish(cfg).open()
    return Engines(CachedAnalyzer(sf, cache), maia, sf.close)


def load_openings(cfg: Config) -> OpeningIndex | None:
    path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    try:
        return OpeningIndex.load(path)
    except (OSError, ValueError):
        log.warning("Indice delle aperture non disponibile: %s", path)
        return None


def run_analysis(cfg: Config, pos: Position, us: UserSettings, out_base: Path, *, verbose: bool = False,
                 engines: Engines | None = None, progress: Callable[[str], None] = lambda s: None,
                 openings: OpeningIndex | None = None, time_scale: float = 1.0) -> Path:
    openings = openings if openings is not None else load_openings(cfg)
    entry = openings.lookup_epd(pos.board) if openings is not None else None
    outdir = make_output_dir(out_base, entry["name"] if entry else None, pos.board.epd(en_passant="legal"))
    handler = attach_run_log(outdir / "run.log", verbose)
    own = engines is None
    try:
        log.info("Analisi di %s (utente %s, Elo %s %s, profilo %s)", pos.fen, us.code, us.elo_declared,
                 us.elo_scale, us.budget_profile)
        if pos.source == "pgn" and pos.game is not None:
            (outdir / "game.pgn").write_text(truncated_pgn(pos), encoding="utf-8")
        if own:
            engines = open_engines(cfg)
        try:
            pack = analyse_position(cfg, pos, us, engines.analyzer, engines.maia, openings,
                                    progress=progress, time_scale=time_scale)
        finally:
            if own:
                engines.close()
        (outdir / "pack.json").write_text(pack.model_dump_json(indent=2), encoding="utf-8")
        log.info("pack.json scritto in %s", outdir)
    except Exception:
        log.exception("Analisi interrotta")
        raise
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()
    return outdir
