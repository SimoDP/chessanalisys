"""T4, the radar of the categories (§8.5, S02, M3): rows ordered by decreasing R."""

from __future__ import annotations

from typing import Any

from chessanalyst.config import Config
from chessanalyst.pack.tables import _columns


def radar_order(categories: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    """By R decreasing; ties in the order of §5-bis.1."""
    return sorted(categories, key=lambda c: (-c["R"], order.index(c["id"])))


def build_t4(cfg: Config, anchor: str, categories: list[dict[str, Any]], user: str, opp_t: bool = False) -> dict | None:
    """``opp_t``: also the opponent's T (detail 5, §7.2), after the user's."""
    if not categories:
        return None
    spec = dict(cfg.tables["T4"])
    if opp_t:
        data = list(spec["data"])
        data.insert(data.index("T") + 1, "T_opp")
        spec["data"] = data
    low = any(c["confidence"] == "low" for c in categories)
    cols = _columns(cfg, spec)
    if low:
        for c in cols:
            if c["key"] in ("T", "T_opp"):
                c["header"] += "*"
    rows = []
    for c in radar_order(categories, cfg.thresholds.scoring.categories)[: spec["rows_max"][anchor]]:
        cells: dict[str, Any] = {"category": cfg.wording["score_categories"][c["id"]], "T": str(c["T"][user]),
                                 "R": str(c["R"])}
        if opp_t:
            cells["T_opp"] = str(c["T"]["b" if user == "w" else "w"])
        cells.update({k: None for k in spec.get("text", [])})
        rows.append({"id": c["id"], "cells": cells})
    return {"id": "T4", "section": "S02", "columns": cols, "rows": rows,
            "footnote": cfg.wording["fixed"]["score_low_confidence_table"] if low else None}
