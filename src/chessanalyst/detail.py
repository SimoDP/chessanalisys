"""Detail level 1–5 (§7.2, M4): effective K, maximum line length, E3 below the mandatory Elo."""

from __future__ import annotations

from chessanalyst.config import BandParams, Config


def effective_k(cfg: Config, band: str, detail: int) -> int:
    bp = cfg.thresholds.band_params[band]
    rule = cfg.thresholds.detail[str(detail)].k
    if rule == "explained_min":
        return bp.explained_min
    if rule == "explained_min_plus_1":
        return min(bp.explained_min + 1, bp.K)
    return bp.K


def effective_band(cfg: Config, band: str, detail: int) -> BandParams:
    """The band parameters with the K of the detail level (selection of the explained candidates)."""
    return cfg.thresholds.band_params[band].model_copy(update={"K": effective_k(cfg, band, detail)})


def plies_max(cfg: Config, band: str, detail: int) -> int:
    lo, hi = cfg.thresholds.plies_bounds
    bp = cfg.thresholds.band_params[band]
    return max(lo, min(hi, bp.plies_max + cfg.thresholds.detail[str(detail)].plies_delta))


def e3_active(cfg: Config, elo_ref_fide: int, detail: int) -> bool:
    """§7.1: E3 is mandatory from ``e3_mandatory_from`` and below it active only with detail >= ``e3_min_detail``."""
    r = cfg.thresholds.elo_rules
    return elo_ref_fide >= r.e3_mandatory_from or detail >= r.e3_min_detail
