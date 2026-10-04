"""Token ``plan`` (§9-bis.3, D-26) and ``diag`` validation (V04)."""

from __future__ import annotations

import chess


class PlanError(ValueError):
    pass


def check_plan(board: chess.Board, side: str, sans: list[str], max_moves: int) -> list[str]:
    """Validate a plan of moves of one side; return the canonical SANs."""
    if not 1 <= len(sans) <= max_moves:
        raise PlanError(f"il piano ha {len(sans)} mosse (da 1 a {max_moves})")
    color = chess.WHITE if side == "w" else chess.BLACK
    b = board.copy(stack=False)
    if b.turn != color:
        if b.is_check():
            raise PlanError("il lato al tratto è sotto scacco: non si può passare la mossa")
        b.push(chess.Move.null())
    out = []
    for i, san in enumerate(sans):
        try:
            mv = b.parse_san(san)
        except ValueError:
            raise PlanError(f"{san} non è legale nella sequenza del piano") from None
        out.append(b.san(mv))
        b.push(mv)
        if i < len(sans) - 1:
            if b.is_check():
                raise PlanError(f"{san} dà scacco: lo scacco è ammesso solo come ultima mossa")
            b.push(chess.Move.null())
    return out


def render_plan(side: str, sans: list[str]) -> str:
    dots = "..." if side == "b" else ""
    return " → ".join(dots + s for s in sans)


def check_diag(a: str, b: str) -> str:
    """Two aligned, different squares (same diagonal, file or rank) → ``a7–g1``."""
    sa, sb = chess.parse_square(a), chess.parse_square(b)
    if sa == sb:
        raise PlanError(f"case uguali: {a}-{b}")
    df = abs(chess.square_file(sa) - chess.square_file(sb))
    dr = abs(chess.square_rank(sa) - chess.square_rank(sb))
    if not (df == 0 or dr == 0 or df == dr):
        raise PlanError(f"case non allineate: {a}-{b}")
    return f"{a}–{b}"
