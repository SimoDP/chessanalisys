"""Category Scoring Engine: tags, T (static, dynamic, combined), balance, R, confidence (§5-bis, M3).

Every number is traceable: each category lists the root features (indexes into ``pack.features``),
the lines (``L<n>`` of ``filtered_lines``) and, for ``practical_complexity``, the nodes it comes from.
"""

from __future__ import annotations

import math
from typing import Any

import chess

from chessanalyst.config import Config, ScoringCfg
from chessanalyst.features.model import Feature
from chessanalyst.features.profile import m3_features, phase_of, static_features
from chessanalyst.features.see import see_move
from chessanalyst.features.tactics import tempo_counts
from chessanalyst.scoring.filter import ScoredLine

TACTICAL_KEYS = ("hanging_piece", "fork", "skewer", "pin", "overloaded_piece")
KING_KEYS = ("pawn_shield_weakened", "open_file_to_king", "castling_lost")
WEAK_PAWN_KEYS = ("isolated_pawn", "doubled_pawn", "backward_pawn")
ACTIVE_KEYS = ("knight_outpost", "rook_open_file", "rook_seventh", "bishop_diagonal_open")


def _other(s: str) -> str:
    return "b" if s == "w" else "w"


# -- tags (§5-bis.4 point 1) ---------------------------------------------------


def quiescent_leaf(start: chess.Board, plies: list[str], horizon: int, see_min: int, max_extra: int) -> chess.Board:
    """Leaf of a line after quiescence: the first ``horizon`` half-moves, then the line itself while its next
    move is a capture or a check (at most ``max_extra``); if the line ends first, the best capture with
    SEE >= ``see_min`` is played while there is one (same bound)."""
    b = start.copy(stack=False)
    moves = []
    for san in plies:
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        moves.append(mv)
        b.push(mv)
    b = start.copy(stack=False)
    for mv in moves[:horizon]:
        b.push(mv)
    extra = 0
    k = min(horizon, len(moves))
    while extra < max_extra and k < len(moves) and (b.is_capture(moves[k]) or b.gives_check(moves[k])):
        b.push(moves[k])
        k += 1
        extra += 1
    if k >= len(moves):
        while extra < max_extra:
            caps = [(see_move(b, m), m.uci(), m) for m in b.legal_moves if b.is_capture(m)]
            caps = [c for c in caps if c[0] >= see_min]
            if not caps:
                break
            b.push(min(caps, key=lambda c: (-c[0], c[1]))[2])
            extra += 1
    return b


def _feats(board: chess.Board, cfg: Config) -> list[Feature]:
    return static_features(board, cfg) + m3_features(board, cfg, [])


def _keys(feats: list[Feature], side: str, keys) -> set[tuple]:
    return {(f.key, tuple(f.squares)) for f in feats if f.side == side and f.key in keys}


def _value(feats: list[Feature], key: str, side: str | None = None):
    return next((f.value for f in feats if f.key == key and (side is None or f.side == side)), None)


def line_tags(line: ScoredLine, cfg: Config) -> list[str]:
    """Categories of a line: features at its start and at its leaf (after quiescence), plus the moves."""
    tg = cfg.thresholds.scoring.tags
    lc = cfg.thresholds.scoring.lines
    a, d = line.attacker, line.defender
    start = chess.Board(line.start["fen"])
    b = start.copy(stack=False)
    checks = False
    first_after: chess.Board | None = None
    for san in line.plies[: tg.leaf_plies]:
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        if b.turn == (chess.WHITE if a == "w" else chess.BLACK) and b.gives_check(mv):
            checks = True
        b.push(mv)
        if first_after is None:
            first_after = b.copy(stack=False)
    leaf = quiescent_leaf(start, line.plies, tg.leaf_plies, lc.quiescence_see_min, lc.quiescence_max_plies)
    f0, f1 = _feats(start, cfg), _feats(leaf, cfg)
    tags: list[str] = []

    # king safety: checks or a mate by A, or the defender's king more exposed at the leaf
    zone0 = _value(f0, "king_zone_attackers", d) or 0
    zone1 = _value(f1, "king_zone_attackers", d) or 0
    if checks or line.mate_for_attacker or zone1 > zone0 or _keys(f1, d, KING_KEYS) - _keys(f0, d, KING_KEYS):
        tags.append("king_safety")
    # pawn structure: new weak pawns of D or new passed pawns of A
    if (_keys(f1, d, WEAK_PAWN_KEYS) - _keys(f0, d, WEAK_PAWN_KEYS)
            or _keys(f1, a, ("passed_pawn",)) - _keys(f0, a, ("passed_pawn",))):
        tags.append("pawn_structure")
    # space and centre
    c0, c1 = _value(f0, "central_control") or {}, _value(f1, "central_control") or {}
    shift = (c1.get(a, 0) - c1.get(d, 0)) - (c0.get(a, 0) - c0.get(d, 0))
    if shift >= tg.center_shift_min or _keys(f1, a, ("space_advantage",)) - _keys(f0, a, ("space_advantage",)):
        tags.append("space_center")
    # piece activity
    def mob(feats, s):
        return sum((_value(feats, "piece_mobility", s) or {}).values())
    mshift = (mob(f1, a) - mob(f1, d)) - (mob(f0, a) - mob(f0, d))
    if (mshift >= tg.mobility_shift_min or _keys(f1, d, ("inactive_piece",)) - _keys(f0, d, ("inactive_piece",))
            or _keys(f1, a, ACTIVE_KEYS) - _keys(f0, a, ACTIVE_KEYS)):
        tags.append("piece_activity")
    # initiative: forcing moves of A
    color_a = chess.WHITE if a == "w" else chess.BLACK
    geo = cfg.thresholds.features
    if tempo_counts(start, line.plies, geo.tempo_plies, geo.tempo_threat_see_min)[color_a] >= tg.tempo_min:
        tags.append("initiative_tempo")
    # threats: the null move, or a new tactical motif against D after A's first move
    if line.kind == "threat" or (first_after is not None and
                                 _keys(_feats(first_after, cfg), d, TACTICAL_KEYS) - _keys(f0, d, TACTICAL_KEYS)):
        tags.append("threats_dynamics")
    # material
    m0, m1 = _value(f0, "material_balance") or 0, _value(f1, "material_balance") or 0
    gain = (m1 - m0) if a == "w" else (m0 - m1)
    if gain >= tg.material_min:
        tags.append("material")
    # transitions: into the endgame, or into tablebase-size material
    syz = cfg.default.engines.syzygy.max_pieces
    if (phase_of(leaf, cfg, False) != phase_of(start, cfg, False) and phase_of(leaf, cfg, False) == "endgame") \
            or (len(leaf.piece_map()) <= syz < len(start.piece_map())):
        tags.append("transition_plans")
    tags = tags or ["threats_dynamics"]
    # main category (the override of §5-bis.4 point 5 applies only to it): mate -> king, material won ->
    # material, null move -> threats, otherwise the first tag in the order of §5-bis.1
    if line.mate_for_attacker:
        line.primary = "king_safety"
    elif "material" in tags:
        line.primary = "material"
    elif line.kind == "threat":
        line.primary = "threats_dynamics"
    else:
        line.primary = tags[0]
    if line.primary not in tags:
        tags.append(line.primary)
    order = cfg.thresholds.scoring.categories
    return sorted(tags, key=order.index)


# -- T, balance, R (§5-bis.2, §5-bis.4) ----------------------------------------------


def static_t(cat: str, side: str, feats: list[Feature], sc: ScoringCfg) -> tuple[float, list[int]]:
    """T_stat: 100 minus the penalty points of the features (own = of the side, opp = of the opponent);
    for a ``relative`` category only the points beyond the opponent's count."""
    rule = sc.static[cat]
    pts, used = _static_points(rule, side, feats)
    if rule.relative:
        pts = max(0.0, pts - _static_points(rule, _other(side), feats)[0])
    return max(0.0, min(100.0, 100.0 - pts)), used


def _static_points(rule, side: str, feats: list[Feature]) -> tuple[float, list[int]]:
    pts, used = 0.0, []
    for i, f in enumerate(feats):
        table = rule.own if f.side == side else rule.opp if f.side == _other(side) else {}
        if f.key in table:
            mult = f.value if f.key in rule.per_value and isinstance(f.value, (int, float)) else 1
            pts += table[f.key] * mult
            used.append(i)
    if rule.center_points is not None:
        for i, f in enumerate(feats):
            if f.key == "central_control":
                pts += rule.center_points * max(0, f.value[_other(side)] - f.value[side])
                used.append(i)
    if rule.pawn_points is not None:
        for i, f in enumerate(feats):
            if f.key == "material_balance":
                bal = f.value if side == "w" else -f.value
                if bal < 0:
                    pts += rule.pawn_points * -bal
                    used.append(i)
    return pts, sorted(set(used))


def complexity_t(side: str, nodes: list[dict[str, Any]], sc: ScoringCfg) -> tuple[float, list[str]]:
    """practical_complexity (meta): Maia-2 entropy and unique moves at the nodes where ``side`` moves."""
    cc = sc.complexity
    own = [n for n in nodes if n["citable"] and n["side_to_move"] == side and n["maia"] and n["multipv"]]
    if not own:
        return 100.0, []
    h = sum(-sum(e["p"] * math.log2(e["p"]) for e in n["maia"]["policy"] if e["p"] > 0) for n in own) / len(own)
    hn = min(1.0, h / cc.entropy_max_bits)

    def gap(n):
        m = n["multipv"]
        if len(m) < 2 or m[0]["mate_user"] is not None or m[1]["mate_user"] is not None:
            return False
        return abs(m[0]["eval_user_cp"] - m[1]["eval_user_cp"]) >= cc.unique_gap_cp   # the best is first
    u = sum(1 for n in own if gap(n)) / len(own)
    wsum = cc.entropy_weight + cc.unique_weight
    return 100.0 * (1 - (cc.entropy_weight * hn + cc.unique_weight * u) / wsum), [n["id"] for n in own]


def advice(t: int, sc: ScoringCfg) -> str:
    a = sc.advice
    if t >= a["no_worry"]:
        return "no_worry"
    if t >= a["monitor"]:
        return "monitor"
    if t >= a["attention"]:
        return "attention"
    return "critical"


def score_categories(cfg: Config, nodes: list[dict[str, Any]], features: list[Feature], lines: list[ScoredLine],
                     user: str, phase: str, saturated: bool, band: str,
                     main: list[ScoredLine] | None = None) -> list[dict[str, Any]]:
    """``lines``: the filtered lines (T_dyn, proximity); ``main``: the main lines (``id`` = ``PV<n>``), tagged
    but without risk, that weigh in R as the share of the decision the category concerns."""
    main = main or []
    sc = cfg.thresholds.scoring
    rel = sc.relevance
    root_unstable = nodes[0]["unstable_depth"]
    out = []
    for cat in sc.categories:
        T, t_stat, t_dyn, risk, override = {}, {}, {}, {}, {}
        feat_idx: set[int] = set()
        used_nodes: list[str] = []
        cat_lines = [ln for ln in lines if cat in ln.tags]
        for s in ("w", "b"):
            if cat == "practical_complexity":
                t, used_nodes_s = complexity_t(s, nodes, sc)
                used_nodes += used_nodes_s
                t_stat[s], t_dyn[s], risk[s], override[s] = round(t), round(t), 0.0, False
                T[s] = round(t)
                continue
            ts, used = static_t(cat, s, features, sc)
            feat_idx.update(used)
            mine = [ln for ln in cat_lines if ln.defender == s]
            r = sum(ln.risk for ln in mine)
            td = 100.0 * math.exp(-r / sc.k[cat])
            t = sc.w[cat] * td + (1 - sc.w[cat]) * ts
            ov = any((ln.mate_for_attacker or ln.impact_cp >= sc.decisive_cp) and ln.p_att >= sc.override.p_att_min
                     and ln.primary == cat for ln in mine)
            if ov:
                t = min(t, sc.override.t_max)
            t_stat[s], t_dyn[s], risk[s], override[s] = round(ts), round(td), round(r, 4), ov
            T[s] = round(t)
        opp = _other(user)
        balance = T[user] - T[opp]
        prox = 0.0
        for ln in cat_lines:   # how soon the line starts, weighted by how real it is at the level
            dist = max(1, len(ln.start["path"]))
            prox = max(prox, 100.0 * max(0.0, 1 - (dist - 1) / rel.proximity_plies) * min(1.0, ln.risk / sc.theta[band]))
        main_c = [ln for ln in main if cat in ln.tags]
        decision = 100.0 * len(main_c) / len(main) if main else 0.0
        wt = rel.weights
        raw = (wt["worry"] * (100 - min(T.values())) + wt["balance"] * abs(balance) + wt["proximity"] * prox
               + wt["decision"] * decision) / sum(wt.values())
        R = round(rel.phase[phase][cat] * raw)
        unstable = root_unstable or any(ln.start["unstable_depth"] for ln in cat_lines)
        out.append({
            "id": cat, "T": T, "R": max(0, min(100, R)), "balance": balance, "advice": advice(T[user], sc),
            "confidence": "low" if (saturated or unstable) else "normal",
            "components": {"T_stat": t_stat, "T_dyn": t_dyn, "w": sc.w[cat], "k": sc.k[cat], "risk": risk,
                           "proximity": round(prox), "decision": round(decision), "override": override},
            "trace": {"features": sorted(feat_idx), "lines": [ln.id for ln in cat_lines],
                      "pvs": [ln.id for ln in main_c],
                      "nodes": sorted(set(used_nodes), key=lambda x: int(x[1:]))},
        })
    return out
