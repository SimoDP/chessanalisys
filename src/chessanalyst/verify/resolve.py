"""Token resolution against the pack (§9-bis.2): V02, V04 and the rendered text.

A resolved token carries its rendered text, its data class (for V08/V10) and
the IDs it cites (for V07 c).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import chess

from chessanalyst.engines.types import CP_CLAMP
from chessanalyst.render.format_it import fmt_eval, fmt_loss, fmt_pct, fmt_wdl, numbered, tb_outcome
from chessanalyst.verify.plan_check import PlanError, check_diag, check_plan, render_plan
from chessanalyst.verify.tokens import Token, TokenSyntaxError, parse_token

ELO_SCALE_NAMES = {"fide": "FIDE", "lichess": "Lichess", "chesscom": "chess.com"}


class ResolveError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Resolved:
    token: Token
    text: str
    data: str                  # ev | loss | pv | pct_maia | pct_root | plan | sc | move | other
    cites: set[str] = field(default_factory=set)
    value: Any = None          # for assertions: (cp, mate) or probability


def _v02(msg: str) -> ResolveError:
    return ResolveError("V02", msg)


def _v04(msg: str) -> ResolveError:
    return ResolveError("V04", msg)


class Resolver:
    def __init__(self, pack: dict, wording: dict) -> None:
        self.pack = pack
        self.wording = wording
        self.user = pack["user"]
        self.user_color = chess.WHITE if self.user["color"] == "w" else chess.BLACK
        self.opp_name = wording["colors"]["b" if self.user["color"] == "w" else "w"]
        self.me_name = wording["colors"][self.user["color"]]
        self.root = chess.Board(pack["position"]["fen"])
        eng = pack["engine"]
        self.cands = {c["id"]: c for c in eng["candidates"]}
        self.replies = {r["id"]: r for r in eng["replies"]}
        self.ruids = {u["id"]: (r, u) for r in eng["replies"] for u in r["user_best"]}
        self.pvs = {p["id"]: p for p in eng["pvs"]}
        self.nodes = {n["id"]: n for n in pack["nodes"]}
        self.tb = pack.get("tablebase")          # M2: exact result at the root, values in words

    # -- helpers -------------------------------------------------------------
    def node(self, nid: str) -> dict:
        n = self.nodes.get(nid)
        if n is None or not n["citable"]:
            raise _v02(f"nodo inesistente o non citabile: {nid}")
        return n

    def board(self, nid: str) -> chess.Board:
        return chess.Board(self.node(nid)["fen"])

    def move_in(self, nid: str, san: str) -> tuple[chess.Board, chess.Move]:
        b = self.board(nid)
        try:
            mv = b.parse_san(san)
        except ValueError:
            raise _v04(f"{san} non è legale nel nodo {nid}") from None
        return b, mv

    def line_of(self, nid: str, uci: str) -> dict | None:
        """Row of ``uci`` in the node's MultiPV or in a restricted search of the same position."""
        n = self.node(nid)
        for ln in n["multipv"]:
            if ln["uci"] == uci:
                return ln
        for other in self.pack["nodes"]:
            if other["fen"] == n["fen"] and other["root_moves"]:
                for ln in other["multipv"]:
                    if ln["uci"] == uci:
                        return ln
        return None

    def _ev_text(self, cp: int, mate: int | None, root_node: bool = False) -> str:
        if self.tb is not None:          # tablebase position: the exact result, in words (§3.3)
            key = self.tb["result_text_key"] if root_node else tb_outcome(cp, mate, CP_CLAMP)
            return self.wording["tablebase"]["results"][key]
        return fmt_eval(cp, mate, opp_name=self.opp_name)

    def _loss_text(self, loss_cp: int, mate: bool, best: tuple[int, int | None], move: tuple[int, int | None]) -> str:
        if self.tb is not None:          # same outcome as the best move or not
            same = tb_outcome(*best, CP_CLAMP) == tb_outcome(*move, CP_CLAMP)
            return self.wording["tablebase"]["loss_none" if same else "loss_decisive"]
        return fmt_loss(loss_cp, mate)

    def _ruid(self, ref: str) -> tuple[dict, dict]:
        if ref not in self.ruids:
            raise _v02(f"ID inesistente: {ref}")
        return self.ruids[ref]

    def _reply_board(self, r: dict) -> chess.Board:
        b = self.root.copy(stack=False)
        b.push_uci(r["uci"])
        return b

    # -- resolution ----------------------------------------------------------
    def resolve(self, raw: str) -> Resolved:
        try:
            t = parse_token(raw)
        except TokenSyntaxError as e:
            raise _v02(str(e)) from None
        return getattr(self, f"_r_{t.kind}")(t)

    def _r_mv(self, t: Token) -> Resolved:
        ref = t.ref
        if ref in self.cands:
            board, san = self.root, self.cands[ref]["san"]
        elif ref in self.replies:
            board, san = self.root, self.replies[ref]["san"]
        elif "." in ref:
            r, u = self._ruid(ref)
            board, san = self._reply_board(r), u["san"]
        else:
            raise _v02(f"ID inesistente: {ref}")
        text = san if t.flag == ":bare" else numbered(board, [san])
        return Resolved(t, text, "move", {ref})

    def _r_m(self, t: Token) -> Resolved:
        b, mv = self.move_in(t.node, t.san)
        san = b.san(mv)
        if t.flag == ":num":
            text = numbered(b, [san])
        else:
            text = ("..." if b.turn == chess.BLACK else "") + san
        return Resolved(t, text, "move", {t.node})

    def _move_eval(self, t: Token) -> tuple[dict, dict, chess.Board]:
        b, mv = self.move_in(t.node, t.san)
        ln = self.line_of(t.node, mv.uci())
        if ln is None:
            raise _v02(f"{t.san} non ha una valutazione nel nodo {t.node}")
        return self.node(t.node), ln, b

    def _r_ev(self, t: Token) -> Resolved:
        ref = t.ref
        if ref is None:
            _, ln, _ = self._move_eval(t)
            cp, mate, cites = ln["eval_user_cp"], ln["mate_user"], {t.node}
        elif ref in self.cands:
            c = self.cands[ref]
            cp, mate, cites = c["eval_user_cp"], c["mate_user"], {ref}
        elif ref in self.replies:
            r = self.replies[ref]
            cp, mate, cites = r["eval_user_cp"], r["mate_user"], {ref}
        elif "." in ref:
            _, u = self._ruid(ref)
            cp, mate, cites = u["eval_user_cp"], u["mate_user"], {ref}
        elif ref.startswith("N"):
            n = self.node(ref)
            if not n["multipv"]:
                raise _v02(f"il nodo {ref} non ha valutazioni")
            cp, mate, cites = n["multipv"][0]["eval_user_cp"], n["multipv"][0]["mate_user"], {ref}
        else:
            raise _v02(f"ID inesistente: {ref}")
        return Resolved(t, self._ev_text(cp, mate, root_node=(ref == "N1")), "ev", cites, (cp, mate))

    def _r_loss(self, t: Token) -> Resolved:
        ref = t.ref
        if ref is None:
            n, ln, b = self._move_eval(t)
            best = n["multipv"][0]
            mate = ln["mate_user"] is not None or best["mate_user"] is not None
            diff = best["eval_user_cp"] - ln["eval_user_cp"]
            loss = diff if b.turn == self.user_color else -diff
            text = self._loss_text(max(0, loss), mate, (best["eval_user_cp"], best["mate_user"]),
                                   (ln["eval_user_cp"], ln["mate_user"]))
            return Resolved(t, text, "loss", {t.node}, max(0, loss))
        if ref in self.cands:
            c = self.cands[ref]
            best = self.pack["engine"]["root"]
            mate = c["mate_user"] is not None or best["mate_user"] is not None
            text = self._loss_text(c["loss_cp"], mate, (best["eval_user_cp"], best["mate_user"]),
                                   (c["eval_user_cp"], c["mate_user"]))
            return Resolved(t, text, "loss", {ref}, c["loss_cp"])
        if "." in ref:
            r, u = self._ruid(ref)
            u1 = r["user_best"][0]
            mate = u["mate_user"] is not None or u1["mate_user"] is not None
            text = self._loss_text(u["loss_cp"], mate, (u1["eval_user_cp"], u1["mate_user"]),
                                   (u["eval_user_cp"], u["mate_user"]))
            return Resolved(t, text, "loss", {ref}, u["loss_cp"])
        raise _v02(f"ID inesistente: {ref}")

    def _r_pct(self, t: Token) -> Resolved:
        ref, f = t.ref, t.field
        if ref is None:
            b, mv = self.move_in(t.node, t.san)
            n = self.node(t.node)
            if n["maia"] is None:
                raise _v02(f"il nodo {t.node} non ha la policy di Maia-2")
            p = next((x["p"] for x in n["maia"]["policy"] if x["uci"] == mv.uci()), None)
            text = fmt_pct(p) if p is not None else "<1%"
            return Resolved(t, text, "pct_maia", {t.node}, p if p is not None else 0.0)
        if ref == "root":
            if self.tb is not None:
                raise _v02("con la tablebase l'esito esatto prevale: usa {{ev:N1}} invece di pct:root")
            wdl = self.pack["engine"]["root"]["wdl_user"]
            if wdl is None:
                raise _v02("WDL della radice nullo")
            v = wdl[("win", "draw", "loss").index(f)]
            return Resolved(t, fmt_wdl(v), "pct_root", set(), v / 1000)
        if ref in self.cands:
            p = self.cands[ref][f]
        elif ref in self.replies:
            p = self.replies[ref][f]
        elif "." in ref:
            p = self._ruid(ref)[1][f]
        else:
            raise _v02(f"ID inesistente: {ref}")
        if p is None:
            raise _v02(f"valore nullo: {ref}.{f}")
        return Resolved(t, fmt_pct(p), "pct_maia", {ref}, p)

    def _r_pv(self, t: Token) -> Resolved:
        pv = self.pvs.get(t.ref)
        if pv is None:
            raise _v02(f"ID inesistente: {t.ref}")
        if t.n > len(pv["plies"]):
            raise _v02(f"{t.ref} ha solo {len(pv['plies'])} semimosse")
        return Resolved(t, self.pv_text(t.ref, t.n), "pv", {t.ref}, t.n)

    def pv_text(self, pvid: str, n: int) -> str:
        pv = self.pvs[pvid]
        b = chess.Board(self.nodes[pv["start_node"]]["fen"])
        return numbered(b, pv["plies"][:n])

    def _r_plan(self, t: Token) -> Resolved:
        b = self.board(t.node)
        try:
            sans = check_plan(b, t.side, t.moves, self.pack["constraints"]["plan_max_moves"])
        except PlanError as e:
            raise _v04(str(e)) from None
        return Resolved(t, render_plan(t.side, sans), "plan", {t.node})

    def _r_diag(self, t: Token) -> Resolved:
        try:
            text = check_diag(*t.squares)
        except PlanError as e:
            raise _v04(str(e)) from None
        return Resolved(t, text, "other")

    def _r_elo(self, t: Token) -> Resolved:
        v = self.user["elo_declared"] if t.field == "user" else self.user["opp_elo_declared"]
        text = f"{v} {ELO_SCALE_NAMES[self.user['elo_scale']]}" if t.flag == ":full" else str(v)
        return Resolved(t, text, "other")

    def _r_opening(self, t: Token) -> Resolved:
        op = self.pack["opening"]
        if op is None:
            raise _v02("nessuna apertura riconosciuta")
        return Resolved(t, op[t.field], "other")

    def _r_txt(self, t: Token) -> Resolved:
        if t.field == "opp":
            return Resolved(t, self.opp_name, "other")
        if t.field == "me":
            return Resolved(t, self.me_name, "other")
        group = self.pack["maia"]["p_up_bucket"]
        if group is None:
            raise _v02("p_up assente: txt:p_up_group non disponibile")
        return Resolved(t, self.wording["p_up_group"][group], "other")

    def _r_sc(self, t: Token) -> Resolved:
        raise _v02("punteggi delle categorie non disponibili (da M3)")
