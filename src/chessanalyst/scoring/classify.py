"""Automatic classification (§4.2, D-25, D-36): first true condition wins."""

from __future__ import annotations

from chessanalyst.config import Classification


def classify(p_user: float, loss_cp: int, complexity: int | None, p_up: float | None, band: str,
             th: Classification) -> str | None:
    nt = th.natural_trap
    loss_min = nt.loss_min_low_bands if band in nt.low_bands else nt.loss_min
    if p_user >= nt.p_user_min and loss_cp >= loss_min:
        return "natural_trap"
    if p_user < th.hard_move.p_user_max and loss_cp <= th.hard_move.loss_max:
        return "hard_move"
    if p_user >= th.solid.p_user_min and loss_cp <= th.solid.loss_max:
        return "solid"
    pa = th.practical_alt
    if pa.loss_gt < loss_cp <= pa.max_loss and complexity is not None and complexity <= pa.complexity_max:
        return "practical_alt"
    ie = th.improbable_error
    if p_up is not None and p_user < ie.p_user_max and loss_cp >= ie.loss_min and p_up >= ie.p_up_min:
        return "improbable_error"
    return None
