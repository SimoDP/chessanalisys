"""``chessanalyst doctor``: environment checks (§11.3, AC-19).

One line per check with ``OK`` / ``AVVISO`` / ``ERRORE`` and the suggested fix
in Italian. Exit code 0 without ``ERRORE``, otherwise 4.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chess
import platformdirs

from chessanalyst import elo, exit_codes
from chessanalyst.config import Config
from chessanalyst.engines import syzygy
from chessanalyst.engines.maia2 import bucket, saturated
from chessanalyst.engines.openings import OpeningIndex

OK, WARN, ERR = "OK", "AVVISO", "ERRORE"
ANCHOR_ELOS = (1500, 1900, 2400)


@dataclass
class Check:
    name: str
    status: str
    detail: str
    fix: str = ""


def _python_check() -> Check:
    v = sys.version_info
    ver = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) in ((3, 11), (3, 12)):
        return Check("Python", OK, ver)
    return Check("Python", WARN, ver, "Usa Python 3.12 (o 3.11): maia2 richiede >=3.10,<3.13")


def _torch_check() -> Check:
    try:
        import torch
    except ImportError:
        return Check("PyTorch", ERR, "non installato", "pip install torch (CPU sufficiente)")
    device = "CUDA" if torch.cuda.is_available() else "CPU"
    if device == "CPU" and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "MPS"
    return Check("PyTorch", OK, f"{torch.__version__} · dispositivo {device}")


def _writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, delete=True):
            pass
        return True
    except OSError:
        return False


def _benchmark(cfg: Config, sf: Any) -> list[Check]:
    """E0 on the example position at the minimum root depth of ``fast``,
    MultiPV of ``standard``; estimate per profile = B × measured / reference."""
    ex = cfg.exploration
    depth = ex.profiles["fast"].dmin.root
    multipv = ex.profiles["standard"].multipv.root
    fen = (cfg.project_root / cfg.default.input.example_fen_file).read_text(encoding="utf-8").strip()
    board = chess.Board(fen)
    t0 = time.monotonic()
    res = sf.analyse_node(board, multipv=multipv, t_target=0.0, d_min=depth, t_cap=600.0)
    measured = time.monotonic() - t0
    out = [Check("Benchmark", OK, f"E0 MultiPV {multipv} a profondità {res.depth}: {measured:.1f} s")]
    ref = ex.reference_time_s
    if ref is None:
        out.append(Check("Stima tempi", WARN, "reference_time_s non impostato",
                         "Imposta reference_time_s in config/exploration.yaml (M0)"))
    else:
        parts = [f"{name} ≈ {p.B_s * measured / ref:.0f} s" for name, p in ex.profiles.items()]
        out.append(Check("Stima tempi", OK, " · ".join(parts)))
    return out


def run_doctor(
    cfg: Config,
    *,
    env: Mapping[str, str] | None = None,
    stockfish_factory: Callable[[Config], Any] | None = None,
    maia_factory: Callable[[Config], Any] | None = None,
    benchmark: bool = True,
) -> tuple[list[Check], int]:
    from chessanalyst.engines.factory import make_maia, make_stockfish, stockfish_path

    env = os.environ if env is None else env
    checks: list[Check] = [
        Check("Sistema operativo", OK, f"{platform.system()} {platform.release()} ({platform.machine()})"),
        _python_check(),
        _torch_check(),
    ]

    # Stockfish
    sf_cfg = cfg.default.engines.stockfish
    sf = None
    try:
        sf = (stockfish_factory or make_stockfish)(cfg)
        sf.open()
        version = sf.version
        checks.append(Check("Stockfish", OK, f"{stockfish_path(cfg) if stockfish_factory is None else 'personalizzato'}"
                                             f" · {version} · Threads {sf.threads} · Hash {sf.hash_mb} MB"))
        if sf_cfg.version_pin is None:
            checks.append(Check("Versione Stockfish", WARN, "version_pin non impostato",
                                "Imposta engines.stockfish.version_pin in config/default.yaml"))
        elif version != sf_cfg.version_pin:
            checks.append(Check("Versione Stockfish", WARN, f"{version} diversa dal pin {sf_cfg.version_pin}",
                                f"Installa {sf_cfg.version_pin} con scripts/setup_engines.py"))
        else:
            checks.append(Check("Versione Stockfish", OK, f"coincide con il pin {sf_cfg.version_pin}"))
    except Exception as e:  # noqa: BLE001 - reported to the user
        checks.append(Check("Stockfish", ERR, f"non disponibile: {e}", "Esegui `python scripts/setup_engines.py`"))
        sf = None

    # Maia-2
    m_cfg = cfg.default.engines.maia2
    try:
        maia = (maia_factory or make_maia)(cfg)
        info = maia.info()
        fen = (cfg.project_root / cfg.default.input.example_fen_file).read_text(encoding="utf-8").strip()
        t0 = time.monotonic()
        pol = maia.policy(fen, 1500, 1500)
        dt = time.monotonic() - t0
        top = max(pol, key=pol.get)
        checks.append(Check("Maia-2", OK, f"maia2 {info['package_version']} · modello {info['model_type']} · "
                                          f"{info['device']} · chiamata di prova {dt:.2f} s (prima mossa {top})"))
        if m_cfg.version_pin is not None and info["package_version"] != m_cfg.version_pin:
            checks.append(Check("Versione Maia-2", WARN, f"{info['package_version']} diversa dal pin {m_cfg.version_pin}",
                                f"pip install maia2=={m_cfg.version_pin}"))
    except Exception as e:  # noqa: BLE001
        checks.append(Check("Maia-2", ERR, f"non disponibile: {e}", "Esegui `python scripts/setup_engines.py`"))

    # Elo table for the anchors (AC-19)
    lim = cfg.maia2_limits
    rows = []
    for e_fide in ANCHOR_ELOS:
        e_maia = elo.fide_to_lichess(e_fide, cfg)
        rows.append(f"{e_fide} FIDE → {e_maia} → fascia {bucket(e_maia, lim)}"
                    f"{' (satura)' if saturated(e_maia, lim) else ''}")
    checks.append(Check("Elo Maia-2", OK, f"top_bucket_lower {lim.top_bucket_lower}: " + " · ".join(rows)))

    # Syzygy (SyzygyPath and direct probe from M2)
    tb_path = cfg.resolve_path(cfg.default.engines.syzygy.path)
    n = syzygy.complete_up_to(tb_path)
    if n >= 5:
        checks.append(Check("Syzygy", OK, f"{tb_path}: completo fino a {n} pezzi"))
    else:
        checks.append(Check("Syzygy", WARN, f"tablebase 3-4-5 incomplete ({n} pezzi) in {tb_path or 'percorso non configurato'}",
                            "Esegui `python scripts/setup_engines.py`: senza tablebase i finali con pochi pezzi restano in colonna 3"))

    # Openings index
    idx_path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    try:
        idx = OpeningIndex.load(idx_path)
        if idx.sequences:
            checks.append(Check("Indice aperture", OK, f"{len(idx)} voci, {len(idx.sequences)} sequenze"))
        else:                                      # M2: lookup by sequence (§3.3)
            checks.append(Check("Indice aperture", WARN, f"{len(idx)} voci, sequenze assenti",
                                "Esegui `python scripts/setup_engines.py --skip stockfish maia syzygy`"))
    except (OSError, ValueError) as e:
        checks.append(Check("Indice aperture", ERR, f"non leggibile: {e}", "Esegui `python scripts/setup_engines.py`"))

    # API key of the chosen provider (never printed, D-64)
    from chessanalyst.llm.client import API_KEY_ENV

    provider = cfg.default.llm.provider
    var = API_KEY_ENV[provider]
    if env.get(var):
        checks.append(Check(var, OK, f"presente (fornitore {provider}, modello {cfg.default.llm.model})"))
    else:
        checks.append(Check(var, WARN, f"assente (fornitore {provider}: serve per il testo dell'analisi, "
                                       "analyze e rerun)", f"Imposta la variabile d'ambiente {var}"))

    # Write permissions
    for label, path in (
        ("Cartella di output", cfg.resolve_path(cfg.default.output.dir)),
        ("Cache", Path(platformdirs.user_cache_dir("chessanalyst"))),
        ("Configurazione utente", Path(platformdirs.user_config_dir("chessanalyst"))),
    ):
        if _writable(path):
            checks.append(Check(label, OK, f"{path} scrivibile"))
        else:
            checks.append(Check(label, ERR, f"{path} non scrivibile", "Controlla i permessi della cartella"))

    if benchmark and sf is not None:
        try:
            checks.extend(_benchmark(cfg, sf))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("Benchmark", ERR, f"fallito: {e}"))
    if sf is not None:
        sf.close()

    code = exit_codes.ENVIRONMENT if any(c.status == ERR for c in checks) else exit_codes.OK
    return checks, code


def print_checks(checks: list[Check], console: Any | None = None) -> None:
    from rich.console import Console
    from rich.markup import escape

    console = console or Console()
    style = {OK: "green", WARN: "yellow", ERR: "red"}
    for c in checks:
        line = f"[{style[c.status]}]{c.status:<7}[/] {escape(c.name)}: {escape(c.detail)}"
        if c.fix and c.status != OK:
            line += f"\n        → {escape(c.fix)}"
        console.print(line, highlight=False)
