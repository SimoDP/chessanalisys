"""Elo scales, bands and anchors (§3-bis, D-05, D-38)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from chessanalyst.config import Config, Range


def round_half_away(x: float) -> int:
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)


def _interp(points: list[tuple[int, int]], x: float) -> float:
    """Piecewise linear; constant offset outside the points."""
    if not points:
        raise ValueError("tabella di conversione vuota")
    pts = sorted(points)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x1 <= x0 or y1 <= y0:
            raise ValueError("la tabella di conversione deve essere strettamente crescente")
    if x <= pts[0][0]:
        return x + (pts[0][1] - pts[0][0])
    if x >= pts[-1][0]:
        return x + (pts[-1][1] - pts[-1][0])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise AssertionError("unreachable")


def fide_to_lichess(elo: int, cfg: Config) -> int:
    return round_half_away(_interp(cfg.elo_conversion.fide_to_lichess, elo))


def lichess_to_fide(elo: int, cfg: Config) -> int:
    inverse = [(y, x) for x, y in cfg.elo_conversion.fide_to_lichess]
    return round_half_away(_interp(inverse, elo))


def _in(r: Range, value: int) -> bool:
    return (r.lo is None or value >= r.lo) and (r.hi is None or value < r.hi)


def band_of(elo_ref_fide: int, cfg: Config) -> str:
    for name, r in cfg.thresholds.bands.items():
        if _in(r, elo_ref_fide):
            return name
    raise ValueError(f"nessuna fascia per {elo_ref_fide}")


def anchor_of(elo_ref_fide: int, cfg: Config) -> str:
    for name, r in cfg.thresholds.anchors.items():
        if _in(r, elo_ref_fide):
            return name
    raise ValueError(f"nessuna ancora per {elo_ref_fide}")


@dataclass(frozen=True)
class EloInfo:
    declared: int
    scale: str
    ref_fide: int
    maia: int


def resolve(declared: int, scale: str, cfg: Config) -> EloInfo:
    if scale == "fide":
        return EloInfo(declared, scale, declared, fide_to_lichess(declared, cfg))
    if scale == "lichess":
        return EloInfo(declared, scale, lichess_to_fide(declared, cfg), declared)
    if scale == "chesscom":
        if not cfg.elo_conversion.chesscom_to_lichess:
            from chessanalyst.errors import UsageError

            raise UsageError("Scala chess.com non ancora configurata")
        maia = round_half_away(_interp(cfg.elo_conversion.chesscom_to_lichess, declared))
        return EloInfo(declared, scale, lichess_to_fide(maia, cfg), maia)
    raise ValueError(f"scala Elo sconosciuta: {scale}")
