"""Exploration runner (§3-ter.2, D-43).

Order: Maia-2 at the root → E0 → E4 → candidate selection → E1 → E2 (+ Maia-2)
→ E3-ℓ1 (+ Maia-2) → E2b → E2c → E3-ℓ2 (+ Maia-2) → E3-ℓ3 (+ Maia-2). The levels
are capped by ``milestone_max_e3_level`` (M1: ℓ1, from M2: ℓ3). From M2 the T3
nodes include the ℓ2 nodes: E2c runs on the E2 nodes in its slot and once more
after ℓ2 for the moves missing there (OQ-M2-2). With the opponent to move the
phase R replaces E2, E2b and E3 (§2-bis.6).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import chess

from chessanalyst.config import BandParams, Config, ProfileCfg
from chessanalyst.engines.cache import CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.engines.types import EngineLine, NodeResult
from chessanalyst.explore import context as ctx
from chessanalyst.explore.pvwalk import complexity, e2b_plies
from chessanalyst.explore.select import (BandSel, ReplyRow, RootRow, Selection, quiet_spread,
                                         select_candidates, select_replies)

log = logging.getLogger(__name__)
DISCARDABLE = ("E3l1", "E2b", "E2c", "E3l2", "E3l3")


@dataclass
class UserCtx:
    color: chess.Color
    elo_maia: int
    opp_elo_maia: int
    band: str
    bp: BandParams                     # with the effective K of the detail level (M4)
    profile_name: str
    e3: bool = True                    # §7.1: below 2150 only with detail >= 4 (M4)


@dataclass
class NodeRec:
    phase: str                         # E0 E1 E2 E3l1 E3l2 E3l3 E2b E2c R
    path: list[str]                    # SAN from the root ("--" = null move)
    board: chess.Board
    result: NodeResult | None = None
    maia: dict[str, Any] | None = None
    citable: bool = True
    order: tuple = ()
    root_moves: list[str] | None = None

    @property
    def label(self) -> str:
        return " ".join(self.path) if self.path else "root"


@dataclass
class Item:
    phase: str
    board: chess.Board
    multipv: int
    d_min: int
    root_moves: list[chess.Move] | None
    ref: str


@dataclass
class Exploration:
    user_to_move: bool
    profile: ProfileCfg
    root: NodeRec
    e4: NodeResult | None = None
    null: NodeRec | None = None
    e2: dict[str, NodeRec] = field(default_factory=dict)            # candidate uci → node
    e3: list[tuple[int, str, NodeRec]] = field(default_factory=list)  # (level, candidate uci, node)
    rset: dict[str, list[str]] = field(default_factory=dict)
    e2b: dict[str, list[NodeRec]] = field(default_factory=dict)
    e2b_partial: dict[str, bool] = field(default_factory=dict)
    e2c: list[NodeRec] = field(default_factory=list)
    replies: list[str] = field(default_factory=list)
    r_nodes: dict[str, NodeRec] = field(default_factory=dict)
    rows: dict[str, RootRow] = field(default_factory=dict)
    lines: dict[str, EngineLine] = field(default_factory=dict)       # root line of every evaluated move
    selection: Selection | None = None
    quiet: bool = False
    spread_cp: int = 0
    p_up: dict[str, float] | None = None
    p_up_elo: int | None = None
    p_up_bucket: str | None = None
    complexity: dict[str, tuple[int, bool]] = field(default_factory=dict)
    context: dict | None = None
    omitted_phases: list[dict] = field(default_factory=list)
    omitted_nodes: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    time_s: float = 0.0
    nodes_analyzed: int = 0


class Budget:
    """Time per node, node cap and global deadline (§3-ter.2)."""

    def __init__(self, cfg: Config, prof: ProfileCfg, B: float, analyzer: CachedAnalyzer,
                 clock: Callable[[], float], exp: Exploration) -> None:
        self.cfg, self.prof, self.B = cfg, prof, B
        self.analyzer, self.clock, self.exp = analyzer, clock, exp
        self.calls0 = analyzer.calls
        self.start: float | None = None
        self.deadline = prof.deadline_factor * B

    @property
    def analyzed(self) -> int:
        return self.analyzer.calls - self.calls0

    def share(self, phase: str) -> float:
        s = self.cfg.exploration.phase_shares
        if phase == "R":
            return s.E2 + s.E2b + s.E3
        if phase.startswith("E3l"):
            return s.E3
        return getattr(s, phase)

    def plan(self, items: list[Item], discardable: bool) -> list[Item]:
        """Drop the worst uncached items (end of the list) beyond the node cap."""
        uncached = [i for i in items if not self.analyzer.is_cached(i.board, i.multipv, i.d_min, i.root_moves)]
        if discardable:
            over = self.analyzed + len(uncached) - self.prof.max_nodes
            if over > 0:
                drop = set(id(i) for i in uncached[-over:])
                for i in items:
                    if id(i) in drop:
                        self.exp.omitted_nodes.append({"phase": i.phase, "reason": "node_cap", "ref": i.ref})
                items = [i for i in items if id(i) not in drop]
        return items

    def t_target(self, phase: str, n: int) -> float:
        return self.share(phase) * self.B / max(1, n)

    def run(self, item: Item, t_target: float, discardable: bool) -> NodeResult | None:
        if self.start is None:
            self.start = self.clock()
        t_cap = self.prof.node_cap_factor * t_target
        if self.clock() - self.start > self.deadline:
            if discardable:
                self.exp.omitted_nodes.append({"phase": item.phase, "reason": "deadline", "ref": item.ref})
                return None
            t_target = 0.0
        return self.analyzer.analyse(item.board, item.multipv, t_target, item.d_min, t_cap, root_moves=item.root_moves)

    def run_phase(self, items: list[Item], discardable: bool, t_target: float | None = None,
                  progress: Callable[[str], None] = lambda s: None) -> list[NodeResult | None]:
        """Run planned items; returns results aligned with ``items`` (None = omitted)."""
        kept = self.plan(items, discardable)
        n_uncached = sum(1 for i in kept if not self.analyzer.is_cached(i.board, i.multipv, i.d_min, i.root_moves))
        tt = t_target if t_target is not None else (self.t_target(items[0].phase, n_uncached) if items else 0.0)
        out: list[NodeResult | None] = []
        kept_ids = {id(i) for i in kept}
        for i, it in enumerate(items):
            if id(it) not in kept_ids:
                out.append(None)
                continue
            progress(f"{it.phase} {it.ref}")
            out.append(self.run(it, tt, discardable))
        return out


def _maia_rec(maia: MaiaEngine, board: chess.Board, elo_self: int, elo_oppo: int) -> dict[str, Any]:
    fen = board.fen(en_passant="legal")
    return {"elo_self": elo_self, "elo_oppo": elo_oppo, "policy": maia.policy(fen, elo_self, elo_oppo),
            "expected_score": maia.expected_score(fen, elo_self, elo_oppo)}


def _child(board: chess.Board, uci: str) -> chess.Board:
    b = board.copy()
    b.push(chess.Move.from_uci(uci))
    return b


def _user_cp(eval_white_cp: int, color: chess.Color) -> int:
    return eval_white_cp if color == chess.WHITE else -eval_white_cp


def explore(cfg: Config, root_board: chess.Board, user: UserCtx, analyzer: CachedAnalyzer, maia: MaiaEngine,
            clock: Callable[[], float] = time.monotonic, progress: Callable[[str], None] = lambda s: None,
            time_scale: float = 1.0) -> Exploration:
    prof = cfg.exploration.profiles[user.profile_name]
    ex = cfg.exploration
    sel_th = cfg.thresholds.selection
    t0 = clock()
    user_to_move = root_board.turn == user.color
    root = NodeRec("E0", [], root_board.copy(), order=(0,))
    exp = Exploration(user_to_move=user_to_move, profile=prof, root=root)
    budget = Budget(cfg, prof, prof.B_s * time_scale, analyzer, clock, exp)

    mover, other = (user.elo_maia, user.opp_elo_maia) if user_to_move else (user.opp_elo_maia, user.elo_maia)
    root.maia = _maia_rec(maia, root_board, mover, other)
    policy: dict[str, float] = root.maia["policy"]

    # E0
    progress("E0 radice")
    [root.result] = budget.run_phase([Item("E0", root_board, prof.multipv.root, prof.dmin.root, None, "root")], False)
    assert root.result is not None
    e0_ucis = [ln.uci for ln in root.result.lines]

    # E4: Maia-2 seeds absent from E0
    seeds = [u for u, p in sorted(policy.items(), key=lambda kv: (-kv[1], kv[0]))
             if p >= ex.e4_min_p and u not in e0_ucis][: prof.e4_max_moves]
    if seeds:
        moves = [chess.Move.from_uci(u) for u in seeds]
        [exp.e4] = budget.run_phase([Item("E4", root_board, len(moves), prof.dmin.root, moves, "root")], False)

    for ln in root.result.lines:
        exp.lines[ln.uci] = ln
    e4_lines = [ln for ln in (exp.e4.lines if exp.e4 else []) if ln.uci not in exp.lines]
    for ln in e4_lines:
        exp.lines[ln.uci] = ln

    if user_to_move:
        _user_branch(cfg, exp, budget, root_board, user, maia, policy, e4_lines, progress)
    else:
        _opponent_branch(cfg, exp, budget, root_board, user, maia, policy, e4_lines, progress)

    exp.time_s = round(clock() - t0, 3)
    exp.nodes_analyzed = budget.analyzed
    return exp


def _run_null(cfg: Config, exp: Exploration, budget: Budget, root_board: chess.Board, prof: ProfileCfg,
              progress) -> None:
    if root_board.is_check():
        exp.omitted_phases.append({"phase": "E1", "reason": "in_check"})
        return
    b = root_board.copy(stack=False)
    b.push(chess.Move.null())
    nb = chess.Board(b.fen(en_passant="legal"))
    exp.null = NodeRec("E1", ["--"], nb, order=(1,))
    [exp.null.result] = budget.run_phase([Item("E1", nb, prof.multipv.nodes, prof.dmin.root, None, "--")], False,
                                         progress=progress)


def _user_branch(cfg: Config, exp: Exploration, budget: Budget, root_board: chess.Board, user: UserCtx,
                 maia: MaiaEngine, policy: dict[str, float], e4_lines: list[EngineLine], progress) -> None:
    prof, bp, th = exp.profile, user.bp, cfg.thresholds
    color = user.color
    e0 = [RootRow(ln.san, ln.uci, _user_cp(ln.eval_white_cp, color), "e0", ln.rank, policy.get(ln.uci, 0.0))
          for ln in exp.root.result.lines]
    e4 = [RootRow(ln.san, ln.uci, _user_cp(ln.eval_white_cp, color), "e4", None, policy.get(ln.uci, 0.0))
          for ln in e4_lines]
    for r in e0 + e4:
        exp.rows[r.uci] = r
    sel = select_candidates(e0, e4, policy, BandSel(bp.K, bp.explained_min, bp.listed_max, bp.L_max, bp.A))
    exp.selection = sel
    exp.warnings.extend(sel.warnings)
    band_k = th.band_params[user.band].K           # a property of the position: K of the band, not of the detail
    exp.quiet, exp.spread_cp = quiet_spread([r.eval_user_cp for r in e0], band_k, th.selection.quiet_spread_cp)

    # p_up (root only, user to move)
    lim = cfg.maia2_limits
    elo_up = min(user.elo_maia + cfg.default.engines.maia2.up_delta, lim.elo_max_model)
    if maia.bucket(elo_up) != maia.bucket(user.elo_maia):
        exp.p_up = maia.policy(root_board.fen(en_passant="legal"), elo_up, user.opp_elo_maia)
        exp.p_up_elo = elo_up
        exp.p_up_bucket = "top" if maia.bucket(elo_up) == maia.bucket(lim.top_bucket_lower) else "higher"

    _run_null(cfg, exp, budget, root_board, prof, progress)

    # E2: node after every explained candidate
    open_u = [u for u in sel.explained if not _child(root_board, u).is_game_over()]   # mate/stalemate: no node
    items = [Item("E2", _child(root_board, u), prof.multipv.nodes, prof.dmin.nodes, None, exp.rows[u].san)
             for u in open_u]
    results = budget.run_phase(items, False, progress=progress)
    for k, (u, it, res) in enumerate(zip(open_u, items, results)):
        node = NodeRec("E2", [exp.rows[u].san], it.board, res, order=(2, k))
        node.maia = _maia_rec(maia, it.board, user.opp_elo_maia, user.elo_maia)
        exp.e2[u] = node

    # E3 ℓ1: first M explained candidates × Rset
    levels = min(prof.e3_levels, cfg.exploration.milestone_max_e3_level)
    for lvl in range(levels + 1, prof.e3_levels + 1):
        exp.omitted_phases.append({"phase": f"E3l{lvl}", "reason": "milestone"})
    e3_levels = levels
    if not user.e3:
        exp.omitted_phases.append({"phase": "E3", "reason": "detail"})
        levels = 0
    e3_items: list[tuple[str, str, Item]] = []
    for u in sel.explained[: prof.e3_M] if levels else []:
        if u not in exp.e2:
            continue
        n2 = exp.e2[u]
        rset = [ln.uci for ln in n2.result.lines[: prof.e3_R]]
        pol2 = n2.maia["policy"]
        if pol2:
            top = min(pol2, key=lambda m: (-pol2[m], m))
            if top not in rset:
                rset.append(top)
        exp.rset[u] = rset
        for r in rset:
            b = _child(n2.board, r)
            if b.is_game_over():
                continue
            ref = f"{exp.rows[u].san} {n2.board.san(chess.Move.from_uci(r))}"
            e3_items.append((u, r, Item("E3l1", b, prof.multipv.nodes, prof.dmin.nodes, None, ref)))
    # one t_target for the whole phase E3: ℓ2 and ℓ3 add one node per node of the level above
    e3_t = budget.t_target("E3l1", (len(e3_items) if e3_items else prof.e3_M * (prof.e3_R + 1)) * e3_levels)
    results = budget.run_phase([it for _, _, it in e3_items], True, t_target=e3_t,
                               progress=progress) if e3_items else []
    for k, ((u, r, it), res) in enumerate(zip(e3_items, results)):
        if res is None:
            continue
        san_r = exp.e2[u].board.san(chess.Move.from_uci(r))
        node = NodeRec("E3l1", [exp.rows[u].san, san_r], it.board, res,
                       order=(3, 1, sel.explained.index(u), exp.rset[u].index(r)))
        node.maia = _maia_rec(maia, it.board, user.elo_maia, user.opp_elo_maia)
        exp.e3.append((1, u, node))

    # E2b: forced moves along the PV of the candidates
    max_loss = max(bp.L_max, th.classification.practical_alt.max_loss)
    e2b_set = [u for u in sel.explained if sel.loss[u] <= max_loss]
    walk: list[tuple[str, int, list[str], Item]] = []
    for u in sorted(e2b_set, key=lambda x: sel.order.index(x)):
        pv = exp.lines[u].pv_uci
        for p in e2b_plies(len(pv), bp.plies_max):
            b = root_board.copy()
            sans = []
            for mv in pv[:p]:
                m = chess.Move.from_uci(mv)
                sans.append(b.san(m))
                b.push(m)
            if b.is_game_over():
                continue
            walk.append((u, p, sans, Item("E2b", b, prof.multipv.pvwalk, prof.dmin.pvwalk, None, " ".join(sans))))
    results = budget.run_phase([w[3] for w in walk], True, progress=progress) if walk else []
    for u in e2b_set:
        exp.e2b[u] = []
    for (u, p, sans, it), res in zip(walk, results):
        exp.e2b[u].append(NodeRec("E2b", sans, it.board, res, citable=False,
                                  order=(5, sel.order.index(u), p)))
    fg = th.selection.forced_gap_cp
    for u in e2b_set:
        recs = exp.e2b[u]
        exp.complexity[u] = complexity([(r.board, r.result) for r in recs], fg)
        exp.e2b[u] = [r for r in recs if r.result is not None]

    # E2c + context move: T3 nodes = E2 nodes, then (from M2) also the ℓ2 nodes
    t3 = [ctx.ContextNode(exp.rows[u].san, exp.e2[u].board, exp.e2[u].result, exp.e2[u].maia["policy"])
          for u in sel.explained if u in exp.e2 and exp.e2[u].result is not None]
    e2c_t = cfg.exploration.e2c_time_factor * e3_t
    _run_e2c(exp, budget, t3, prof, th.selection.context_candidates, th.selection.context_min_p, e2c_t, progress)

    # E3 ℓ2 (opponent to move, after the first move of ℓ1) and ℓ3 (user, after the first move of ℓ2)
    for lvl in range(2, levels + 1):
        above = [(u, n) for lv, u, n in exp.e3 if lv == lvl - 1 and n.result is not None and n.result.lines]
        items = []
        for u, n in above:
            b = _child(n.board, n.result.lines[0].uci)
            if b.is_game_over():
                continue
            path = n.path + [n.result.lines[0].san]
            items.append((u, n, path, Item(f"E3l{lvl}", b, prof.multipv.nodes, prof.dmin.nodes, None, " ".join(path))))
        results = budget.run_phase([it for *_, it in items], True, t_target=e3_t, progress=progress) if items else []
        for (u, n, path, it), res in zip(items, results):
            if res is None:
                continue
            rec = NodeRec(f"E3l{lvl}", path, it.board, res, order=(3, lvl) + n.order[2:])
            user_moves = it.board.turn == user.color
            rec.maia = _maia_rec(maia, it.board, *((user.elo_maia, user.opp_elo_maia) if user_moves
                                                   else (user.opp_elo_maia, user.elo_maia)))
            exp.e3.append((lvl, u, rec))
            if lvl == 2:
                t3.append(ctx.ContextNode(" ".join(path), it.board, res, rec.maia["policy"]))
        if lvl == 2 and items:
            _run_e2c(exp, budget, t3, prof, th.selection.context_candidates, th.selection.context_min_p, e2c_t, progress)
    cands = ctx.context_candidates(t3, th.selection.context_candidates, th.selection.context_min_p)
    exp.context = ctx.choose_context(t3, cands, th.selection.context_spread_cp,
                                     th.profile.tactical.gap_cp)       # D-68: blunders are not context costs


def _run_e2c(exp: Exploration, budget: Budget, t3: list[ctx.ContextNode], prof: ProfileCfg, n_cands: int,
             min_p: float, t_target: float, progress) -> None:
    """E2c: restricted searches for the context candidates where they are legal but missing (§3-ter.6)."""
    cands = ctx.context_candidates(t3, n_cands, min_p)
    items: list[tuple[ctx.ContextNode, str, Item]] = []
    for m in cands:
        for n in ctx.missing_nodes(t3, m):
            if n.extra and m in n.extra:
                continue
            mv = chess.Move.from_uci(m)
            items.append((n, m, Item("E2c", n.board, 1, prof.dmin.pvwalk, [mv], f"{n.key} {n.board.san(mv)}")))
    if not items:
        return
    results = budget.run_phase([it for _, _, it in items], True, t_target=t_target, progress=progress)
    for (n, m, it), res in zip(items, results):
        if res is None or not res.lines:
            continue
        n.extra = {**(n.extra or {}), m: res.lines[0].eval_white_cp}
        exp.e2c.append(NodeRec("E2c", n.key.split(" "), it.board, res, citable=False,
                               order=(6, len(exp.e2c)), root_moves=[m]))


def _opponent_branch(cfg: Config, exp: Exploration, budget: Budget, root_board: chess.Board, user: UserCtx,
                     maia: MaiaEngine, policy: dict[str, float], e4_lines: list[EngineLine], progress) -> None:
    prof, bp, th = exp.profile, user.bp, cfg.thresholds
    opp = not user.color
    rows = [ReplyRow(ln.san, ln.uci, _user_cp(ln.eval_white_cp, opp), ln.rank, policy.get(ln.uci, 0.0))
            for ln in exp.root.result.lines]
    rows += [ReplyRow(ln.san, ln.uci, _user_cp(ln.eval_white_cp, opp), None, policy.get(ln.uci, 0.0))
             for ln in e4_lines]
    exp.quiet, exp.spread_cp = quiet_spread([_user_cp(ln.eval_white_cp, opp) for ln in exp.root.result.lines],
                                            th.band_params[user.band].K, th.selection.quiet_spread_cp)
    exp.replies = select_replies(rows, bp.K, th.selection.replies_min_p, th.selection.replies_best_sf)
    exp.omitted_phases.append({"phase": "E2b", "reason": "opponent_to_move"})
    exp.omitted_phases.append({"phase": "E3", "reason": "opponent_to_move"})
    _run_null(cfg, exp, budget, root_board, prof, progress)
    san = {r.uci: r.san for r in rows}
    items = [Item("R", _child(root_board, u), prof.multipv.nodes, prof.dmin.nodes, None, san[u]) for u in exp.replies]
    results = budget.run_phase(items, False, progress=progress)
    for k, (u, it, res) in enumerate(zip(exp.replies, items, results)):
        node = NodeRec("R", [san[u]], it.board, res, order=(4, k))
        node.maia = _maia_rec(maia, it.board, user.elo_maia, user.opp_elo_maia)
        exp.r_nodes[u] = node
