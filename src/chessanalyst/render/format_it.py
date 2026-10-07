"""Italian number formats (§9-bis.7)."""

from __future__ import annotations

import math

import chess


def _half_away(x: float, nd: int = 0) -> float:
    f = 10 ** nd
    return math.floor(abs(x) * f + 0.5) / f * (1 if x >= 0 else -1)


def eval_sign(wording: dict, user_color: str) -> int:
    """Sign that turns a user-side evaluation into the displayed one (D-75): with
    ``numbers.eval_sign: white`` the numbers follow Stockfish (positive = better for White)."""
    white = wording.get("numbers", {}).get("eval_sign", "user") == "white"
    return -1 if white and user_color == "b" else 1


def fmt_eval(cp: int, mate_user: int | None = None, table: bool = False, opp_name: str = "", sign: int = 1) -> str:
    """Evaluation in pawns: ``+0,37``, ``-0,15``, ``0,00``. ``cp`` and ``mate_user`` are from the user's
    side; ``sign`` (``eval_sign``) gives the displayed side. A mate in words stays from the user's side."""
    if mate_user is not None:
        n = abs(mate_user)
        if table:
            return f"#{n}" if mate_user * sign > 0 else f"-#{n}"
        return f"matto in {n} per te" if mate_user > 0 else f"matto in {n} per {opp_name}"
    v = _half_away(sign * cp / 100, 2)
    if v == 0:
        return "0,00"
    return ("+" if v > 0 else "-") + f"{abs(v):.2f}".replace(".", ",")


def fmt_loss(cp: int, mate: bool = False) -> str:
    if mate:
        return "decisiva"
    return f"{abs(_half_away(cp / 100, 2)):.2f}".replace(".", ",")


def tb_outcome(cp: int, mate_user: int | None, win_cp: int) -> str:
    """Outcome class of an evaluation in a tablebase position: Stockfish with Syzygy reports a
    tablebase win as a clamped score (``|cp| >= win_cp``) or a mate, a draw as 0."""
    if mate_user is not None:
        return "win" if mate_user > 0 else "loss"
    if abs(cp) >= win_cp:
        return "win" if cp > 0 else "loss"
    return "draw"


def fmt_pct(p: float) -> str:
    if p == 0:
        return "0%"
    if 0 < p < 0.005:
        return "<1%"
    r = int(_half_away(p * 100))
    if r >= 100 and p < 1:
        return ">99%"
    return f"{r}%"


def fmt_wdl(permille: int) -> str:
    return f"{int(_half_away(permille / 10))}%"


def numbered(board: chess.Board, sans: list[str], first_black_dots: bool = True) -> str:
    """``6.Be3 e5 7.Nb3``; a sequence starting with Black: ``6...e5 7.Nb3``."""
    parts = []
    num, turn = board.fullmove_number, board.turn
    for i, san in enumerate(sans):
        if turn == chess.WHITE:
            parts.append(f"{num}.{san}")
        else:
            parts.append(f"{num}...{san}" if i == 0 and first_black_dots else san)
            num += 1
        turn = not turn
    return " ".join(parts)
