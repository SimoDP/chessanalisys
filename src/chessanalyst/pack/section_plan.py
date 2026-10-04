"""SectionPlan (§8.2–§8.4, D-27, D-45, D-54, D-57).

Rules are applied in the order matrix → milestone → anchor → opponent mode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from chessanalyst.config import Config, SECTION_IDS

# Matrix of §8.2: "req" mandatory, "cN" conditional, None omitted, per column 1..4.
MATRIX: dict[str, tuple] = {
    "S01": ("req", "req", "req", "req"),
    "S02": ("req", "req", "req", None),
    "S03": ("req", "c3", None, None),
    "S04": ("c4", "c4", None, None),
    "S05": ("req", "c5", None, None),
    "S06": ("req", "req", "req", "req"),
    "S07": ("req", "req", "req", "req"),
    "S08": ("c8", "c8", "c8", None),
    "S09": ("req", "req", "c9", None),
    "S10": ("req", "req", "req", "req"),
    "S11": ("c11", "c11", "c11", None),
    "S12": (None, None, "req", "req"),
    "S13": (None, "req", None, None),
}
# Sections available in the current milestone (§8.3, M3): S02 and S09 from M3, S11 arrives in M4.
MILESTONE_SECTIONS = ("S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S12", "S13")
THEORY = {"S01": False, "S02": False, "S03": True, "S04": True, "S05": True, "S06": True, "S07": False,
          "S08": False, "S09": False, "S10": True, "S11": True, "S12": True, "S13": False}
COUNTING_C8 = ("natural_trap", "hard_move", "practical_alt", "improbable_error")
COUNTING_C8_2400 = ("natural_trap", "hard_move")
CASTLING_OPEN = ("can_both", "can_short", "can_long")


@dataclass
class PlanInput:
    anchor: str
    band: str
    elo_ref_fide: int
    matrix_column: int
    castling: dict[str, str]                 # {"w": ..., "b": ...}
    user_to_move: bool
    opp_color_name: str                      # "il Bianco" / "il Nero"
    explained: list[str] = field(default_factory=list)       # CIDs
    explained_low_loss: int = 0              # explained with loss_cp ≤ 30 (c3)
    categories: dict[str, str | None] = field(default_factory=dict)   # CID → category
    replies: list[str] = field(default_factory=list)         # RIDs
    recommendation: str | None = None
    has_t2: bool = False
    has_t3: bool = False
    maia_low: bool = False
    detail: int = 4
    focus_squares: list[str] = field(default_factory=list)   # c5 (column 2)
    tablebase: bool = False                  # exact result at the root: S12 must cite N1
    has_t4: bool = False                     # radar (M3)
    invisible_lines: list[str] = field(default_factory=list)  # L<n> with visible_at_level false (c9, S09)


def fill_opp(text: str, opp: str) -> str:
    """Replace ``{opp}``; «di il Nero» becomes «del Nero»."""
    if opp.startswith("il "):
        text = text.replace("di {opp}", "del " + opp[3:])
    return text.replace("{opp}", opp)


def _round_tens(x: float) -> int:
    return int(math.floor(x / 10 + 0.5)) * 10


def build_section_plan(cfg: Config, pi: PlanInput) -> tuple[list[dict], list[dict], list[str]]:
    """(plan entries, omitted_sections, header warnings)."""
    col = pi.matrix_column
    status: dict[str, dict] = {s: {"omitted": None, "absorbed_into": None} for s in SECTION_IDS}
    warnings: list[str] = []
    c8_cats = COUNTING_C8_2400 if pi.anchor == "2400" else COUNTING_C8
    c8_moves = sorted((c for c, cat in pi.categories.items() if cat in c8_cats), key=lambda c: int(c[1:]))

    def omit(s: str, reason: str) -> None:
        if status[s]["omitted"] is None and status[s]["absorbed_into"] is None:
            status[s]["omitted"] = reason

    # 1. matrix
    for s in SECTION_IDS:
        rule = MATRIX[s][col - 1]
        if rule is None:
            omit(s, "matrix")
        elif rule == "c3" and pi.explained_low_loss < 2:
            omit(s, "matrix")
        elif rule == "c4" and not any(pi.castling.get(side) in CASTLING_OPEN for side in ("w", "b")):
            omit(s, "matrix")
        elif rule == "c5" and not pi.focus_squares:
            omit(s, "matrix")
        elif rule == "c8" and not c8_moves and pi.anchor != "1500" and pi.user_to_move:
            # always present at 1500 (D-48); with the opponent to move the reason is opponent_to_move (D-54)
            omit(s, "no_classified_move")
        elif rule == "c9" and not pi.invisible_lines:
            omit(s, "no_invisible_line")
        elif rule == "c11" and not (pi.elo_ref_fide >= cfg.thresholds.elo_rules.s11_from or pi.detail == 5):
            omit(s, "elo<2000")
    # 2. milestone
    for s in SECTION_IDS:
        if s not in MILESTONE_SECTIONS:
            omit(s, "milestone")
    # 3. anchor (§8.2-bis)
    if pi.anchor == "1500":
        omit("S11", "band_1500")
    if pi.anchor == "2400":
        omit("S05", "band_2400")
        omit("S10", "band_2400")
    if pi.anchor in ("1500", "2400") and status["S04"]["omitted"] is None:
        if pi.user_to_move and status["S03"]["omitted"] is None:
            status["S04"]["absorbed_into"] = "S03"
        else:
            status["S04"]["omitted"] = "opponent_to_move" if not pi.user_to_move else status["S03"]["omitted"]
    # 4. opponent to move (D-54)
    if not pi.user_to_move:
        for s in ("S03", "S08"):
            if status[s]["omitted"] is None:
                status[s]["omitted"] = "opponent_to_move"

    bp = cfg.thresholds.band_params[pi.band]
    detail = cfg.thresholds.detail[str(pi.detail)]
    total = bp.prose_words * detail.words
    weights = cfg.section_budget[pi.anchor]
    required = [s for s in SECTION_IDS if status[s]["omitted"] is None and status[s]["absorbed_into"] is None]
    w = {s: weights.get(s, 0.0) + sum(weights.get(a, 0.0) for a in SECTION_IDS if status[a]["absorbed_into"] == s)
         for s in required}
    wsum = sum(w.values()) or 1.0
    titles = cfg.section_titles
    plies = max(2, bp.plies_max + detail.plies_delta)

    plan, omitted = [], []
    for s in SECTION_IDS:
        st = status[s]
        req = s in required
        title = None
        if req:
            key = "S07_alt" if (s == "S07" and not pi.user_to_move) else s
            t = titles[key][pi.anchor]
            title = fill_opp(t, pi.opp_color_name) if t else t
        tables: list[str] = []
        must: list[str] = []
        t2_anchors = cfg.tables["T2"]["anchors"] + (cfg.tables["T2"]["detail5_anchors"] if pi.detail == 5 else [])
        if req and s == "S07":
            tables = ["T1"] + (["T2"] if pi.has_t2 and pi.user_to_move and pi.anchor in t2_anchors else [])
            must = list(pi.explained) if pi.user_to_move else list(pi.replies)
        if req and s == "S06" and pi.has_t3 and pi.user_to_move and pi.anchor in cfg.tables["T3"]["anchors"]:
            tables = ["T3"]
        if req and s == "S08":
            must = c8_moves
        if req and s == "S03" and pi.anchor == "1500" and pi.recommendation:
            must = [pi.recommendation]
        if req and s == "S02" and pi.has_t4:
            tables = ["T4"]
        if req and s == "S09":
            must = list(pi.invisible_lines)
        if req and s == "S12" and pi.tablebase:
            must = ["N1"]
        theory = THEORY[s] or (s == "S08" and pi.anchor == "1500")
        plan.append({
            "id": s, "title": title, "required": req, "absorbed_into": st["absorbed_into"],
            "omitted": st["omitted"], "word_budget": _round_tens(total * w[s] / wsum) if req else None,
            "max_pv_plies": plies, "theory_allowed": theory, "tables": tables, "must_cover": must,
            "focus_squares": list(pi.focus_squares) if (req and s == "S05" and col == 2) else [],
            "maia_low_confidence": bool(req and pi.maia_low and s in ("S06", "S08")),
        })
        if st["omitted"] is not None:
            omitted.append({"id": s, "reason": st["omitted"]})
    return plan, omitted, warnings
