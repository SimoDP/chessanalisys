"""Candidate selection (§3-ter.3, D-42, D-63), replies (§2-bis.6), quiet and
transpositions. Pure functions on root rows."""

from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass
class RootRow:
    """A root move with an evaluation (E0 row or E4 restricted search)."""

    san: str
    uci: str
    eval_user_cp: int
    source: str                      # "e0" | "e4"
    e0_rank: int | None              # MultiPV rank in E0 (None for E4)
    p: float = 0.0                   # Maia-2 probability of the side to move


@dataclass
class BandSel:
    K: int
    explained_min: int
    listed_max: int
    L_max: int
    A: float


@dataclass
class Selection:
    order: list[str]                 # UCI of every evaluated root move, C1, C2, ... order
    loss: dict[str, int]
    pre: dict[str, float]
    explained: list[str]             # UCI, eval order
    listed: list[str]                # UCI, S order
    mt: str | None
    warnings: list[str] = field(default_factory=list)

    def cid(self, uci: str) -> str:
        return f"C{self.order.index(uci) + 1}"


def _s_rank(S: list[RootRow], uci: str) -> int:
    for i, r in enumerate(S):
        if r.uci == uci:
            return i
    return len(S) + 1


def select_candidates(e0: list[RootRow], e4: list[RootRow], policy: dict[str, float], bp: BandSel) -> Selection:
    rows = {r.uci: r for r in e4}
    rows.update({r.uci: r for r in e0})
    S = sorted(e0, key=lambda r: (-r.eval_user_cp, r.e0_rank))
    warnings: list[str] = []
    best = max(r.eval_user_cp for r in e0)
    if any(r.eval_user_cp > best for r in e4):
        warnings.append("e4_better_than_root")
    loss = {u: max(0, best - r.eval_user_cp) for u, r in rows.items()}
    pre = {u: -loss[u] + bp.A * 100 * policy.get(u, 0.0) for u in rows}
    W = [r.uci for r in S if loss[r.uci] <= bp.L_max]
    W.sort(key=lambda u: (-pre[u], -rows[u].eval_user_cp, _s_rank(S, u), u))
    mt = None
    if policy:
        mt = min(policy, key=lambda u: (-policy[u], _s_rank(S, u), u))
    E = W[: bp.K]
    if mt is not None and mt not in E:
        if mt in rows:
            E = W[: bp.K - 1] + [mt]
        else:
            warnings.append("maia_top_unevaluated")
    for u in W + [r.uci for r in S]:
        if len(E) >= bp.explained_min:
            break
        if u not in E:
            E.append(u)
    explained = sorted(E, key=lambda u: (-rows[u].eval_user_cp, _s_rank(S, u)))
    listed = [r.uci for r in S[: bp.listed_max]]
    order = sorted(rows, key=lambda u: (-rows[u].eval_user_cp,
                                        rows[u].e0_rank if rows[u].e0_rank is not None else float("inf"),
                                        -policy.get(u, 0.0), u))
    return Selection(order, loss, pre, explained, listed, mt, warnings)


def quiet_spread(mover_evals_e0: list[int], K: int, quiet_spread_cp: int) -> tuple[bool, int]:
    """``mover_evals_e0`` in E0 order (rank 1 first) from the point of view of the side to move."""
    S = sorted(mover_evals_e0, reverse=True)
    if not S:
        return False, 0
    sq = min(max(K, 3), len(S))
    spread = S[0] - S[sq - 1]
    return spread <= quiet_spread_cp, spread


@dataclass
class ReplyRow:
    san: str
    uci: str
    eval_opp_cp: int                 # point of view of the opponent (side to move)
    e0_rank: int | None
    p_opp: float


def select_replies(rows: list[ReplyRow], K: int, replies_min_p: float, replies_best_sf: int) -> list[str]:
    """§2-bis.6 step 2: B ∪ P up to K, ordered by p_opp (tie: better for the opponent)."""
    by_sf = sorted(rows, key=lambda r: (-r.eval_opp_cp, r.e0_rank if r.e0_rank is not None else float("inf")))
    B = [r.uci for r in by_sf[:replies_best_sf]]
    P = [r.uci for r in sorted(rows, key=lambda r: (-r.p_opp, -r.eval_opp_cp)) if r.p_opp >= replies_min_p]
    chosen = list(B)
    for u in P:
        if len(chosen) >= K:
            break
        if u not in chosen:
            chosen.append(u)
    idx = {r.uci: r for r in rows}
    return sorted(chosen, key=lambda u: (-idx[u].p_opp, -idx[u].eval_opp_cp))


def transpositions(root: chess.Board, pvs: dict[str, list[str]], plies_max: int,
                   cid: dict[str, str]) -> list[dict]:
    """First common EPD along the PVs (UCI lists) of each pair of explained candidates."""
    epds: dict[str, list[str]] = {}
    for u, pv in pvs.items():
        b = root.copy(stack=False)
        seq = []
        for mv in pv[:plies_max]:
            m = chess.Move.from_uci(mv)
            if m not in b.legal_moves:
                break
            b.push(m)
            seq.append(b.epd(en_passant="legal"))
        epds[u] = seq
    out = []
    keys = sorted(pvs, key=lambda u: int(cid[u][1:]))
    for i, a in enumerate(keys):
        for b_ in keys[i + 1:]:
            for pa, e in enumerate(epds[a], 1):
                if e in epds[b_]:
                    out.append({"a": cid[a], "b": cid[b_], "ply_a": pa, "ply_b": epds[b_].index(e) + 1})
                    break
    return out
