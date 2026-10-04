"""``chessanalyst golden --packs`` (§8-bis.4 M1b, step 1).

Runs the M1a pipeline (profile ``deep``, E3 at ℓ1) on the example position for
the three anchors (user White, 1500/1900/2400 FIDE) and on the AC-21 fixture
(``najdorf_after_be3``, 1900, used by ``_s07_alt.json``), and freezes the packs
in ``examples/golden/packs/``. Existing packs are overwritten only with
``force`` (the fewshot IDs depend on them).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from chessanalyst.config import Config
from chessanalyst.engines.openings import OpeningIndex
from chessanalyst.errors import UsageError
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings

PROFILE = "deep"
ANCHORS = ("1500", "1900", "2400")


@dataclass(frozen=True)
class GoldenPack:
    name: str            # file stem, e.g. "najdorf_w_1900"
    fen_file: str        # relative to the project root
    color: str
    elo: int


def golden_pack_specs() -> list[GoldenPack]:
    specs = [GoldenPack(f"najdorf_w_{a}", "fixtures/positions/najdorf.fen", "w", int(a)) for a in ANCHORS]
    specs.append(GoldenPack("najdorf_after_be3_w_1900", "fixtures/positions/najdorf_after_be3.fen", "w", 1900))
    return specs


def packs_dir(cfg: Config) -> Path:
    return cfg.project_root / "examples" / "golden" / "packs"


def pack_path(cfg: Config, name: str) -> Path:
    return packs_dir(cfg) / f"{name}.pack.json"


def load_frozen_pack(cfg: Config, name: str) -> dict:
    return json.loads(pack_path(cfg, name).read_text(encoding="utf-8"))


def check_overwrite(cfg: Config, force: bool) -> None:
    """Frozen packs are overwritten only on purpose (exit code 2 otherwise)."""
    if not force and any(pack_path(cfg, s.name).is_file() for s in golden_pack_specs()):
        raise UsageError("I pacchetti golden esistono già (sono congelati): usa --force per rigenerarli "
                         "e poi riallinea i fewshot")


def golden_packs(cfg: Config, analyzer, maia, openings: OpeningIndex | None, *, force: bool = False,
                 time_scale: float = 1.0, progress: Callable[[str], None] = print) -> list[Path]:
    check_overwrite(cfg, force)
    specs = golden_pack_specs()
    packs_dir(cfg).mkdir(parents=True, exist_ok=True)
    written = []
    for s in specs:
        progress(f"== {s.name} · profilo {PROFILE}")
        board = parse_fen((cfg.project_root / s.fen_file).read_text(encoding="utf-8"), cfg.wording["errors"])
        us = resolve_settings(cfg, s.color, s.elo, "fide", None, PROFILE)
        pack = analyse_position(cfg, Position(board=board, source="fen"), us, analyzer, maia, openings,
                                progress=lambda m: progress(f"   {m}"), time_scale=time_scale)
        out = pack_path(cfg, s.name)
        out.write_text(pack.model_dump_json(indent=2) + "\n", encoding="utf-8")
        written.append(out)
    return written
