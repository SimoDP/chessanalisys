"""Tables T1–T3 built by code (§8.5, D-44, config/tables.yaml). Data cells
hold already formatted text (§9-bis.7); text cells are ``None`` (filled by the LLM)."""

from __future__ import annotations

from typing import Any

import chess

from chessanalyst.config import Config
from chessanalyst.pack.section_plan import fill_opp
from chessanalyst.engines.types import CP_CLAMP
from chessanalyst.render.format_it import fmt_eval, fmt_loss, fmt_pct, numbered, tb_outcome


def header(cfg: Config, key: str, *, elo: int | None = None, opp_elo: int | None = None,
           opp: str = "", star: bool = False) -> str:
    h = fill_opp(cfg.tables["headers"][key], opp)
    if elo is not None:
        h = h.replace("{elo}", str(elo))
    if opp_elo is not None:
        h = h.replace("{opp_elo}", str(opp_elo))
    return h + ("*" if star else "")


def _columns(cfg: Config, spec: dict, **kw) -> list[dict]:
    cols = []
    for k in spec.get("data", []):
        cols.append({"key": k, "header": header(cfg, k, star=(k in ("p_user", "p_opp") and kw.get("star", False)),
                                                **{x: v for x, v in kw.items() if x != "star"}), "kind": "data"})
    for k in spec.get("text", []):
        cols.append({"key": k, "header": header(cfg, k, **{x: v for x, v in kw.items() if x != "star"}), "kind": "text"})
    return cols


def ev_cell(cfg: Config, cp: int, mate: int | None, tb: bool, sign: int = 1) -> str:
    """Evaluation in a table: the number, or the tablebase outcome in words (§3.3, M2)."""
    if tb:
        return cfg.wording["tablebase"]["table"][tb_outcome(cp, mate, CP_CLAMP)]
    return fmt_eval(cp, mate, table=True, sign=sign)


def _footnote(cfg: Config, low: bool) -> str | None:
    return cfg.wording["fixed"]["maia_low_confidence_table"] if low else None


def build_t1(cfg: Config, anchor: str, root: chess.Board, candidates: list[dict], pvs: dict[str, dict],
             rec_id: str | None, elo: int, low: bool, plies_max: int, tb: bool = False, sign: int = 1) -> dict:
    spec = cfg.tables["T1"][anchor]
    cols = _columns(cfg, spec, elo=elo, star=low)
    max_line = min(cfg.tables["t1_line_plies"].get(anchor, 0), plies_max - 1)
    rows = []
    for c in candidates:
        if not (c["explained"] or c["listed"]):
            continue
        move = numbered(root, [c["san"]])
        cells: dict[str, Any] = {}
        for k in spec.get("data", []):
            if k == "move":
                cells[k] = f"**{move}** {cfg.tables['recommended_marker']}" if c["id"] == rec_id else move
            elif k == "eval":
                cells[k] = ev_cell(cfg, c["eval_user_cp"], c["mate_user"], tb, sign)
            elif k == "p_user":
                cells[k] = fmt_pct(c["p_user"])
            elif k == "line":
                b = root.copy(stack=False)
                b.push_san(c["san"])
                cells[k] = numbered(b, pvs[c["pv"]]["plies"][1:1 + max_line]) if max_line > 0 else ""
        for k in spec.get("text", []):
            cells[k] = None
        rows.append({"id": c["id"], "cells": cells})
    return {"id": "T1", "section": "S07", "columns": cols, "rows": rows, "footnote": _footnote(cfg, low)}


def build_t1_alt(cfg: Config, root: chess.Board, replies: list[dict], r_boards: dict[str, chess.Board],
                 opp_elo: int, low: bool, tb: bool = False, sign: int = 1) -> dict:
    spec = cfg.tables["T1_alt"]
    cols = _columns(cfg, spec, opp_elo=opp_elo, star=low)
    rows = []
    for r in replies:
        cells: dict[str, Any] = {
            "reply": numbered(root, [r["san"]]),
            "p_opp": fmt_pct(r["p_opp"]),
            "eval": ev_cell(cfg, r["eval_user_cp"], r["mate_user"], tb, sign),
        }
        if r["user_best"]:
            u1 = r["user_best"][0]
            cells["user_best"] = f"{numbered(r_boards[r['id']], [u1['san']])} " \
                                 f"({ev_cell(cfg, u1['eval_user_cp'], u1['mate_user'], tb, sign)})"
        else:
            cells["user_best"] = cfg.tables["empty_text_cell"]
        cells["prepare"] = None
        rows.append({"id": r["id"], "cells": cells})
    return {"id": "T1", "section": "S07", "columns": cols, "rows": rows, "footnote": _footnote(cfg, low)}


def _moves_cell(cfg: Config, board: chess.Board, moves: list[tuple[str, int | None, int | None]], tb: bool,
                sign: int = 1) -> str:
    parts = []
    for san, ev, mate in moves:
        mv = numbered(board, [san])
        parts.append(f"{mv} ({ev_cell(cfg, ev, mate, tb, sign)})" if ev is not None else mv)
    return ", ".join(parts)


def build_t2(cfg: Config, entries: list[dict], tb: bool = False, sign: int = 1) -> dict | None:
    """``entries``: [{"after_board", "after_moves" (SAN from root), "moves": [(san, eval_user, mate_user)]}]."""
    if not entries:
        return None
    spec = {"data": ["t2_after", "t2_moves"], "text": cfg.tables["T2"]["text"]}
    cols = _columns(cfg, spec)
    rows = []
    for k, e in enumerate(entries, 1):
        rows.append({"id": f"r{k}", "cells": {
            "t2_after": numbered(e["root"], e["after_moves"]),
            "t2_moves": _moves_cell(cfg, e["after_board"], e["moves"], tb, sign),
            **{t: None for t in spec["text"]},
        }})
    return {"id": "T2", "section": "S07", "columns": cols, "rows": rows, "footnote": None}


def build_t3(cfg: Config, root: chess.Board, context: dict, boards: dict[str, chess.Board], opp: str,
             tb: bool = False, sign: int = 1) -> dict:
    """``context`` = pack ``context_move`` (dict); ``boards`` = node id → board."""
    first_node = context["rows"][0]["node"]
    san0 = context["san_by_node"][first_node]
    b0 = boards[first_node]
    move_header = ("..." if b0.turn == chess.BLACK else "") + san0
    cols = [
        {"key": "t3_after", "header": header(cfg, "t3_after"), "kind": "data"},
        {"key": "t3_best", "header": header(cfg, "t3_best", opp=opp), "kind": "data"},
        {"key": "context", "header": move_header, "kind": "data"},
        {"key": "t3_cost", "header": header(cfg, "t3_cost"), "kind": "data"},
    ]
    rows = []
    for k, r in enumerate(context["rows"], 1):
        b = boards[r["node"]]
        dots = "..." if b.turn == chess.BLACK else ""
        rows.append({"id": f"r{k}", "cells": {
            "t3_after": numbered(root, r["path"]),
            "t3_best": f"{dots}{r['best_san']} ({ev_cell(cfg, r['best_eval_user_cp'], None, tb, sign)})",
            "context": ev_cell(cfg, r["move_eval_user_cp"], None, tb, sign),
            "t3_cost": (cfg.wording["tablebase"]["loss_none" if tb_outcome(r["best_eval_user_cp"], None, CP_CLAMP)
                        == tb_outcome(r["move_eval_user_cp"], None, CP_CLAMP) else "loss_decisive"]
                        if tb else fmt_loss(r["cost_cp"])),
        }})
    return {"id": "T3", "section": "S06", "columns": cols, "rows": rows, "footnote": None}
