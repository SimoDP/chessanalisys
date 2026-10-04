"""``chessanalyst golden --packs`` (§8-bis.4 M1b, step 1).

Runs the pipeline (profile ``deep``, E3 at ℓ1–ℓ3 from M2) on the example
position for the three anchors (user White, 1500/1900/2400 FIDE) and on the
AC-21 fixture (``najdorf_after_be3``, 1900, used by ``_s07_alt.json``), and
freezes the packs in ``examples/golden/packs/``. From M2 it also freezes the
packs of the non-Najdorf fixtures with a checklist (§8-bis.6) in
``fixtures/packs/``. Existing packs are overwritten only with ``force`` (the
fewshot IDs and the recorded model answers depend on them).
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
from chessanalyst.inputs.pgn import position_from_game, read_games
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings

PROFILE = "deep"
ANCHORS = ("1500", "1900", "2400")


@dataclass(frozen=True)
class GoldenPack:
    name: str            # file stem, e.g. "najdorf_w_1900"
    fen_file: str        # FEN or PGN file, relative to the project root
    color: str
    elo: int
    folder: str = "examples/golden/packs"


# Non-Najdorf positions with a checklist (§8-bis.6, M2): fixtures/checklists/<name>.yaml
CHECKLIST_PACKS = (
    GoldenPack("fried_liver_w_1500", "fixtures/pgn/fried_liver.pgn", "w", 1500, "fixtures/packs"),
    GoldenPack("rook_endgame_w_1900", "fixtures/positions/rook_endgame.fen", "w", 1900, "fixtures/packs"),
    GoldenPack("lucena_w_1900", "fixtures/positions/lucena.fen", "w", 1900, "fixtures/packs"),
)


def golden_pack_specs() -> list[GoldenPack]:
    specs = [GoldenPack(f"najdorf_w_{a}", "fixtures/positions/najdorf.fen", "w", int(a)) for a in ANCHORS]
    specs.append(GoldenPack("najdorf_after_be3_w_1900", "fixtures/positions/najdorf_after_be3.fen", "w", 1900))
    return specs + list(CHECKLIST_PACKS)


def packs_dir(cfg: Config) -> Path:
    return cfg.project_root / "examples" / "golden" / "packs"


def pack_path(cfg: Config, name: str) -> Path:
    spec = next((s for s in golden_pack_specs() if s.name == name), None)
    folder = cfg.project_root / spec.folder if spec is not None else packs_dir(cfg)
    return folder / f"{name}.pack.json"


def spec_position(cfg: Config, spec: GoldenPack) -> Position:
    """FEN file, or the end of the main line of a PGN (with its history)."""
    text = (cfg.project_root / spec.fen_file).read_text(encoding="utf-8")
    if spec.fen_file.endswith(".pgn"):
        return position_from_game(read_games(text)[0], cfg.wording["errors"])
    return Position(board=parse_fen(text, cfg.wording["errors"]), source="fen")


def load_frozen_pack(cfg: Config, name: str) -> dict:
    return json.loads(pack_path(cfg, name).read_text(encoding="utf-8"))


def check_overwrite(cfg: Config, force: bool) -> None:
    """Frozen packs are overwritten only on purpose (exit code 2 otherwise)."""
    if not force and any(pack_path(cfg, s.name).is_file() for s in golden_pack_specs()):
        raise UsageError("I pacchetti golden esistono già (sono congelati): usa --force per rigenerarli "
                         "e poi riallinea i fewshot")


def golden_packs(cfg: Config, analyzer, maia, openings: OpeningIndex | None, *, force: bool = False,
                 time_scale: float = 1.0, progress: Callable[[str], None] = print, tablebase=None) -> list[Path]:
    check_overwrite(cfg, force)
    specs = golden_pack_specs()
    written = []
    for s in specs:
        progress(f"== {s.name} · profilo {PROFILE}")
        pos = spec_position(cfg, s)
        us = resolve_settings(cfg, s.color, s.elo, "fide", None, PROFILE)
        pack = analyse_position(cfg, pos, us, analyzer, maia, openings,
                                progress=lambda m: progress(f"   {m}"), time_scale=time_scale, tablebase=tablebase)
        out = pack_path(cfg, s.name)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(pack.model_dump_json(indent=2) + "\n", encoding="utf-8")
        written.append(out)
    return written
