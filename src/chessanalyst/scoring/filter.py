"""Lines of the Category Scoring Engine and their filter by Elo (§5-bis.3, M3).

A line ℓ is the first MultiPV line of an analysed node, read as an attack of the side to move there
(the attacker A) against the other side (the defender D). Two kinds (OQ-M3-1):

* ``threat``: the lines of the null move (E1). The impact is what A gains with the free tempo with
  respect to the root, and D walks into it if at the root it plays a move that does not parry it.
  With the opponent to move, also the opponent's first lines at the root: the impact is what it gains with
  respect to the Maia-2 average of its root moves, and the user cannot avoid it (``p_walk`` = 1).
* ``refutation``: the node X was reached by a move ``m`` of D (E2, E3 ℓ1–ℓ3, replies). The impact is
  the loss of ``m``, and D walks into it with the probability that the game gets to X and D plays ``m``.

``risk(ℓ) = P_att × (1 − P_dif) × impact`` (pawns), with ``P_att`` the product of the Maia-2
probabilities of A's moves in the first ``att_plies`` half-moves and ``1 − P_dif`` = ``p_walk``, the
probability that D does not avoid the line. A line enters the report when ``risk ≥ θ(band)``; forced
mates and decisive losses always enter, invisible at the level when ``P_att`` is low.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import chess

from chessanalyst.config import ScoringCfg

PolicyFn = Callable[[str, int, int], dict[str, float]]
REFUTATION_PHASES = ("E2", "E3l1", "E3l2", "E3l3", "R")


@dataclass
class ScoredLine:
    kind: str                      # threat | refutation | main (not in the report)
    start: dict[str, Any]          # node dict (pack format)
    rank: int
    attacker: str                  # "w" | "b"
    entry: dict[str, Any] | None   # {node, san, p} for a refutation
    plies: list[str]
    eval_end_user_cp: int
    mate_user: int | None
    impact_cp: int
    p_att: float
    p_walk: float
    attacker_moves: list[dict[str, Any]]
    tags: list[str] = field(default_factory=list)
    primary: str | None = None     # main category (override, §5-bis.4 point 5)
    id: str | None = None
    reason: str | None = None
    visible: bool = True
    user: str = "w"

    @property
    def defender(self) -> str:
        return "b" if self.attacker == "w" else "w"

    @property
    def risk(self) -> float:
        return round(self.p_att * self.p_walk * self.impact_cp / 100, 4)

    @property
    def mate_for_attacker(self) -> bool:
        if self.mate_user is None:
            return False
        return (self.mate_user > 0) == (self.attacker == self.user)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "kind": self.kind, "start_node": self.start["id"], "rank": self.rank,
            "entry": self.entry, "attacker": self.attacker, "defender": self.defender,
            "against_user": self.defender == self.user, "plies": self.plies,
            "eval_end_user_cp": self.eval_end_user_cp, "mate_user": self.mate_user, "impact_cp": self.impact_cp,
            "p_att": self.p_att, "p_walk": self.p_walk, "risk": self.risk, "attacker_moves": self.attacker_moves,
            "tags": self.tags, "primary": self.primary, "visible_at_level": self.visible, "reason": self.reason,
        }


def side_value(entry: dict[str, Any], side: str, user: str, mate_cp: int) -> int:
    """Value of a MultiPV entry (or anything with eval_user_cp/mate_user) from ``side``'s view."""
    if entry.get("mate_user") is not None:
        v = mate_cp if entry["mate_user"] > 0 else -mate_cp
    else:
        v = entry["eval_user_cp"]
    return v if side == user else -v


def _policy_p(node: dict[str, Any], uci: str) -> float:
    if not node.get("maia"):
        return 0.0
    return next((e["p"] for e in node["maia"]["policy"] if e["uci"] == uci), 0.0)


def path_probability(node: dict[str, Any], by_id: dict[str, dict]) -> float:
    """Probability that the game reaches ``node`` from the root: product of the Maia-2 probabilities
    (stored in the nodes) of the moves of its path."""
    p = 1.0
    cur = node
    while cur.get("parent"):
        parent = by_id[cur["parent"]]
        p *= _policy_p(parent, cur["via_uci"])
        cur = parent
    return p


def attacker_probability(board: chess.Board, plies: list[str], attacker: chess.Color, n_plies: int,
                         elo: dict[str, int], policy: PolicyFn) -> tuple[float, list[dict[str, Any]]]:
    """P_att: product of the Maia-2 probabilities of the moves the attacker has to find in the first ``n_plies``:
    its first move and its forcing moves (captures and checks). Quiet follow-ups are not part of the attack
    (OQ-M3-1)."""
    a = "w" if attacker == chess.WHITE else "b"
    d = "b" if a == "w" else "w"
    b = board.copy(stack=False)
    p = 1.0
    moves = []
    for san in plies[:n_plies]:
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        if b.turn == attacker and (not moves or b.is_capture(mv) or b.gives_check(mv)):
            q = float(policy(b.fen(en_passant="legal"), elo[a], elo[d]).get(mv.uci(), 0.0))
            p *= q
            moves.append({"san": san, "p": round(q, 4)})
        b.push(mv)
    return round(p, 4), moves


def _expected_value(node: dict[str, Any], user: str, mate_cp: int) -> float | None:
    """Value for the user of the move the side to move plays, on average (Maia-2 probabilities of the MultiPV
    moves, renormalised)."""
    ps = [(_policy_p(node, ln["uci"]), side_value(ln, user, user, mate_cp)) for ln in node["multipv"]]
    total = sum(p for p, _ in ps)
    return sum(p * v for p, v in ps) / total if total > 0 else None


def build_lines(nodes: list[dict[str, Any]], user: str, elo: dict[str, int], sc: ScoringCfg,
                policy: PolicyFn, root_losses: dict[str, int]) -> list[ScoredLine]:
    """Every line of the two kinds with ``impact >= impact_min_cp`` (before the Elo filter)."""
    lc = sc.lines
    by_id = {n["id"]: n for n in nodes}
    root = nodes[0]
    out: list[ScoredLine] = []

    def make(kind, node, rank, entry_info, impact, p_walk) -> ScoredLine:
        line = node["multipv"][rank - 1]
        board = chess.Board(node["fen"])
        a = node["side_to_move"]
        p_att, moves = attacker_probability(board, line["pv"], board.turn, lc.att_plies, elo, policy)
        return ScoredLine(kind=kind, start=node, rank=rank, attacker=a, entry=entry_info, plies=list(line["pv"]),
                          eval_end_user_cp=line["eval_user_cp"], mate_user=line["mate_user"],
                          impact_cp=min(impact, lc.impact_cap_cp), p_att=p_att, p_walk=round(p_walk, 4),
                          attacker_moves=moves, user=user)

    if root["side_to_move"] != user and root["multipv"] and root.get("maia"):
        ref = _expected_value(root, user, lc.mate_cp)
        for line in root["multipv"][: lc.root_threat_lines]:
            impact = ref - side_value(line, user, user, lc.mate_cp) if ref is not None else 0
            if impact >= lc.impact_min_cp:
                out.append(make("threat", root, line["rank"], None, round(impact), 1.0))
    for node in nodes:
        if not node["citable"] or not node["multipv"]:
            continue
        if node["phase"] == "E1" and root["multipv"]:
            d = root["side_to_move"]
            ref = side_value(root["multipv"][0], d, user, lc.mate_cp)
            for line in node["multipv"][: lc.null_lines]:
                impact = ref - side_value(line, d, user, lc.mate_cp)
                if impact < lc.impact_min_cp:
                    continue
                parry = sum(_policy_p(root, u) for u, loss in root_losses.items()
                            if loss < sc.lines.parry_share * impact)
                out.append(make("threat", node, line["rank"], None, impact, max(0.0, 1.0 - parry)))
        elif node["phase"] in REFUTATION_PHASES and node.get("parent") and node.get("via_uci"):
            parent = by_id[node["parent"]]
            if not parent["multipv"]:
                continue
            d = parent["side_to_move"]
            impact = (side_value(parent["multipv"][0], d, user, lc.mate_cp)
                      - side_value(node["multipv"][0], d, user, lc.mate_cp))
            if impact < lc.impact_min_cp:
                continue
            p_m = _policy_p(parent, node["via_uci"])
            entry = {"node": parent["id"], "san": node["via_san"], "p": p_m}
            out.append(make("refutation", node, 1, entry, impact, p_m * path_probability(parent, by_id)))
    return out


def main_lines(nodes: list[dict[str, Any]], pvs: list[dict[str, Any]], user: str) -> list[ScoredLine]:
    """The PVs of the explained candidates (or of the replies) from the root, as lines of the side to move:
    no impact (they are the reference), only tags (R, decision term)."""
    root = nodes[0]
    return [ScoredLine(kind="main", start=root, rank=0, attacker=root["side_to_move"], entry=None,
                       plies=list(p["plies"]), eval_end_user_cp=p["eval_end_user_cp"], mate_user=p.get("mate_user"),
                       impact_cp=0, p_att=1.0, p_walk=0.0, attacker_moves=[], id=p["id"], user=user)
            for p in pvs]


def filter_lines(lines: list[ScoredLine], band: str, sc: ScoringCfg) -> list[ScoredLine]:
    """§5-bis.3: ``risk >= θ(band)``, or a forced mate / decisive loss (always, visible only with P_att high
    enough). Canonical IDs ``L<n>``: threats first, then by start node and rank."""
    theta = sc.theta[band]
    kept = []
    for ln in lines:
        if ln.risk >= theta:
            ln.reason, ln.visible = "theta", True
        elif ln.mate_for_attacker or ln.impact_cp >= sc.decisive_cp:
            ln.reason = "mate" if ln.mate_for_attacker else "decisive"
            ln.visible = ln.p_att >= sc.visible_p_att_min
        else:
            continue
        kept.append(ln)
    kept.sort(key=lambda x: (x.kind != "threat", int(x.start["id"][1:]), x.rank))
    for k, ln in enumerate(kept, 1):
        ln.id = f"L{k}"
    return kept
