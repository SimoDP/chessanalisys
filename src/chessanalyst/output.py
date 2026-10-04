"""Output folder and run log (§2-bis.5)."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path

SLUG_MAX = 40


def slug(opening_name: str | None, epd: str) -> str:
    if not opening_name:
        return "pos_" + hashlib.sha1(epd.encode("utf-8")).hexdigest()[:8]
    ascii_ = unicodedata.normalize("NFKD", opening_name).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", ascii_).strip("_")[:SLUG_MAX]


def make_output_dir(base: Path, opening_name: str | None, epd: str, now: datetime | None = None) -> Path:
    now = now or datetime.now()
    name = f"{now:%Y%m%d_%H%M}_{slug(opening_name, epd)}"
    path = base / name
    k = 2
    while path.exists():
        path = base / f"{name}_{k}"
        k += 1
    path.mkdir(parents=True)
    return path


def attach_run_log(path: Path, verbose: bool) -> logging.Handler:
    """``run.log`` at DEBUG; UCI traffic (logger ``chess.engine``) only with --verbose."""
    h = logging.FileHandler(path, encoding="utf-8")
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    if not verbose:
        h.addFilter(lambda r: not r.name.startswith("chess.engine"))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(h)
    return h
