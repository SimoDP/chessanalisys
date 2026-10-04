"""Automatic annotation of the sampled positions with the real engines (M5).

For every position (the side to move is «the user», with the Elo of the game, in Lichess scale):

* the pipeline of the app (profile ``annotate.profile``) gives the pack;
* every line of §5-bis.3 *before* the Elo filter, with tags and main category, and the main lines: the fit
  recomputes T and R for other values of θ, k_c and w_c without engines;
* the next ``own_moves`` moves of the player in the game (the one played and the following ones): their cost
  with respect to the best move (Stockfish), and for an error (cost >= ``fit.error_cp``) the categories of the
  refutation, tagged with the same rules as the lines (§5-bis.4 point 1).

The output (``fixtures/calibration/annotations.jsonl``) has only what the fit needs; the packs go to
``data/calibration/packs`` (not versioned). The run can be resumed: done IDs are skipped.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import chess

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from chessanalyst.scoring.categories import line_tags
from chessanalyst.scoring.filter import ScoredLine, build_lines, main_lines, side_value

ANNOTATIONS_FILE = Path("fixtures/calibration/annotations.jsonl")
PACKS_DIR = Path("data/calibration/packs")
CACHE_FILE = Path("data/calibration/cache.sqlite")


def _board(moves: list[str], n: int) -> chess.Board:
    b = chess.Board()
    for u in moves[:n]:
        b.push_uci(u)
    return b


def _mover_cp(line, turn: chess.Color, mate_cp: int) -> int:
    if line.mate_white is not None:
        v = mate_cp if line.mate_white > 0 else -mate_cp
    else:
        v = line.eval_white_cp
    return v if turn == chess.WHITE else -v


def move_cost(cfg: Config, analyzer: CachedAnalyzer, board: chess.Board, uci: str) -> tuple[int, Any]:
    """Cost of ``uci`` for the side to move (cp, >= 0) and the best line of the position after it."""
    a = cfg.calibration["annotate"]
    mate_cp = cfg.thresholds.scoring.lines.mate_cp
    res = analyzer.analyse(board, a["multipv"], a["t_target_s"], a["d_min"], a["t_cap_s"])
    best = _mover_cp(res.lines[0], board.turn, mate_cp)
    mine = next((ln for ln in res.lines if ln.uci == uci), None)
    if mine is None:
        r2 = analyzer.analyse(board, 1, a["t_target_s"], a["d_min"], a["t_cap_s"],
                              root_moves=[chess.Move.from_uci(uci)])
        mine = r2.lines[0]
    cost = max(0, best - _mover_cp(mine, board.turn, mate_cp))
    after = board.copy()
    after.push_uci(uci)
    refut = None
    if not after.is_game_over():
        refut = analyzer.analyse(after, 1, a["t_target_s"], a["d_min"], a["t_cap_s"]).lines[0]
    return cost, (after, refut)


def _error_tags(cfg: Config, after: chess.Board, refut, player: str) -> tuple[list[str], str | None]:
    """Categories of an error: the refutation (best line after the move) tagged as a line of the opponent."""
    if refut is None:
        return [], None
    node = {"id": "N0", "fen": after.fen(), "path": [], "unstable_depth": False}
    mate_user = None if refut.mate_white is None else (refut.mate_white if player == "w" else -refut.mate_white)
    ln = ScoredLine(kind="refutation", start=node, rank=1, attacker="b" if player == "w" else "w", entry=None,
                    plies=list(refut.pv), eval_end_user_cp=0, mate_user=mate_user, impact_cp=0, p_att=1.0,
                    p_walk=1.0, attacker_moves=[], user=player)
    tags = line_tags(ln, cfg)
    return tags, ln.primary


def annotate_position(cfg: Config, p: dict[str, Any], analyzer: CachedAnalyzer, maia, openings, tablebase,
                      progress: Callable[[str], None] = lambda s: None) -> tuple[dict[str, Any], dict]:
    a, sc = cfg.calibration["annotate"], cfg.thresholds.scoring
    board = _board(p["moves"], p["ply"])
    pos = Position(board=board, source="pgn", plies=p["ply"])
    us = resolve_settings(cfg, p["side"], p["elo_self"], "lichess", p["elo_opp"], a["profile"])
    pack = json.loads(analyse_position(cfg, pos, us, analyzer, maia, openings, tablebase=tablebase,
                                       progress=progress).model_dump_json())
    user, opp = p["side"], "b" if p["side"] == "w" else "w"
    elo = {user: us.elo_maia, opp: us.opp_elo_maia}
    nodes = pack["nodes"]
    root = nodes[0]
    losses = {}
    if root["multipv"]:
        best = side_value(root["multipv"][0], user, user, sc.lines.mate_cp)
        losses = {ln["uci"]: max(0, best - side_value(ln, user, user, sc.lines.mate_cp)) for ln in root["multipv"]}
    for c in pack["engine"]["candidates"]:
        losses.setdefault(c["uci"], c["loss_cp"])
    lines = build_lines(nodes, user, elo, sc, maia.policy, losses)
    pvs = {v["id"]: v for v in pack["engine"]["pvs"]}
    main_src = ([dict(pvs[c["pv"]], mate_user=c["mate_user"]) for c in pack["engine"]["candidates"] if c["explained"]]
                if pack["position"]["user_to_move"] else [])
    mains = main_lines(nodes, main_src, user)
    for ln in lines + mains:
        ln.tags = line_tags(ln, cfg)
    policy = {e["uci"]: e["p"] for e in (root["maia"] or {}).get("policy", [])}
    played = []
    for k in range(a["own_moves"]):
        n = p["ply"] + 2 * k
        if n >= len(p["moves"]):
            break
        b = _board(p["moves"], n)
        cost, (after, refut) = move_cost(cfg, analyzer, b, p["moves"][n])
        tags, primary = _error_tags(cfg, after, refut, user) if cost >= cfg.calibration["fit"]["error_cp"] else ([], None)
        played.append({"k": k, "uci": p["moves"][n], "cost_cp": cost, "tags": tags, "primary": primary})
    cats = {c["id"]: c for c in pack["categories"]}
    record = {
        "id": p["id"], "band": p["band"], "side": user, "elo_self": p["elo_self"], "elo_opp": p["elo_opp"],
        "phase": pack["profile"]["phase"], "matrix_column": pack["profile"]["matrix_column"],
        "saturated": pack["maia"]["saturated"],
        "t_stat": {c: cats[c]["components"]["T_stat"] for c in cats},
        "complexity_t": cats["practical_complexity"]["T"],
        "lines": [{"kind": ln.kind, "defender": ln.defender, "risk": ln.risk, "p_att": ln.p_att,
                   "p_walk": ln.p_walk, "impact_cp": ln.impact_cp, "mate": ln.mate_for_attacker, "tags": ln.tags,
                   "primary": ln.primary, "dist": max(1, len(ln.start["path"]))} for ln in lines],
        "main_tags": [ln.tags for ln in mains],
        "candidates": [{"uci": c["uci"], "san": c["san"], "eval_user_cp": c["eval_user_cp"], "loss_cp": c["loss_cp"],
                        "p_user": c["p_user"], "e0_rank": c["e0_rank"], "source": c["source"],
                        "explained": c["explained"], "complexity": c["complexity"]}
                       for c in pack["engine"]["candidates"]],
        "policy_played": policy.get(p["moves"][p["ply"]], 0.0),
        "maia_top": (root["maia"] or {}).get("policy", [{}])[0].get("uci"),
        "played": played,
    }
    return record, pack


def annotate_all(cfg: Config, positions: list[dict[str, Any]], progress: Callable[[str], None] = print) -> Path:
    from chessanalyst.run import load_openings, open_engines

    root = cfg.project_root
    out = root / ANNOTATIONS_FILE
    done = set()
    if out.is_file():
        done = {json.loads(line)["id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    (root / PACKS_DIR).mkdir(parents=True, exist_ok=True)
    cache = Cache(root / CACHE_FILE)
    engines = open_engines(cfg, cache)
    openings = load_openings(cfg)
    try:
        for i, p in enumerate(positions, 1):
            if p["id"] in done:
                continue
            progress(f"[{i}/{len(positions)}] {p['id']} · {p['band']} · {p['side']} · Elo {p['elo_self']}")
            rec, pack = annotate_position(cfg, p, engines.analyzer, engines.maia, openings, engines.tablebase)
            (root / PACKS_DIR / f"{p['id']}.pack.json").write_text(json.dumps(pack), encoding="utf-8")
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    finally:
        engines.close()
    return out
