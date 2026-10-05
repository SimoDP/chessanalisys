"""Key points of the analysis, chosen and ordered by the code (phase B of the plan after v1.0, OQ-BENCH).

From a pack, an ORDERED list of key points: each has a type, the IDs the text can cite, the facts (from the
engines, Maia-2 and python-chess, already computed) and a priority. The model only writes them.

Types (``thresholds.yaml: keypoints``, order per side to move):

- ``verdict``: band of N1, who stands better, the best move and why (its facts; «positional» when the material
  is equal and the advantage is large);
- ``recommendation`` (user to move): the recommended candidate, whether it is the only move, the natural trap
  to avoid;
- ``main_danger``: with the opponent to move, its reply with the largest damage against the Maia-2 average of its
  moves, with its probability; with the user to move, the strongest threat line of the null move against the
  user;
- ``likely_reply``: the most probable replies of the opponent (to the recommended move, or at the root), each
  with the user's right answer, whether it is the only one, and the natural trap (a probable answer that loses);
- ``opportunity``: probable replies that give the user something (eval jump over the reference);
- ``systems`` (user to move): several equivalent candidates (no single best move);
- ``plan``: the features for the quiet moves (weaknesses of the opponent, own assets, pawn islands, the
  opponent's typical move);
- ``reasoning``: «how to think here», a short list (theory), last.

Every reply is in one point only: a reply that is an opportunity or the main danger is not repeated in
``likely_reply``. Nothing here reads the engines: only the pack.
"""

from __future__ import annotations

from typing import Any

import chess

from chessanalyst.config import Config
from chessanalyst.features.motifs import move_facts, piece_name
from chessanalyst.features.values import piece_value
from chessanalyst.verify.assertions import eval_band_of, maia_band_of


def _value(cp: int | None, mate: int | None, mate_cp: int) -> int:
    if mate is not None:
        return mate_cp if mate > 0 else -mate_cp
    return cp or 0


def _policy(node: dict | None) -> dict[str, float]:
    if not node or not node.get("maia"):
        return {}
    return {e["uci"]: e["p"] for e in node["maia"]["policy"]}


class _Ctx:
    def __init__(self, cfg: Config, pack: dict):
        self.cfg, self.pack = cfg, pack
        self.kp = cfg.thresholds.keypoints
        self.mate_cp = cfg.thresholds.scoring.lines.mate_cp
        self.bands, self.maia_bands = cfg.wording["eval_bands"], cfg.wording["maia_bands"]
        self.words = cfg.wording["pieces"]
        self.nodes = {n["id"]: n for n in pack["nodes"]}
        self.root = pack["nodes"][0]
        self.user = pack["user"]["color"]
        self.user_to_move = pack["position"]["user_to_move"]
        self.detail = str(pack["user"]["detail_level"])
        self.eng = pack["engine"]
        self.cands = {c["id"]: c for c in self.eng["candidates"]}

    def band(self, cp, mate) -> str:
        return eval_band_of(cp or 0, mate, self.bands)

    def maia_band(self, p: float | None) -> str | None:
        return None if p is None else maia_band_of(p, self.maia_bands)

    def facts_of(self, fen: str, san: str) -> dict:
        try:
            return move_facts(chess.Board(fen), san, self.words)
        except ValueError:
            return {}

    def ev(self, x: dict) -> int:
        return _value(x.get("eval_user_cp"), x.get("mate_user"), self.mate_cp)


# --- the opponent's replies, in both modes ------------------------------------


def _replies(c: _Ctx) -> tuple[list[dict], dict | None]:
    """(replies, node where the opponent moves). Each reply: ref, san, node, p, eval, answers (ref, san, eval,
    loss, p) ordered by eval. Opponent to move: the R rows; user to move: the opponent's moves after the
    recommended candidate (E3 nodes under its node), cited as ``SAN@N``."""
    out = []
    if not c.user_to_move:
        for r in c.eng["replies"]:
            answers = [{"ref": u["id"], "san": u["san"], "eval_user_cp": u["eval_user_cp"],
                        "mate_user": u["mate_user"], "loss_cp": u["loss_cp"], "p": u["p_user"]}
                       for u in r["user_best"]]
            out.append({"ref": r["id"], "san": r["san"], "node": r["node"], "p": r["p_opp"],
                        "eval_user_cp": r["eval_user_cp"], "mate_user": r["mate_user"], "answers": answers})
        return out, c.root
    rec = (c.pack.get("recommendation") or {}).get("id")
    cand = c.cands.get(rec) if rec else None
    if cand is None or cand.get("node") is None:
        return [], None
    at = c.nodes[cand["node"]]
    pol = _policy(at)
    seen = set()
    for n in c.pack["nodes"]:
        if n["parent"] != at["id"] or not n["citable"] or not n["multipv"] or n["via_san"] in seen:
            continue
        seen.add(n["via_san"])
        best = c.ev(n["multipv"][0])
        upol = _policy(n)
        answers = [{"ref": f"{m['san']}@{n['id']}", "san": m["san"], "eval_user_cp": m["eval_user_cp"],
                    "mate_user": m["mate_user"], "loss_cp": max(0, best - c.ev(m)), "p": upol.get(m["uci"])}
                   for m in n["multipv"]]
        out.append({"ref": f"{n['via_san']}@{at['id']}", "san": n["via_san"], "node": n["id"],
                    "p": pol.get(n["via_uci"], 0.0), "eval_user_cp": n["multipv"][0]["eval_user_cp"],
                    "mate_user": n["multipv"][0]["mate_user"], "answers": answers})
    return out, at


def _reference(c: _Ctx, at: dict | None, without: str | None = None) -> float | None:
    """What the user can expect from the opponent's move: the Maia-2 average of the opponent's moves at the root
    other than ``without`` (opponent to move), or the value of the recommended move (user to move)."""
    if at is None:
        return None
    if c.user_to_move:
        return c.ev(at["multipv"][0]) if at.get("multipv") else None
    pol = _policy(at)
    ps = [(pol.get(m["uci"], 0.0), c.ev(m)) for m in at.get("multipv") or [] if m["san"] != without]
    total = sum(p for p, _ in ps)
    return sum(p * v for p, v in ps) / total if total > 0 else None


def _reply_facts(c: _Ctx, r: dict, at: dict) -> dict:
    kp = c.kp
    ok = [a for a in r["answers"] if a["loss_cp"] <= kp.answer_loss_max_cp]
    best = r["answers"][0] if r["answers"] else None
    second = r["answers"][1] if len(r["answers"]) > 1 else None
    traps = [a for a in r["answers"] if (a["p"] or 0) >= kp.trap_p_min and a["loss_cp"] >= kp.trap_loss_min_cp]
    out = {"ref": r["ref"], "san": r["san"], "p_opp": r["p"], "maia_band": c.maia_band(r["p"]),
           "eval_user_cp": r["eval_user_cp"], "mate_user": r["mate_user"],
           "band": c.band(r["eval_user_cp"], r["mate_user"]), "move": c.facts_of(at["fen"], r["san"])}
    wing = _space(c, at["fen"], r["san"])
    if wing:
        out["gains_space"] = wing
    if best is not None:
        after = c.nodes.get(r["node"])
        out["answer"] = {"ref": best["ref"], "san": best["san"], "eval_user_cp": best["eval_user_cp"],
                         "band": c.band(best["eval_user_cp"], best["mate_user"]), "p_user": best["p"],
                         "move": c.facts_of(after["fen"], best["san"]) if after else {}}
        out["only_answer"] = len(ok) == 1 and second is not None and second["loss_cp"] >= kp.only_move_gap_cp
        out["good_answers"] = [a["ref"] for a in ok]
    if traps:
        t = max(traps, key=lambda a: a["p"])
        out["trap"] = {"ref": t["ref"], "san": t["san"], "p_user": t["p"], "loss_cp": t["loss_cp"],
                       "eval_user_cp": t["eval_user_cp"], "band": c.band(t["eval_user_cp"], t["mate_user"])}
    return out


def _space(c: _Ctx, fen: str, san: str) -> str | None:
    """A pawn that arrives in the other half of the board: the wing where it gains space."""
    b = chess.Board(fen)
    try:
        mv = b.parse_san(san)
    except ValueError:
        return None
    if b.piece_type_at(mv.from_square) != chess.PAWN:
        return None
    rank = chess.square_rank(mv.to_square) if b.turn == chess.WHITE else 7 - chess.square_rank(mv.to_square)
    if rank < c.kp.space_rank:
        return None
    w = c.cfg.wording["wings"]
    return w["queenside"] if chess.square_file(mv.to_square) < 4 else w["kingside"]


def _ids_of(f: dict) -> list[str]:
    ids = [f["ref"]]
    for k in ("answer", "trap"):
        if k in f:
            ids.append(f[k]["ref"])
    return ids


# --- the points -----------------------------------------------------------------


def _material_words(c: _Ctx, bal: int) -> str:
    """The material balance in words («un pedone in più»), so the text has no number to write."""
    from chessanalyst.llm.prompt import number_words

    w = c.cfg.wording["material_words"]
    if bal == 0:
        return w["even"]
    n = abs(bal)
    count = w["one"] if n == 1 else number_words(n)
    return w["up" if bal > 0 else "down"].format(n=f"{count} {w['pawn'] if n == 1 else w['pawns']}")


def _easy_share(c: _Ctx, node: dict) -> float | None:
    """Maia-2 probability, for the side to move, of a move losing at most ``answer_loss_max_cp``."""
    if not node.get("multipv"):
        return None
    pol = _policy(node)
    sign = 1 if (node["fen"].split()[1] == c.user) else -1        # the values are the user's
    vals = [(m, sign * c.ev(m)) for m in node["multipv"]]
    best = max(v for _, v in vals)
    return sum(pol.get(m["uci"], 0.0) for m, v in vals if best - v <= c.kp.answer_loss_max_cp)


def _verdict(c: _Ctx) -> dict:
    root = c.eng["root"]
    band = c.band(root["eval_user_cp"], root["mate_user"])
    better = "none" if band == "equal" else ("user" if band.endswith("_plus") else "opp")
    bal = next((f["value"] for f in c.pack["features"] if f["key"] == "material_balance"), 0) or 0
    bal_user = bal if c.user == "w" else -bal
    facts: dict[str, Any] = {"band": band, "eval_user_cp": root["eval_user_cp"], "mate_user": root["mate_user"],
                             "better": better, "to_move": "user" if c.user_to_move else "opp",
                             "material_balance_user": bal_user, "material": _material_words(c, bal_user),
                             "positional": bal_user == 0 and abs(c.ev(root)) >= c.kp.positional_min_cp}
    opp = "b" if c.user == "w" else "w"
    if bal_user > 0 and band == "equal" and any(f["key"] == "check_available" and f["side"] == opp
                                                for f in c.pack["features"]):
        facts["compensation"] = "checks"           # material up, but the opponent's checks hold the balance
    easy = _easy_share(c, c.root)
    if easy is not None and easy >= c.kp.easy_min_p:
        facts["easy_for"] = "user" if c.user_to_move else "opp"   # Maia-2: the side to move finds a good move
    ids = ["N1"]
    best_san = c.root["multipv"][0]["san"] if c.root.get("multipv") else None
    if best_san and band != "equal":           # in a level position the first move is not «the» move
        if c.user_to_move:
            ref = next((x["id"] for x in c.eng["candidates"] if x["san"] == best_san), f"{best_san}@N1")
        else:
            ref = next((x["id"] for x in c.eng["replies"] if x["san"] == best_san), f"{best_san}@N1")
        facts["best"] = {"ref": ref, "san": best_san, "move": c.facts_of(c.root["fen"], best_san)}
        ids.append(ref)
    if c.pack.get("tablebase"):
        facts["tablebase"] = c.pack["tablebase"]["result_text_key"]
    return {"type": "verdict", "ids": ids, "facts": facts}


def _recommendation(c: _Ctx) -> dict | None:
    rec = (c.pack.get("recommendation") or {}).get("id")
    if not c.user_to_move or rec not in c.cands:
        return None
    x = c.cands[rec]
    others = sorted((o for o in c.eng["candidates"] if o["id"] != rec), key=lambda o: o["loss_cp"])
    second = others[0] if others else None
    facts = {"ref": rec, "san": x["san"], "eval_user_cp": x["eval_user_cp"], "mate_user": x["mate_user"],
             "band": c.band(x["eval_user_cp"], x["mate_user"]), "p_user": x["p_user"],
             "maia_band": c.maia_band(x["p_user"]), "move": c.facts_of(c.root["fen"], x["san"]),
             "only_move": second is not None and second["loss_cp"] - x["loss_cp"] >= c.kp.only_move_gap_cp}
    ids = [rec]
    if second is not None:
        facts["second"] = {"ref": second["id"], "san": second["san"], "loss_cp": second["loss_cp"]}
        ids.append(second["id"])
    traps = [o for o in others if o.get("category") == "natural_trap"]
    if traps:
        t = max(traps, key=lambda o: o["p_user"])
        if second is not None and t["id"] == second["id"]:      # the second best is also the natural trap
            facts["second"]["is_trap"] = True
            return {"type": "recommendation", "ids": ids, "facts": facts}
        facts["trap"] = {"ref": t["id"], "san": t["san"], "p_user": t["p_user"], "loss_cp": t["loss_cp"],
                         "band": c.band(t["eval_user_cp"], t["mate_user"])}
        if t["id"] not in ids:
            ids.append(t["id"])
    return {"type": "recommendation", "ids": ids, "facts": facts}


def _main_danger(c: _Ctx, replies: list[dict], at: dict | None) -> dict | None:
    kp = c.kp
    if not c.user_to_move:
        if not replies or at is None:
            return None

        def damage(x: dict) -> float:     # against the average of the other moves: the game if it misses it
            ref = _reference(c, at, without=x["san"])
            return -1e9 if ref is None else ref - _value(x["eval_user_cp"], x["mate_user"], c.mate_cp)

        r = max(replies, key=damage)
        if damage(r) < kp.danger_min_cp:
            return None
        f = dict(_reply_facts(c, r, at), damage_cp=round(damage(r)))
        line = next((ln["id"] for ln in c.pack.get("filtered_lines", [])
                     if ln["kind"] == "threat" and ln["start_node"] == c.root["id"] and ln["plies"][:1] == [r["san"]]),
                    None)
        ids = _ids_of(f)
        if line:
            f["line"] = line
            ids.append(line)
        return {"type": "main_danger", "ids": ids, "facts": f, "_reply": r["ref"]}
    lines = [ln for ln in c.pack.get("filtered_lines", [])
             if ln["kind"] == "threat" and ln["against_user"] and ln["impact_cp"] >= kp.danger_min_cp]
    if not lines:
        return None
    ln = max(lines, key=lambda x: (x["p_att"] * x["impact_cp"], -int(x["id"][1:])))
    start = c.nodes[ln["start_node"]]
    f = {"line": ln["id"], "san": ln["plies"][0], "impact_cp": ln["impact_cp"], "p_att": ln["p_att"],
         "maia_band": c.maia_band(ln["p_att"]), "visible_at_level": ln["visible_at_level"],
         "move": c.facts_of(start["fen"], ln["plies"][0]), "hypothetical": True}
    return {"type": "main_danger", "ids": [ln["id"]], "facts": f}


def _likely(c: _Ctx, replies: list[dict], at: dict | None, used: set[str]) -> dict | None:
    if at is None:
        return None
    pick = [r for r in sorted(replies, key=lambda r: -r["p"]) if r["p"] >= c.kp.likely_min_p and r["ref"] not in used]
    pick = pick[: c.kp.max_replies[c.detail]]
    if not pick:
        return None
    facts = [_reply_facts(c, r, at) for r in pick]
    used.update(r["ref"] for r in pick)
    return {"type": "likely_reply", "ids": [i for f in facts for i in _ids_of(f)],
            "facts": {"after": None if not c.user_to_move else c.pack["recommendation"]["id"], "replies": facts}}


def _opportunity(c: _Ctx, replies: list[dict], at: dict | None, ref: float | None, used: set[str]) -> dict | None:
    if at is None or ref is None:
        return None
    kp = c.kp
    pick = [r for r in sorted(replies, key=lambda r: -r["p"])
            if r["ref"] not in used and r["p"] >= kp.opportunity_min_p
            and _value(r["eval_user_cp"], r["mate_user"], c.mate_cp) - ref >= kp.opportunity_gain_cp]
    pick = pick[: kp.max_replies[c.detail]]
    if not pick:
        return None
    facts = [dict(_reply_facts(c, r, at), gain_cp=round(_value(r["eval_user_cp"], r["mate_user"], c.mate_cp) - ref))
             for r in pick]
    used.update(r["ref"] for r in pick)
    return {"type": "opportunity", "ids": [i for f in facts for i in _ids_of(f)], "facts": {"replies": facts}}


def _systems(c: _Ctx) -> dict | None:
    if not c.user_to_move:
        return None
    eq = [x for x in c.eng["candidates"] if x["explained"] and x["loss_cp"] <= c.kp.systems_loss_max_cp]
    if len(eq) < c.kp.systems_min_moves:
        return None
    facts = [{"ref": x["id"], "san": x["san"], "eval_user_cp": x["eval_user_cp"], "p_user": x["p_user"],
              "move": c.facts_of(c.root["fen"], x["san"])} for x in eq]
    return {"type": "systems", "ids": [x["id"] for x in eq], "facts": {"moves": facts}}


def _loose_pieces(c: _Ctx) -> list[dict]:
    """Pieces attacked more times than they are defended (or attacked and undefended), kings excluded: the
    user's to defend first, then the opponent's targets."""
    board = chess.Board(c.pack["position"]["fen"])
    me = chess.WHITE if c.user == "w" else chess.BLACK
    out = []
    for sq, p in sorted(board.piece_map().items()):
        if p.piece_type == chess.KING:
            continue
        att, dfd = len(board.attackers(not p.color, sq)), len(board.attackers(p.color, sq))
        if att and att > dfd:
            mine = p.color == me
            out.append({"key": "to_defend" if mine else "target", "of": "user" if mine else "opp",
                        "squares": [chess.square_name(sq)], "value": {"attackers": att, "defenders": dfd}})
    return sorted(out, key=lambda x: x["key"] != "to_defend")


def _at(board: chess.Board, sq: int, words: dict) -> str:
    return f"{piece_name(board.piece_at(sq), words)} in {chess.square_name(sq)}"


def _pins(c: _Ctx, board: chess.Board) -> list[dict]:
    """Pieces in front of their king or of a more valuable piece of their side, on the line of an enemy bishop,
    rook or queen (the pin a player calls a pin): the user's first, then the opponent's."""
    me = chess.WHITE if c.user == "w" else chess.BLACK
    out = []
    for sq, p in sorted(board.piece_map().items()):
        if p.piece_type == chess.KING:
            continue
        for a in sorted(board.attackers(not p.color, sq)):
            if board.piece_type_at(a) not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                continue
            beyond = sorted((s for s in chess.SquareSet(chess.ray(a, sq)) if sq in chess.SquareSet(chess.between(a, s))),
                            key=lambda s: chess.square_distance(a, s))
            behind = next((s for s in beyond if board.piece_at(s)), None)
            q = board.piece_at(behind) if behind is not None else None
            if q is not None and q.color == p.color and (
                    q.piece_type == chess.KING or piece_value(q.piece_type) > piece_value(p.piece_type)):
                out.append({"key": "pinned", "of": "user" if p.color == me else "opp",
                            "squares": [chess.square_name(sq)], "piece": _at(board, sq, c.words),
                            "by": _at(board, a, c.words), "behind": _at(board, behind, c.words)})
                break
    return sorted(out, key=lambda x: x["of"] != "user")


def _long_diagonals(c: _Ctx, board: chess.Board) -> list[dict]:
    """Bishops on a long diagonal (a1-h8, h1-a8) with no pawn of their side on it: the opponent's first."""
    me = chess.WHITE if c.user == "w" else chess.BLACK
    out = []
    diags = {"a1-h8": chess.SquareSet(chess.ray(chess.A1, chess.H8)),
             "h1-a8": chess.SquareSet(chess.ray(chess.H1, chess.A8))}
    for sq in sorted(board.pieces(chess.BISHOP, chess.WHITE) | board.pieces(chess.BISHOP, chess.BLACK)):
        color = board.color_at(sq)
        for name, squares in diags.items():
            if sq in squares and not any(board.piece_at(s) == chess.Piece(chess.PAWN, color) for s in squares):
                out.append({"key": "bishop_long_diagonal", "of": "user" if color == me else "opp",
                            "squares": [chess.square_name(sq)], "diagonal": name, "piece": _at(board, sq, c.words)})
    return sorted(out, key=lambda x: x["of"] != "opp")


def _king_squares(c: _Ctx, board: chess.Board) -> list[dict]:
    """For each king, the square next to it that only the king defends and that most enemy pieces can hit now,
    from behind one of their own pieces (it moves away) or with a knight jump; kept with at least
    ``king_attack_min`` pieces. The user's king first."""
    me = chess.WHITE if c.user == "w" else chess.BLACK
    out = []
    for color in (me, not me):
        king = board.king(color)
        if king is None:
            continue
        best = None
        for t in sorted(chess.SquareSet(chess.BB_KING_ATTACKS[king])):
            if board.color_at(t) == (not color) or any(d != king for d in board.attackers(color, t)):
                continue
            hits = [f"{_at(board, a, c.words)}" for a in sorted(board.attackers(not color, t))]
            for a in sorted(board.pieces(chess.QUEEN, not color) | board.pieces(chess.BISHOP, not color)
                            | board.pieces(chess.ROOK, not color)):
                between = [s for s in chess.SquareSet(chess.between(a, t)) if board.piece_at(s)]
                if (chess.SquareSet(chess.ray(a, t)) and len(between) == 1 and board.color_at(between[0]) == (not color)
                        and a not in board.attackers(not color, t) and _slides(board.piece_type_at(a), a, t)):
                    hits.append(f"{_at(board, a, c.words)} dietro {_at(board, between[0], c.words)}")
            for n in sorted(board.pieces(chess.KNIGHT, not color)):
                for d in sorted(chess.SquareSet(chess.BB_KNIGHT_ATTACKS[n])):
                    if board.color_at(d) != (not color) and t in chess.SquareSet(chess.BB_KNIGHT_ATTACKS[d]):
                        hits.append(f"{_at(board, n, c.words)} con il salto in {chess.square_name(d)}")
            if len(hits) >= c.kp.king_attack_min and (best is None or len(hits) > len(best["pieces"])):
                best = {"key": "king_square", "of": "user" if color == me else "opp",
                        "squares": [chess.square_name(t)], "king": _at(board, king, c.words),
                        "occupant": _at(board, t, c.words) if board.piece_at(t) else None, "pieces": hits}
        if best:
            out.append(best)
    return out


def _slides(ptype: int, a: int, t: int) -> bool:
    straight = chess.square_file(a) == chess.square_file(t) or chess.square_rank(a) == chess.square_rank(t)
    return ptype == chess.QUEEN or (ptype == chess.ROOK) == straight


def _pawn_breaks(c: _Ctx, board: chess.Board) -> list[dict]:
    """The opponent's pawn push (one or two squares) that would attack a pawn of the user on the
    ``break_files``, the one Maia-2 gives most often where the opponent moves in the tree (at most one)."""
    opp = chess.BLACK if c.user == "w" else chess.WHITE
    step, start = (8, 1) if opp == chess.WHITE else (-8, 6)
    nodes = [n for n in c.pack["nodes"] if n.get("maia") and n["fen"].split()[1] == ("w" if opp else "b")]
    best = None
    for sq in sorted(board.pieces(chess.PAWN, opp)):
        dests = [sq + step] + ([sq + 2 * step] if chess.square_rank(sq) == start else [])
        for d in dests:
            if not 0 <= d < 64 or any(board.piece_at(x) for x in chess.SquareSet(chess.between(sq, d)) | {d}):
                continue
            hit = [t for t in chess.SquareSet(chess.BB_PAWN_ATTACKS[opp][d])
                   if board.piece_at(t) == chess.Piece(chess.PAWN, not opp)
                   and chess.FILE_NAMES[chess.square_file(t)] in c.kp.break_files]
            uci = chess.square_name(sq) + chess.square_name(d)
            p = sum(_policy(n).get(uci, 0.0) for n in nodes) / len(nodes) if nodes else 0.0
            if hit and p > 0 and (best is None or p > best[0]):
                best = (p, {"key": "pawn_break", "of": "opp", "from": chess.square_name(sq), "to": chess.square_name(d),
                            "piece": _at(board, sq, c.words), "hits": [_at(board, t, c.words) for t in hit]})
    return [best[1]] if best else []


def _plan(c: _Ctx) -> dict | None:
    kp = c.kp
    opp = "b" if c.user == "w" else "w"
    side = {"user": c.user, "opp": opp}
    feats = c.pack["features"]
    out: list[dict] = []
    cm = c.eng.get("context_move")
    cm_san = next(iter(cm["san_by_node"].values()), None) if cm else None
    room = kp.plan_max_facts - (1 if cm_san else 0)       # the opponent's typical move always has a place
    board = chess.Board(c.pack["position"]["fen"])
    out += (_loose_pieces(c) + _pins(c, board) + _king_squares(c, board) + _pawn_breaks(c, board)
            + _long_diagonals(c, board))
    islands = {f["side"]: f["value"] for f in feats if f["key"] == "pawn_island_count"}
    if islands.get(opp, 0) - islands.get(c.user, 0) >= kp.island_diff_min:
        out.append({"key": "pawn_island_count", "of": "opp", "value": islands[opp], "user_value": islands.get(c.user)})
    for key, who in kp.plan_features:
        out += [{"key": key, "of": who, "squares": f["squares"], "value": f["value"]}
                for f in feats if f["key"] == key and f["side"] == side[who]]
    seen = {(i["key"], tuple(i.get("squares") or [])) for i in out}
    out = [i for i in out if not (i["key"] == "outpost" and ("knight_outpost", tuple(i["squares"])) in seen)]
    out = out[:room]
    if c.band(c.eng["root"]["eval_user_cp"], c.eng["root"]["mate_user"]) in kp.secondary_bands:
        for i in out:                        # clearly worse: the user's assets do not change the verdict
            if i["of"] == "user" and i["key"] in kp.user_assets:
                i["secondary"] = True
    for i in out:
        if i["key"] == "rook_open_file":
            i["file"] = i["squares"][0][0]
    if cm_san:
        out.append({"key": "context_move", "of": "opp", "san": cm_san})
    if not out:
        return None
    return {"type": "plan", "ids": [], "facts": {"items": out}}


def key_points(cfg: Config, pack: dict) -> list[dict]:
    """The ordered key points of the pack (``K1``, ``K2``, … in order), at most ``max_points`` of the detail."""
    c = _Ctx(cfg, pack)
    replies, at = _replies(c)
    used: set[str] = set()
    built: dict[str, dict | None] = {}
    built["verdict"] = _verdict(c)
    built["recommendation"] = _recommendation(c)
    danger = _main_danger(c, replies, at)
    if danger is not None and "_reply" in danger:
        used.add(danger.pop("_reply"))
    ref = _reference(c, at, without=danger["facts"]["san"] if danger and not c.user_to_move else None)
    built["main_danger"] = danger
    rec = built["recommendation"]
    forced = [r for r in replies if r["p"] >= c.kp.forced_p] if c.user_to_move and rec else []
    if forced:                    # the reply nearly everybody plays is part of the move: told with it
        f = _reply_facts(c, forced[0], at)
        rec["facts"]["reply"] = f
        rec["ids"] += [i for i in _ids_of(f) if i not in rec["ids"]]
        used.add(forced[0]["ref"])
    built["opportunity"] = _opportunity(c, replies, at, ref, used)    # before likely_reply: a gift is not a reply
    built["likely_reply"] = _likely(c, replies, at, used)
    built["systems"] = _systems(c)
    built["plan"] = _plan(c)
    built["reasoning"] = {"type": "reasoning", "ids": [],
                          "facts": {"items": cfg.thresholds.keypoints.reasoning_items[c.detail]}}
    if built["systems"] is not None and rec is not None:       # one fact, one section
        rec["facts"]["only_move"] = False
        sy = built["systems"]
        sy["facts"]["moves"] = [m for m in sy["facts"]["moves"] if m["ref"] != rec["facts"]["ref"]]
        sy["ids"] = [m["ref"] for m in sy["facts"]["moves"]]
        if rec["facts"].get("second", {}).get("ref") in sy["ids"]:
            rec["ids"].remove(rec["facts"].pop("second")["ref"])
    order = cfg.thresholds.keypoints.order["user_to_move" if c.user_to_move else "opp_to_move"]
    points = [built[t] for t in order if built.get(t) is not None]
    points = points[: cfg.thresholds.keypoints.max_points[c.detail]]
    elsewhere = {i for p in points if p["type"] != "verdict" for i in p["ids"]}
    v = points[0]
    if "best" in v["facts"] and v["facts"]["best"]["ref"] in elsewhere:     # one fact, one section
        v["ids"] = [i for i in v["ids"] if i != v["facts"]["best"]["ref"]]
        v["facts"]["best"]["told_in"] = next(p["type"] for p in points[1:] if v["facts"]["best"]["ref"] in p["ids"])
    for k, p in enumerate(points, 1):
        p["id"], p["priority"] = f"K{k}", k
    return [{"id": p["id"], "type": p["type"], "priority": p["priority"], "ids": p["ids"], "facts": p["facts"]}
            for p in points]
