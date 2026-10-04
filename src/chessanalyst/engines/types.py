"""Engine-independent result types and score conversion (§3.1.2, D-39).

Everything here is stored from White's point of view; conversion to the
user's point of view happens when the pack is built (M1a).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import chess

MATE_BASE = 10000
CP_CLAMP = 9999


def white_cp_from_mate(n: int) -> int:
    """Mate in ``n`` moves (positive = White mates) as equivalent centipawns."""
    return MATE_BASE - n if n > 0 else -(MATE_BASE + n)


def clamp_cp(cp: int) -> int:
    return max(-CP_CLAMP, min(CP_CLAMP, cp))


def to_user(eval_white_cp: int, mate_white: int | None, user_color: str) -> tuple[int, int | None]:
    """Point of view of the user (``"w"`` or ``"b"``)."""
    if user_color == "w":
        return eval_white_cp, mate_white
    return -eval_white_cp, (None if mate_white is None else -mate_white)


def wdl_to_user(wdl_white: list[int] | None, user_color: str) -> list[int] | None:
    if wdl_white is None:
        return None
    w, d, l = wdl_white
    return [w, d, l] if user_color == "w" else [l, d, w]


def san_line(board: chess.Board, moves: list[chess.Move]) -> tuple[list[str], list[str]]:
    """SAN and UCI of a PV played from ``board`` (truncated at the first illegal move)."""
    b = board.copy(stack=False)
    sans: list[str] = []
    ucis: list[str] = []
    for mv in moves:
        if mv not in b.legal_moves:
            break
        sans.append(b.san(mv))
        ucis.append(mv.uci())
        b.push(mv)
    return sans, ucis


@dataclass
class EngineLine:
    rank: int
    san: str
    uci: str
    eval_white_cp: int
    mate_white: int | None
    wdl_white: list[int] | None
    pv: list[str]          # SAN, pv[0] == san
    pv_uci: list[str]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EngineLine":
        return cls(**d)


@dataclass
class NodeResult:
    """Outcome of one ``analyse_node`` call (§3.1.3)."""

    fen: str
    multipv: int                     # number of lines requested (k)
    depth: int
    seldepth: int | None
    nodes: int | None
    time_s: float
    unstable_depth: bool
    engine_version: str
    root_moves: list[str] | None = None
    lines: list[EngineLine] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "NodeResult":
        d = dict(d)
        d["lines"] = [EngineLine.from_dict(x) for x in d.get("lines", [])]
        return cls(**d)

    def truncated(self, k: int) -> "NodeResult":
        """Same result with only the first ``k`` lines (cache reuse, §3.3)."""
        d = self.to_dict()
        d["lines"] = d["lines"][:k]
        d["multipv"] = min(self.multipv, k)
        return NodeResult.from_dict(d)

    def best(self) -> EngineLine | None:
        return self.lines[0] if self.lines else None

    def line_for(self, san: str) -> EngineLine | None:
        for ln in self.lines:
            if ln.san == san:
                return ln
        return None


def line_from_info(board: chess.Board, info: dict[str, Any]) -> EngineLine:
    """Build an :class:`EngineLine` from a python-chess ``InfoDict``."""
    s = info["score"].white()
    if s.is_mate():
        n = s.mate()
        eval_white = white_cp_from_mate(n)
        mate_white: int | None = n
    else:
        eval_white = clamp_cp(s.score())
        mate_white = None
    wdl = None
    if "wdl" in info and info["wdl"] is not None:
        w = info["wdl"].white()
        wdl = [int(w.wins), int(w.draws), int(w.losses)]
    sans, ucis = san_line(board, list(info["pv"]))
    return EngineLine(
        rank=int(info["multipv"]),
        san=sans[0] if sans else "",
        uci=ucis[0] if ucis else "",
        eval_white_cp=int(eval_white),
        mate_white=mate_white,
        wdl_white=wdl,
        pv=sans,
        pv_uci=ucis,
    )
