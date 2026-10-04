"""Build engines from the configuration."""

from __future__ import annotations

import shutil
from pathlib import Path

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache
from chessanalyst.engines.maia2 import Maia2Backend, MaiaEngine, weights_file
from chessanalyst.errors import EnvironmentProblem


def stockfish_path(cfg: Config) -> Path | None:
    """``engines.stockfish.path`` (written by setup_engines.py), else ``stockfish`` on PATH."""
    configured = cfg.resolve_path(cfg.default.engines.stockfish.path)
    if configured is not None:
        return configured
    found = shutil.which("stockfish")
    return Path(found) if found else None


def make_stockfish(cfg: Config):
    from chessanalyst.engines.stockfish import StockfishEngine

    path = stockfish_path(cfg)
    if path is None or not path.is_file():
        raise EnvironmentProblem(
            "Stockfish non trovato: esegui `python scripts/setup_engines.py` oppure imposta "
            "engines.stockfish.path in config/local.yaml"
        )
    sf = cfg.default.engines.stockfish
    return StockfishEngine(path, hash_mb=sf.hash_mb, poll_s=sf.poll_s, ram_fraction=sf.hash_max_ram_fraction,
                           syzygy_path=syzygy_dir(cfg))


def syzygy_dir(cfg: Config) -> Path | None:
    """Folder of the Syzygy tables if present (``engines.syzygy.path``), else None."""
    from chessanalyst.engines.syzygy import complete_up_to

    path = cfg.resolve_path(cfg.default.engines.syzygy.path)
    return path if path is not None and complete_up_to(path) > 0 else None


def make_tablebase(cfg: Config):
    """Direct probe of the tables (M2), or None when they are not installed."""
    from chessanalyst.engines.syzygy import Tablebase

    path = syzygy_dir(cfg)
    return Tablebase(path, cfg.default.engines.syzygy.max_pieces) if path is not None else None


def maia_models_dir(cfg: Config) -> Path:
    return cfg.project_root / "data" / "maia2_models"


def make_maia(cfg: Config, cache: Cache | None = None, allow_download: bool = False) -> MaiaEngine:
    m = cfg.default.engines.maia2
    mdir = maia_models_dir(cfg)
    if not allow_download and not weights_file(mdir, m.model_type).is_file():
        raise EnvironmentProblem(
            f"Pesi di Maia-2 ({m.model_type}) assenti in {mdir}: esegui `python scripts/setup_engines.py`"
        )
    backend = Maia2Backend(m.model_type, m.device, mdir)
    return MaiaEngine(backend, cfg.maia2_limits, cache)
