"""Recommended move, computed by code (§4.3, D-12, D-29)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Cand:
    cid: str
    loss_cp: int
    p_user: float
    complexity: int | None
    order: int          # E0 order (MultiPV rank; E4 moves after)


def rec_score(c: Cand, A: float, B: float) -> float:
    return -c.loss_cp + A * 100 * c.p_user - B * 50 * (c.complexity or 0)


def recommend(explained: list[Cand], L_max: int, A: float, B: float, tie_points: float,
              fallback: str = "C1") -> tuple[str, dict[str, float | None]]:
    """(recommended CID, rec_score by CID: rounded to 2 decimals, None if not eligible)."""
    eligible = [c for c in explained if c.loss_cp <= L_max]
    scores: dict[str, float | None] = {c.cid: None for c in explained}
    for c in eligible:
        scores[c.cid] = round(rec_score(c, A, B), 2)
    if not eligible:
        return fallback, scores
    raw = {c.cid: rec_score(c, A, B) for c in eligible}
    top = max(raw.values())
    tied = [c for c in eligible if top - raw[c.cid] < tie_points]
    tied.sort(key=lambda c: (c.complexity or 0, c.loss_cp, c.order))
    return tied[0].cid, scores
