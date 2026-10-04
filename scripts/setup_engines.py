"""Install the local components (§11.3). Idempotent.

* Stockfish at ``engines.stockfish.version_pin``: an existing binary with the
  pinned version (``--stockfish-path``, ``stockfish`` on PATH, ``/usr/games``)
  is reused; otherwise the official release asset is downloaded.
* Maia-2 weights: ``maia2.model.from_pretrained`` once (Google Drive).
* Syzygy 3-4-5 from tablebase.lichess.ovh (O-8).
* ``lichess-org/chess-openings`` TSV files and ``data/openings_index.json``.

Writes the paths into ``config/local.yaml``. Every download shows the expected
size and asks for confirmation unless ``--yes``.
"""

from __future__ import annotations

import argparse
import io
import platform
import re
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chessanalyst.config import load_config, write_local_config  # noqa: E402
from chessanalyst.engines import syzygy  # noqa: E402
from chessanalyst.engines.openings import TSV_FILES, build_index_from_dir, write_index  # noqa: E402

OPENINGS_URL = "https://raw.githubusercontent.com/lichess-org/chess-openings/master/{name}"
# WDL and DTZ files live in two folders (verified in M0).
SYZYGY_URLS = (
    "https://tablebase.lichess.ovh/tables/standard/3-4-5-wdl/",
    "https://tablebase.lichess.ovh/tables/standard/3-4-5-dtz/",
)
# Release assets of the official repository; names in stockfish_asset(). In M2 the
# direct asset download works (the release page and the API are still blocked).
SF_RELEASE = "https://github.com/official-stockfish/Stockfish/releases/download/sf_{num}/{asset}"


def ask(question: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    return input(f"{question} [s/n] ").strip().lower() in ("s", "si", "sì", "y", "yes")


def head_size(url: str) -> int | None:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            n = r.headers.get("Content-Length")
            return int(n) if n else None
    except OSError:
        return None


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def human(n: int | None) -> str:
    if n is None:
        return "dimensione sconosciuta"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# --- Stockfish ---------------------------------------------------------------


def stockfish_asset(num: int) -> str:
    """Release asset for this machine. From Stockfish 19 the releases ship universal
    binaries that detect the CPU features (names verified on stockfishchess.org/download,
    October 2026); before, one asset per instruction set (Stockfish 16-18)."""
    system, machine = platform.system(), platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    if num >= 19:
        if system == "Linux":
            return "stockfish-linux-arm64-universal.tar.gz" if arm else "stockfish-linux-x86-64-universal.tar.gz"
        if system == "Darwin":
            return "stockfish-macos-universal.tar.gz"
        if system == "Windows":
            return "stockfish-windows-arm64-universal.zip" if arm else "stockfish-windows-x86-64-universal.zip"
        raise SystemExit(f"Sistema non supportato: {system}")
    avx2 = False
    try:
        avx2 = "avx2" in Path("/proc/cpuinfo").read_text()
    except OSError:
        pass
    if system == "Linux":
        return "stockfish-ubuntu-x86-64-avx2.tar" if avx2 else "stockfish-ubuntu-x86-64.tar"
    if system == "Darwin":
        return "stockfish-macos-m1-apple-silicon.tar" if arm else "stockfish-macos-x86-64-avx2.tar"
    if system == "Windows":
        return "stockfish-windows-x86-64-avx2.zip"
    raise SystemExit(f"Sistema non supportato: {system}")


def engine_name(path: Path) -> str | None:
    """Engine name read through the Stockfish adapter (the only module that drives UCI)."""
    from chessanalyst.engines.stockfish import StockfishEngine
    from chessanalyst.errors import EnvironmentProblem

    try:
        with StockfishEngine(path, hash_mb=16, poll_s=0.05, threads=1) as sf:
            return sf.version
    except EnvironmentProblem:
        return None


def setup_stockfish(cfg, args) -> Path | None:
    pin = cfg.default.engines.stockfish.version_pin
    candidates = [Path(p) for p in (args.stockfish_path, shutil.which("stockfish"), "/usr/games/stockfish") if p]
    for c in candidates:
        if c.is_file():
            name = engine_name(c)
            if name and (pin is None or name == pin):
                print(f"Stockfish: uso {c} ({name})")
                return c.resolve()
            print(f"Stockfish: {c} è {name}, diverso dal pin {pin}")
    if pin is None:
        print("Stockfish: version_pin non impostato e nessun binario trovato")
        return None
    num = pin.split()[-1]
    asset = stockfish_asset(int(num))
    url = SF_RELEASE.format(num=num, asset=asset)
    if not ask(f"Scaricare {asset} ({human(head_size(url))})?", args.yes):
        return None
    try:
        blob = fetch(url)
    except OSError as e:
        print(f"Stockfish: download fallito ({e}). Installa {pin} a mano e passa --stockfish-path.")
        return None
    dest = ROOT / "data" / "stockfish"
    dest.mkdir(parents=True, exist_ok=True)
    if asset.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(blob)).extractall(dest)
    else:
        tarfile.open(fileobj=io.BytesIO(blob)).extractall(dest, filter="data")
    exe = next((p for p in dest.rglob("stockfish*") if p.is_file() and p.suffix not in (".tar", ".gz", ".zip", ".txt", ".md")), None)
    if exe is None:
        print("Stockfish: eseguibile non trovato nell'archivio")
        return None
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    print(f"Stockfish: installato in {exe} ({engine_name(exe)})")
    return exe


# --- Maia-2 ------------------------------------------------------------------


def setup_maia(cfg, args) -> bool:
    from chessanalyst.engines.factory import maia_models_dir
    from chessanalyst.engines.maia2 import weights_file

    m = cfg.default.engines.maia2
    mdir = maia_models_dir(cfg)
    if weights_file(mdir, m.model_type).is_file():
        print(f"Maia-2: pesi {m.model_type} già presenti in {mdir}")
        return True
    if not ask(f"Scaricare i pesi di Maia-2 ({m.model_type}, circa 270 MB) da Google Drive?", args.yes):
        return False
    try:
        from chessanalyst.engines.maia2 import Maia2Backend

        Maia2Backend(m.model_type, "cpu", mdir)   # the adapter downloads and checks the weights
    except Exception as e:  # noqa: BLE001
        print(f"Maia-2: download fallito ({e})")
        return False
    print(f"Maia-2: pesi in {mdir}")
    return True


# --- Syzygy ------------------------------------------------------------------


def setup_syzygy(cfg, args) -> Path | None:
    dest = cfg.resolve_path(cfg.default.engines.syzygy.path) or (ROOT / "data" / "syzygy")
    if syzygy.complete_up_to(dest) >= 5:
        print(f"Syzygy: 3-4-5 già complete in {dest}")
        return dest
    files: list[tuple[str, str]] = []
    for base in SYZYGY_URLS:
        try:
            listing = fetch(base).decode("utf-8", "replace")
        except OSError as e:
            print(f"Syzygy: elenco non raggiungibile ({e})")
            return None
        names = sorted(set(re.findall(r'href="([KQRBNP]+v[KQRBNP]+\.rtb[wz])"', listing)))
        files.extend((base, n) for n in names)
    if not ask(f"Scaricare {len(files)} file Syzygy 3-4-5 (circa 1 GB)?", args.yes):
        return None
    dest.mkdir(parents=True, exist_ok=True)
    for i, (base, name) in enumerate(files, 1):
        target = dest / name
        if target.is_file() and target.stat().st_size > 0:
            continue
        print(f"Syzygy [{i}/{len(files)}] {name}")
        part = target.with_name(target.name + ".part")
        part.write_bytes(fetch(base + name))
        part.replace(target)
    return dest


# --- Openings ----------------------------------------------------------------


def setup_openings(cfg, args) -> Path | None:
    src = ROOT / "data" / "openings"
    src.mkdir(parents=True, exist_ok=True)
    for name in TSV_FILES:
        target = src / name
        if target.is_file() and target.stat().st_size > 0:
            continue
        url = OPENINGS_URL.format(name=name)
        try:
            target.write_bytes(fetch(url))
        except OSError as e:
            print(f"Aperture: download di {name} fallito ({e})")
            return None
    index_path = cfg.resolve_path(cfg.default.engines.openings.index_file)
    sequences: dict[str, dict] = {}
    index = build_index_from_dir(src, sequences)
    write_index(index, index_path, sequences)
    print(f"Aperture: {len(index)} posizioni in {index_path}")
    return index_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Installa Stockfish, Maia-2, Syzygy e l'indice delle aperture")
    ap.add_argument("--yes", action="store_true", help="non chiedere conferma")
    ap.add_argument("--stockfish-path", help="usa questo eseguibile di Stockfish")
    ap.add_argument("--skip", nargs="*", default=[], choices=["stockfish", "maia", "syzygy", "openings"])
    args = ap.parse_args(argv)
    cfg = load_config(ROOT)
    local: dict = {}
    failures = []
    if "stockfish" not in args.skip:
        p = setup_stockfish(cfg, args)
        if p:
            local.setdefault("engines", {})["stockfish"] = {"path": str(p)}
        else:
            failures.append("stockfish")
    if "maia" not in args.skip and not setup_maia(cfg, args):
        failures.append("maia")
    if "syzygy" not in args.skip:
        p = setup_syzygy(cfg, args)
        if p:
            local.setdefault("engines", {})["syzygy"] = {"path": str(p)}
        else:
            failures.append("syzygy")
    if "openings" not in args.skip and not setup_openings(cfg, args):
        failures.append("openings")
    if local:
        print(f"Configurazione locale: {write_local_config(ROOT, local)}")
    if failures:
        print(f"Componenti non installati: {', '.join(failures)}. Controlla con `chessanalyst doctor`.")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
