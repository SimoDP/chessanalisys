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
    tablebase: Any = None          # Syzygy probe (M2), None without the tables


def open_engines(cfg: Config, cache: Cache | None = None) -> Engines:
    """Real Stockfish and Maia-2 behind the SQLite cache (missing → EnvironmentProblem, exit 4)."""
    from chessanalyst.engines.factory import make_maia, make_stockfish, make_tablebase

    cache = cache if cache is not None else Cache()
    maia = make_maia(cfg, cache)
    sf = make_stockfish(cfg).open()
    tb = make_tablebase(cfg)

    def close() -> None:
        sf.close()
        if tb is not None:
            tb.close()

    return Engines(CachedAnalyzer(sf, cache), maia, close, tb)


def load_openings(cfg: Config) -> OpeningIndex | None:
    path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    try:
        return OpeningIndex.load(path)
    except (OSError, ValueError):
        log.warning("Indice delle aperture non disponibile: %s", path)
        return None


TEXT_FILES = ("analysis.md", "llm_raw.json", "verification.json")
# «entrambi» (M4): one pack, one set of responses and one verification per color; one analysis.md
COLOR_SUFFIX = {"w": "white", "b": "black"}
BOTH_SEPARATOR = "\n\n---\n\n"


def per_color(name: str, color: str) -> str:
    stem, ext = name.rsplit(".", 1)
    return f"{stem}_{COLOR_SUFFIX[color]}.{ext}"


def _prev_name(name: str) -> str:
    stem, ext = name.rsplit(".", 1)
    return f"{stem}.prev.{ext}"


def produce_text(cfg: Config, outdir: Path, pack: dict, client=None, warnings: list[str] | None = None,
                 color: str | None = None) -> Path:
    """Model, verification and render; files written in ``outdir``. ModelError → exit code 5 with the
    responses received so far in ``llm_raw.json``. With ``color`` («entrambi», M4) the files carry the color
    (``llm_raw_white.json``, …, ``analysis_white.md``) and :func:`join_both` writes ``analysis.md``."""
    name = (lambda n: per_color(n, color)) if color else (lambda n: n)
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
        (outdir / name("llm_raw.json")).write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
        raise ModelError(f"{e}; {hint}") from None
    finally:
        log.info("Risposte del modello ricevute: %d", len(raw))
    (outdir / name("llm_raw.json")).write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
    (outdir / name("verification.json")).write_text(json.dumps(res.verification, indent=1, ensure_ascii=False),
                                                    encoding="utf-8")
    (outdir / name("analysis.md")).write_text(res.document, encoding="utf-8")
    log.info("%s scritto (retry %d%s)", name("analysis.md"), res.retries, ", modalità degradata" if res.degraded else "")
    return outdir / name("analysis.md")


def join_both(outdir: Path, order: list[str]) -> Path:
    """«entrambi» (§2-bis.6): one ``analysis.md`` with the two perspectives, the color to move first."""
    parts = [(outdir / per_color("analysis.md", c)).read_text(encoding="utf-8").rstrip("\n") for c in order]
    (outdir / "analysis.md").write_text(BOTH_SEPARATOR.join(parts) + "\n", encoding="utf-8")
    for c in order:
        (outdir / per_color("analysis.md", c)).unlink()
    return outdir / "analysis.md"


def both_order(pos_board) -> list[str]:
    """The color to move first (§2-bis.6)."""
    import chess

    first = "w" if pos_board.turn == chess.WHITE else "b"
    return [first, "b" if first == "w" else "w"]


def rerun(cfg: Config, folder: Path, *, client=None, verbose: bool = False) -> Path:
    """Reads ``pack.json`` (plan and tables come from the pack, not from the current configuration),
    uses the current configuration for model, prompt, verification and render; previous files
    become ``*.prev.*``."""
    from chessanalyst.pack.schema import Pack

    pack_file = folder / "pack.json"
    both = [c for c in ("w", "b") if (folder / per_color("pack.json", c)).is_file()]   # «entrambi» (M4)
    if not pack_file.is_file() and len(both) != 2:
        raise UsageError(f"{folder} non contiene pack.json")
    files = {None: pack_file} if pack_file.is_file() else {c: folder / per_color("pack.json", c) for c in both}
    packs = {c: json.loads(Pack.model_validate_json(f.read_text(encoding="utf-8")).model_dump_json())
             for c, f in files.items()}
    handler = attach_run_log(folder / "run.log", verbose)
    try:
        log.info("rerun di %s", folder)
        warnings = []
        if any(p["config_hash"] != cfg.config_hash for p in packs.values()):
            log.warning("config_hash del pacchetto diverso da quello corrente: il pacchetto viene usato così com'è")
            warnings.append("config_hash diverso da quello corrente")
        names = list(TEXT_FILES) + [per_color(n, c) for n in TEXT_FILES[1:] for c in ("w", "b")]
        for name in names:
            if (folder / name).exists():
                (folder / name).replace(folder / _prev_name(name))
        if None in packs:
            return produce_text(cfg, folder, packs[None], client, warnings)
        import chess

        order = both_order(chess.Board(packs["w"]["position"]["fen"]))
        for c in order:
            produce_text(cfg, folder, packs[c], client, list(warnings), color=c)
        return join_both(folder, order)
    except AnalystError as e:          # expected: message on the console, no trace
        log.info("rerun interrotto: %s", e)
        raise
    except Exception:
        log.exception("rerun interrotto")
        raise
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()


def run_analysis(cfg: Config, pos: Position, us: UserSettings | list[UserSettings], out_base: Path, *,
                 verbose: bool = False, engines: Engines | None = None,
                 progress: Callable[[str], None] = lambda s: None, openings: OpeningIndex | None = None,
                 time_scale: float = 1.0, llm=None) -> Path:
    """``us`` is a list of two settings (White, Black) in «entrambi» mode (M4, §2-bis.6): two independent
    analyses on the same cache, so Stockfish analyses every node once; one ``analysis.md``."""
    both = isinstance(us, list)
    settings = us if both else [us]
    openings = openings if openings is not None else load_openings(cfg)
    found = openings.lookup(pos.board) if openings is not None else None
    entry = found[0] if found else None
    outdir = make_output_dir(out_base, entry["name"] if entry else None, pos.board.epd(en_passant="legal"),
                             cfg.default.output.slug_max_chars)
    handler = attach_run_log(outdir / "run.log", verbose)
    own = engines is None
    try:
        for u in settings:
            log.info("Analisi di %s (utente %s, Elo %s %s, profilo %s, dettaglio %s)", pos.fen, u.code, u.elo_declared,
                     u.elo_scale, u.budget_profile, u.detail_level)
        if pos.source == "pgn" and pos.game is not None:
            (outdir / "game.pgn").write_text(truncated_pgn(pos), encoding="utf-8")
        if own:
            engines = open_engines(cfg)
        order = both_order(pos.board) if both else [settings[0].code]
        by_color = {u.code: u for u in settings}
        packs = {}
        try:
            for c in order:
                packs[c] = analyse_position(cfg, pos, by_color[c], engines.analyzer, engines.maia, openings,
                                            progress=progress, time_scale=time_scale, tablebase=engines.tablebase)
        finally:
            if own:
                engines.close()
        for c in order:
            name = per_color("pack.json", c) if both else "pack.json"
            (outdir / name).write_text(packs[c].model_dump_json(indent=2), encoding="utf-8")
            log.info("%s scritto in %s", name, outdir)
        progress("modello di linguaggio, verifica e render")
        for c in order:
            produce_text(cfg, outdir, json.loads(packs[c].model_dump_json()), llm, color=c if both else None)
        if both:
            join_both(outdir, order)
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
