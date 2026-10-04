"""Evidence Pack builder (§6, §6.3): canonical IDs, candidates, replies, PVs,
tables, SectionPlan. IDs do not depend on execution order or cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import chess

from chessanalyst import __version__
from chessanalyst.config import Config
from chessanalyst.engines.maia2 import entropy_bits
from chessanalyst.explore.runner import Exploration, NodeRec
from chessanalyst.explore.select import transpositions
from chessanalyst.features.model import Feature
from chessanalyst.inputs.position import Position
from chessanalyst.pack import tables as T
from chessanalyst.pack.schema import Pack
from chessanalyst.pack.section_plan import PlanInput, build_section_plan
from chessanalyst.scoring.categories import line_tags, score_categories
from chessanalyst.scoring.classify import classify
from chessanalyst.scoring.filter import PolicyFn, build_lines, filter_lines, main_lines, side_value
from chessanalyst.scoring.radar import build_t4
from chessanalyst.scoring.recommend import Cand, recommend

@dataclass
class UserSettings:
    color: chess.Color
    elo_declared: int
    elo_scale: str
    elo_ref_fide: int
    elo_maia: int
    opp_elo_declared: int
    opp_elo_maia: int
    band: str
    anchor: str
    budget_profile: str
    detail_level: int = 4

    @property
    def code(self) -> str:
        return "w" if self.color == chess.WHITE else "b"


def _ucp(eval_white_cp: int, color: chess.Color) -> int:
    return eval_white_cp if color == chess.WHITE else -eval_white_cp


def _umate(m: int | None, color: chess.Color) -> int | None:
    return None if m is None else (m if color == chess.WHITE else -m)


def _uwdl(w: list[int] | None, color: chess.Color) -> list[int] | None:
    if w is None:
        return None
    return list(w) if color == chess.WHITE else [w[2], w[1], w[0]]


def _p4(p: float) -> float:
    return round(float(p), 4)


C5_TACTICAL_KEYS = ("pin", "hanging_piece", "unresolved_capture", "fork", "skewer", "overloaded_piece")


def focus_squares(root: chess.Board, features: list[Feature], pvs: list[list[str]], plies: int) -> list[str]:
    """c5 (§8.2): root squares of the pieces in the witness of a tactical feature or moving in the
    first ``plies`` half-moves of the given PVs (SAN from the root). Pawns are not «pieces»."""
    out: set[int] = set()
    for f in features:
        if f.key in C5_TACTICAL_KEYS:
            for name in f.squares:
                sq = chess.parse_square(name)
                p = root.piece_at(sq)
                if p is not None and p.piece_type != chess.PAWN:
                    out.add(sq)
    for pv in pvs:
        b = root.copy(stack=False)
        origin = {sq: sq for sq in chess.SQUARES if b.piece_at(sq) is not None}   # current → root square
        for san in pv[:plies]:
            mv = b.parse_san(san)
            src = origin.pop(mv.from_square, mv.from_square)
            p = b.piece_at(mv.from_square)
            if p is not None and p.piece_type != chess.PAWN:
                out.add(src)
            if b.is_castling(mv):
                rook_from = chess.square(7 if chess.square_file(mv.to_square) == 6 else 0, chess.square_rank(mv.from_square))
                rook_to = chess.square(5 if chess.square_file(mv.to_square) == 6 else 3, chess.square_rank(mv.from_square))
                origin[rook_to] = origin.pop(rook_from, rook_from)
                out.add(origin[rook_to])                          # castling moves the rook too
            origin.pop(mv.to_square, None)
            b.push(mv)
            origin[mv.to_square] = src
    return sorted(chess.square_name(s) for s in out)


def _parent(rec: NodeRec, by_path: dict[tuple, str]) -> str | None:
    """Nearest analysed ancestor (an E2c search has the node it completes as parent)."""
    path = tuple(rec.path)
    if rec.phase == "E2c" and path in by_path:
        return by_path[path]
    for k in range(len(path) - 1, -1, -1):
        if path[:k] in by_path:
            return by_path[path[:k]]
    return None


def _node_dict(rec: NodeRec, nid: str, parent: str | None, color: chess.Color, min_p: float) -> dict[str, Any]:
    b = rec.board
    res = rec.result
    via_san = rec.path[-1] if rec.path else None
    via_uci = None
    if via_san and via_san != "--":
        prev = b.copy()
        try:
            via_uci = prev.pop().uci() if prev.move_stack else None
        except IndexError:
            via_uci = None
    lines = []
    for ln in res.lines if res else []:
        lines.append({"rank": ln.rank, "san": ln.san, "uci": ln.uci, "eval_white_cp": ln.eval_white_cp,
                      "mate_white": ln.mate_white, "eval_user_cp": _ucp(ln.eval_white_cp, color),
                      "mate_user": _umate(ln.mate_white, color), "wdl_user": _uwdl(ln.wdl_white, color),
                      "pv": ln.pv})
    maia = None
    if rec.maia is not None:
        pol = rec.maia["policy"]
        # the threshold applies to the stored value (4 decimals, §6.1): stable at the boundary
        entries = sorted(((u, p) for u, p in pol.items() if _p4(p) >= min_p), key=lambda kv: (-_p4(kv[1]), kv[0]))
        es = rec.maia["expected_score"]
        maia = {"elo_self": rec.maia["elo_self"], "elo_oppo": rec.maia["elo_oppo"],
                "policy": [{"san": b.san(chess.Move.from_uci(u)), "uci": u, "p": _p4(p)} for u, p in entries],
                "expected_score_user": _p4(es if b.turn == color else 1 - es)}
    return {
        "id": nid, "fen": b.fen(en_passant="legal"), "epd": b.epd(en_passant="legal"), "parent": parent,
        "via_san": via_san, "via_uci": via_uci, "phase": rec.phase, "path": list(rec.path),
        "side_to_move": "w" if b.turn == chess.WHITE else "b", "citable": rec.citable,
        "depth": res.depth if res else 0, "seldepth": res.seldepth if res else None,
        "nodes": res.nodes if res else None, "time_s": res.time_s if res else 0.0,
        "unstable_depth": res.unstable_depth if res else True, "root_moves": rec.root_moves,
        "multipv": lines, "maia": maia,
    }


def score_pack(cfg: Config, us: UserSettings, nodes: list[dict], candidates: list[dict], features: list[Feature],
               phase: str, saturated: bool, policy: PolicyFn, main_pvs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Category Scoring Engine on the built nodes (§5-bis): filtered lines with tags, then the categories."""
    sc = cfg.thresholds.scoring
    root = nodes[0]
    mover = root["side_to_move"]
    losses: dict[str, int] = {}
    if root["multipv"]:
        best = side_value(root["multipv"][0], mover, us.code, sc.lines.mate_cp)
        for ln in root["multipv"]:
            losses[ln["uci"]] = max(0, best - side_value(ln, mover, us.code, sc.lines.mate_cp))
    for c in candidates:
        losses.setdefault(c["uci"], c["loss_cp"])
    opp = "b" if us.code == "w" else "w"
    elo = {us.code: us.elo_maia, opp: us.opp_elo_maia}
    kept = filter_lines(build_lines(nodes, us.code, elo, sc, policy, losses), us.band, sc)
    main = main_lines(nodes, main_pvs, us.code)
    for ln in kept + main:
        ln.tags = line_tags(ln, cfg)
    cats = score_categories(cfg, nodes, features, kept, us.code, phase, saturated, us.band, main)
    return cats, [ln.to_dict() for ln in kept]


def build_pack(cfg: Config, pos: Position, us: UserSettings, exp: Exploration, maia_info: dict[str, str],
               features: list[Feature], profile: dict[str, Any], opening: dict | None,
               stockfish: dict[str, Any], maia_limits_bucket, tablebase: dict | None = None,
               policy: PolicyFn | None = None) -> Pack:
    color = us.color
    root = pos.board
    bp = cfg.thresholds.band_params[us.band]
    plies_max = max(2, bp.plies_max + cfg.thresholds.detail[str(us.detail_level)].plies_delta)
    opp_name = cfg.wording["colors"]["b" if color == chess.WHITE else "w"]

    # -- nodes and canonical IDs -------------------------------------------
    recs: list[NodeRec] = [exp.root]
    if exp.null is not None:
        recs.append(exp.null)
    recs += list(exp.e2.values()) + [n for _, _, n in exp.e3] + list(exp.r_nodes.values())
    recs += [n for lst in exp.e2b.values() for n in lst] + list(exp.e2c)
    recs.sort(key=lambda r: r.order)
    nid = {id(r): f"N{k}" for k, r in enumerate(recs, 1)}
    by_path: dict[tuple, str] = {}
    for r in recs:
        if r.phase in ("E0", "E1", "E2", "E3l1", "E3l2", "E3l3", "R"):
            by_path.setdefault(tuple(r.path), nid[id(r)])
    nodes = []
    for r in recs:
        parent = _parent(r, by_path) if r.path else None
        nodes.append(_node_dict(r, nid[id(r)], parent, color, cfg.thresholds.maia.policy_min_p))

    root_res = exp.root.result
    best = root_res.lines[0]
    root_policy = exp.root.maia["policy"]
    warnings = list(exp.warnings)

    candidates: list[dict] = []
    pvs: dict[str, dict] = {}
    replies: list[dict] = []
    recommendation = None
    categories: dict[str, str | None] = {}
    explained_ids: list[str] = []
    e3_entries: list[dict] = []
    context_move = None
    trans: list[dict] = []
    t2_entries: list[dict] = []

    if exp.user_to_move:
        sel = exp.selection
        cid = {u: f"C{k}" for k, u in enumerate(sel.order, 1)}
        for u in sel.order:
            ln = exp.lines[u]
            row = exp.rows[u]
            comp = exp.complexity.get(u)
            p_user = root_policy.get(u, 0.0)
            p_up = exp.p_up.get(u, 0.0) if exp.p_up is not None else None
            c = {
                "id": cid[u], "san": ln.san, "uci": u,
                "node": nid[id(exp.e2[u])] if u in exp.e2 else None,
                "source": row.source, "e0_rank": row.e0_rank,
                "eval_user_cp": row.eval_user_cp, "mate_user": _umate(ln.mate_white, color),
                "loss_cp": sel.loss[u], "wdl_user": _uwdl(ln.wdl_white, color),
                "pv": f"PV{cid[u][1:]}", "p_user": _p4(p_user), "p_up": None if p_up is None else _p4(p_up),
                "category": None, "complexity": comp[0] if comp else None,
                "complexity_partial": bool(comp and comp[1]),
                "explained": u in sel.explained, "listed": u in sel.listed, "rec_score": None,
            }
            c["category"] = classify(p_user, sel.loss[u], c["complexity"], p_up, us.band, cfg.thresholds.classification)
            categories[c["id"]] = c["category"]
            candidates.append(c)
            pvs[c["pv"]] = {"id": c["pv"], "start_node": "N1", "plies": ln.pv, "eval_end_user_cp": row.eval_user_cp}
        explained_ids = [cid[u] for u in sel.explained]
        cands = [Cand(cid[u], sel.loss[u], root_policy.get(u, 0.0), exp.complexity.get(u, (None, False))[0],
                      exp.rows[u].e0_rank if exp.rows[u].e0_rank is not None else len(sel.order) + 1) for u in sel.explained]
        rec_id, scores = recommend(cands, bp.L_max, bp.A, bp.B, cfg.thresholds.selection.rec_tie_points)
        for c in candidates:
            if c["id"] in scores:
                c["rec_score"] = scores[c["id"]]
        recommendation = {"id": rec_id, "strength": "weak" if exp.quiet else "normal", "no_unique_best": exp.quiet}

        # E3 entries and T2 rows
        for lvl, u, n in exp.e3:
            e3_entries.append({"level": lvl, "candidate": cid[u], "path": list(n.path), "node": nid[id(n)]})
        for u in sel.explained[: exp.profile.e3_M]:
            if u not in exp.rset or exp.e2[u].result is None:
                continue
            n2 = exp.e2[u]
            ml = []
            for r in exp.rset[u]:
                ln2 = next((x for x in n2.result.lines if x.uci == r), None)
                san_r = n2.board.san(chess.Move.from_uci(r))
                l1 = next((n for lv, uu, n in exp.e3 if uu == u and n.path[-1] == san_r), None)
                if ln2 is not None:
                    ml.append((san_r, _ucp(ln2.eval_white_cp, color), _umate(ln2.mate_white, color)))
                elif l1 is not None and l1.result and l1.result.lines:
                    b1 = l1.result.lines[0]
                    ml.append((san_r, _ucp(b1.eval_white_cp, color), _umate(b1.mate_white, color)))
                else:
                    ml.append((san_r, None, None))
            ml.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else 0))  # best for the opponent first
            t2_entries.append({"root": root, "after_moves": [exp.rows[u].san], "after_board": n2.board, "moves": ml})
            per_cell = cfg.tables["T2"]["moves_per_cell"]
            for r in exp.rset[u]:
                san_r = n2.board.san(chess.Move.from_uci(r))
                # ℓ1 «Dopo c r», then (from M2) ℓ2 «Dopo c r u» and ℓ3 «Dopo c r u r′» of the same branch
                prefix = [exp.rows[u].san, san_r]
                for lvl in (1, 2, 3):
                    n = next((n for lv, uu, n in exp.e3 if lv == lvl and uu == u and n.path[:2] == prefix), None)
                    if n is None or not n.result:
                        break
                    moves3 = [(x.san, _ucp(x.eval_white_cp, color), _umate(x.mate_white, color))
                              for x in n.result.lines[:per_cell]]
                    t2_entries.append({"root": root, "after_moves": list(n.path), "after_board": n.board,
                                       "moves": moves3})

        # Context move (T3)
        if exp.context is not None:
            rows = []
            san_by_node = {}
            t3_recs = list(exp.e2.values()) + [n for lv, _, n in exp.e3 if lv == 2]
            for r in exp.context["rows"]:
                node_rec = next(n for n in t3_recs if n.board.fen() == r["node"].board.fen())
                n_id = nid[id(node_rec)]
                mv = chess.Move.from_uci(exp.context["uci"])
                san_by_node[n_id] = node_rec.board.san(mv)
                rows.append({"node": n_id, "path": list(node_rec.path), "best_san": r["best"].san,
                             "best_eval_user_cp": _ucp(r["best"].eval_white_cp, color),
                             "move_eval_user_cp": _ucp(r["move_eval_white"], color),
                             "cost_cp": r["cost_cp"], "p_opp": _p4(r["p_opp"])})
            context_move = {"san_by_node": san_by_node, "uci": exp.context["uci"], "rows": rows,
                            "spread_cp": exp.context["spread_cp"]}

        trans = transpositions(root, {u: exp.lines[u].pv_uci for u in sel.explained}, plies_max, cid)
    else:
        rid = {u: f"R{k}" for k, u in enumerate(exp.replies, 1)}
        for k, u in enumerate(exp.replies, 1):
            ln = exp.lines[u]
            node = exp.r_nodes[u]
            ub = []
            if node.result and node.result.lines:
                u1 = _ucp(node.result.lines[0].eval_white_cp, color)
                pol = node.maia["policy"] if node.maia else {}
                for j, x in enumerate(node.result.lines[:3], 1):
                    ev = _ucp(x.eval_white_cp, color)
                    ub.append({"id": f"{rid[u]}.u{j}", "san": x.san, "uci": x.uci, "eval_user_cp": ev,
                               "mate_user": _umate(x.mate_white, color), "loss_cp": max(0, u1 - ev),
                               "p_user": _p4(pol.get(x.uci, 0.0))})
            replies.append({"id": rid[u], "san": ln.san, "uci": u, "node": nid[id(node)],
                            "eval_user_cp": _ucp(ln.eval_white_cp, color), "mate_user": _umate(ln.mate_white, color),
                            "p_opp": _p4(root_policy.get(u, 0.0)), "user_best": ub})
            pvs[f"PV{k}"] = {"id": f"PV{k}", "start_node": "N1", "plies": ln.pv,
                             "eval_end_user_cp": _ucp(ln.eval_white_cp, color)}

    # -- Maia block ----------------------------------------------------------
    lim = cfg.maia2_limits
    sat = us.elo_maia >= lim.top_bucket_lower

    # -- Category Scoring Engine (§5-bis, M3) ------------------------------------
    categories_out: list[dict] = []
    lines_out: list[dict] = []
    if policy is not None:
        if exp.user_to_move:
            main_pvs = [dict(pvs[c["pv"]], mate_user=c["mate_user"]) for c in candidates if c["explained"]]
        else:
            main_pvs = [dict(pvs[f"PV{r['id'][1:]}"], mate_user=r["mate_user"]) for r in replies]
        categories_out, lines_out = score_pack(cfg, us, nodes, candidates, features, profile["phase"], sat, policy,
                                               main_pvs)
    es_root = exp.root.maia["expected_score"]
    maia = {
        "model_type": maia_info["model_type"], "package_version": maia_info["package_version"],
        "device": maia_info["device"], "bucket_user": maia_limits_bucket(us.elo_maia),
        "bucket_opp": maia_limits_bucket(us.opp_elo_maia), "top_bucket_lower": lim.top_bucket_lower,
        "saturated": sat, "confidence": "low" if sat else "normal",
        "p_up_elo": exp.p_up_elo, "p_up_bucket": exp.p_up_bucket,
        "human_expected_score_user": _p4(es_root if root.turn == color else 1 - es_root),
        "entropy_bits": round(entropy_bits(root_policy), 3),
    }

    # -- tables ----------------------------------------------------------------
    tables: dict[str, dict] = {}
    if exp.user_to_move:
        tables["T1"] = T.build_t1(cfg, us.anchor, root, candidates, pvs, recommendation["id"],
                                  us.elo_declared, sat, plies_max, tb=tablebase is not None)
        if us.anchor in cfg.tables["T2"]["anchors"]:
            t2 = T.build_t2(cfg, t2_entries, tb=tablebase is not None)
            if t2 is not None:
                tables["T2"] = t2
        if context_move is not None and us.anchor in cfg.tables["T3"]["anchors"]:
            boards = {nid[id(n)]: n.board for n in list(exp.e2.values()) + [n for lv, _, n in exp.e3 if lv == 2]}
            tables["T3"] = T.build_t3(cfg, root, context_move, boards, opp_name, tb=tablebase is not None)
    else:
        rb = {r["id"]: exp.r_nodes[r["uci"]].board for r in replies}
        tables["T1"] = T.build_t1_alt(cfg, root, replies, rb, us.opp_elo_declared, sat, tb=tablebase is not None)
    t4 = build_t4(cfg, us.anchor, categories_out, us.code) if profile["matrix_column"] != 4 else None   # S02 (§8.2)
    if t4 is not None:
        tables["T4"] = t4

    # -- section plan ------------------------------------------------------------
    spt = cfg.thresholds.section_plan
    low_loss = sum(1 for c in candidates if c["explained"] and c["loss_cp"] <= cfg.thresholds.section_plan.c3_loss_max_cp)
    pi = PlanInput(anchor=us.anchor, band=us.band, elo_ref_fide=us.elo_ref_fide,
                   matrix_column=profile["matrix_column"], castling=profile["castling"],
                   user_to_move=exp.user_to_move, opp_color_name=opp_name, explained=explained_ids,
                   explained_low_loss=low_loss, categories=categories, replies=[r["id"] for r in replies],
                   recommendation=recommendation["id"] if recommendation else None,
                   has_t2="T2" in tables, has_t3="T3" in tables, maia_low=sat, detail=us.detail_level,
                   focus_squares=focus_squares(root, features, [p["plies"] for p in list(pvs.values())[:spt.c5_pvs]],
                                               spt.c5_pv_plies) if profile["matrix_column"] == 2 else [],
                   tablebase=tablebase is not None, has_t4="T4" in tables,
                   invisible_lines=[ln["id"] for ln in lines_out if not ln["visible_at_level"]])
    plan, omitted_sections, plan_warnings = build_section_plan(cfg, pi)
    warnings += plan_warnings
    if (us.elo_ref_fide >= cfg.thresholds.elo_rules.e3_mandatory_from
            and cfg.exploration.milestone_max_e3_level < exp.profile.e3_levels):
        warnings.append("move_order_limited")          # M1 only (§8.3)
    if sat:
        warnings.append("maia_low_confidence_header")
    if any(n["unstable_depth"] for n in nodes):
        warnings.append("unstable_nodes")

    pack = {
        "app_version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_hash": cfg.config_hash,
        "position": {"fen": pos.fen, "epd": root.epd(en_passant="legal"),
                     "side_to_move": "w" if root.turn == chess.WHITE else "b", "fullmove": root.fullmove_number,
                     "legal_moves": root.legal_moves.count(), "in_check": root.is_check(),
                     "last_move_san": pos.last_move_san, "user_to_move": exp.user_to_move},
        "history": {"source": pos.source, "plies": pos.plies, "repetitions": pos.repetitions(),
                    "start_fen": pos.start_fen},
        "user": {"color": us.code, "elo_declared": us.elo_declared, "elo_scale": us.elo_scale,
                 "elo_ref_fide": us.elo_ref_fide, "elo_maia": us.elo_maia,
                 "opp_elo_declared": us.opp_elo_declared, "opp_elo_maia": us.opp_elo_maia,
                 "band": us.band, "anchor": us.anchor, "detail_level": us.detail_level, "language": "it",
                 "budget_profile": us.budget_profile},
        "profile": profile,
        "opening": opening,
        "engine": {
            "stockfish": stockfish,
            "root": {"node": "N1", "depth": root_res.depth, "eval_user_cp": _ucp(best.eval_white_cp, color),
                     "mate_user": _umate(best.mate_white, color), "wdl_user": _uwdl(best.wdl_white, color)},
            "candidates": candidates, "replies": replies, "pvs": list(pvs.values()),
            "null_move": {"node": nid[id(exp.null)]} if exp.null is not None else None,
            "e3": e3_entries, "context_move": context_move, "transpositions": trans,
        },
        "maia": maia,
        "recommendation": recommendation,
        "features": [f.to_dict() for f in features],
        "categories": categories_out,
        "filtered_lines": lines_out,
        "tablebase": tablebase,
        "tables": tables,
        "nodes": nodes,
        "section_plan": plan,
        "omitted_sections": omitted_sections,
        "omitted_phases": exp.omitted_phases,
        "omitted_nodes": exp.omitted_nodes,
        "warnings": warnings,
        "constraints": {"max_pv_plies": plies_max, "plan_max_moves": cfg.default.llm.plan_max_moves},
    }
    return Pack.model_validate(pack)
