"""One analysis run: engines → ``pack.json`` → model, verification and render
(``analysis.md``, ``llm_raw.json``, ``verification.json``); ``rerun`` repeats the
second half from a saved ``pack.json`` (§9.3, D-19)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.openings import OpeningIndex
from chessanalyst.errors import AnalystError, ModelError, UsageError
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


TEXT_FILES = ("analysis.md", "llm_raw.json", "verification.json")


def _prev_name(name: str) -> str:
    stem, ext = name.rsplit(".", 1)
    return f"{stem}.prev.{ext}"


def produce_text(cfg: Config, outdir: Path, pack: dict, client=None, warnings: list[str] | None = None) -> Path:
    """Model, verification and render; files written in ``outdir``. ModelError → exit code 5 with the
    responses received so far in ``llm_raw.json``."""
    from chessanalyst.llm.client import make_client
    from chessanalyst.llm.cycle import run_model

    hint = f"il pacchetto è salvato: dopo aver risolto, usa `chessanalyst rerun {outdir}`"
    try:
        client = client if client is not None else make_client(cfg)
    except AnalystError as e:
        raise type(e)(f"{e} ({hint})") from None
    raw: list[dict] = []
    try:
        res = run_model(cfg, pack, client, raw=raw, warnings=warnings)
    except ModelError as e:
        (outdir / "llm_raw.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
        raise ModelError(f"{e}; {hint}") from None
    finally:
        log.info("Risposte del modello ricevute: %d", len(raw))
    (outdir / "llm_raw.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
    (outdir / "verification.json").write_text(json.dumps(res.verification, indent=1, ensure_ascii=False),
                                              encoding="utf-8")
    (outdir / "analysis.md").write_text(res.document, encoding="utf-8")
    log.info("analysis.md scritto (retry %d%s)", res.retries, ", modalità degradata" if res.degraded else "")
    return outdir / "analysis.md"


def rerun(cfg: Config, folder: Path, *, client=None, verbose: bool = False) -> Path:
    """Reads ``pack.json`` (plan and tables come from the pack, not from the current configuration),
    uses the current configuration for model, prompt, verification and render; previous files
    become ``*.prev.*``."""
    from chessanalyst.pack.schema import Pack

    pack_file = folder / "pack.json"
    if not pack_file.is_file():
        raise UsageError(f"{folder} non contiene pack.json")
    pack = json.loads(Pack.model_validate_json(pack_file.read_text(encoding="utf-8")).model_dump_json())
    handler = attach_run_log(folder / "run.log", verbose)
    try:
        log.info("rerun di %s", folder)
        warnings = []
        if pack["config_hash"] != cfg.config_hash:
            log.warning("config_hash del pacchetto diverso da quello corrente: il pacchetto viene usato così com'è")
            warnings.append("config_hash diverso da quello corrente")
        for name in TEXT_FILES:
            if (folder / name).exists():
                (folder / name).replace(folder / _prev_name(name))
        return produce_text(cfg, folder, pack, client, warnings)
    except AnalystError as e:          # expected: message on the console, no trace
        log.info("rerun interrotto: %s", e)
        raise
    except Exception:
        log.exception("rerun interrotto")
        raise
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()


def run_analysis(cfg: Config, pos: Position, us: UserSettings, out_base: Path, *, verbose: bool = False,
                 engines: Engines | None = None, progress: Callable[[str], None] = lambda s: None,
                 openings: OpeningIndex | None = None, time_scale: float = 1.0, llm=None) -> Path:
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
        progress("modello di linguaggio, verifica e render")
        produce_text(cfg, outdir, json.loads(pack.model_dump_json()), llm)
    except AnalystError as e:          # expected: message on the console, no trace
        log.info("Analisi interrotta: %s", e)
        raise
    except Exception:
        log.exception("Analisi interrotta")
        raise
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()
    return outdir
