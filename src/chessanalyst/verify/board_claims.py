"""V12 (D-71): what the free text says about pieces and squares must be true on the board.

1. «cavallo in c4», «la donna nera in b6», «pedoni b2 e b3», «Torre a1»: in a sentence that describes the
   position (no word of movement or hypothesis, ``verify.yaml: v12.hypothetical``) a piece of that kind (and
   colour, when the sentence says it) stands on the square in the analysed position. In a sentence about a move
   or a line it is enough that such a piece gets there: a legal move from the root or a move of a line of the pack.
2. «il cavallo in c3 protegge d2», «il cavallo nero in f4 attacca g2»: in a sentence that describes the position,
   when the piece stands on the first square, it attacks (or defends) the second one.
3. «il cavallo in c3 è inchiodato»: the piece on that square is pinned (to the king or to a more valuable piece)
   in the analysed position or after a move of the pack (the replies, the candidates and the lines).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import chess

SQUARE = r"[a-h][1-8]"
TOKEN = re.compile(r"\{\{[^{}]*\}\}")
MOVE_TOKEN = re.compile(r"\{\{(?:mv|m|pv|plan):")
SYM = {"p": chess.PAWN, "n": chess.KNIGHT, "b": chess.BISHOP, "r": chess.ROOK, "q": chess.QUEEN, "k": chess.KING}


@dataclass
class Claim:
    text: str
    detail: str


class BoardClaims:
    def __init__(self, pack: dict, words: dict, cfg: dict) -> None:
        self.root = chess.Board(pack["position"]["fen"])
        self.user = chess.WHITE if pack["user"]["color"] == "w" else chess.BLACK
        self.words = words
        self.hyp = {w.lower() for w in cfg["hypothetical"]}
        self.rel = {w: kind for kind, ws in cfg["relations"].items() for w in ws}
        gap = int(cfg["max_gap_words"])
        names = {}
        for sym, n in words["names"].items():
            names[n] = SYM[sym]
            names[words["plural"][sym]] = SYM[sym]
        colors = {}
        for key in ("color_m", "color_f", "color_mp", "color_fp"):
            for side, w in words[key].items():
                colors[w] = chess.WHITE if side == "w" else chess.BLACK
        self.names, self.colors = names, colors
        own = {"tuo", "tua", "tuoi", "tue", "mio", "mia"}
        opp = {"suo", "sua", "suoi", "sue", "avversario", "avversaria"}
        self.own, self.opp = own, opp
        adjectives = "|".join(sorted({re.escape(a) for a in cfg["adjectives"]}, key=len, reverse=True))
        piece = "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True))
        # piece [adj]{0,2} [in|su|di|da] square [(, | e | o ) square]*
        # «il tuo alfiere in f7»: a possessive right before the piece gives its color too (usefulness test, phase 2)
        mine = "|".join(sorted(m for m in own if not m.startswith("mi")))
        self.claim_re = re.compile(
            rf"(?:\b(?P<pre>{mine})\s+)?\b(?P<piece>{piece})\b(?P<adj>(?:\s+(?:{adjectives})\b){{0,2}})\s+(?P<prep>(?:in|su|di|da)\s+)?"
            rf"(?P<squares>{SQUARE}(?:\s*(?:,|\be\b|\bo\b)\s*{SQUARE})*)\b", re.IGNORECASE)
        self.rel_re = re.compile(
            rf"\b(?P<piece>{piece})\b(?:\s+(?:{adjectives})\b){{0,2}}\s+(?:(?:in|su|di|da)\s+)?(?P<sq1>{SQUARE})\b"
            rf"(?P<mid>(?:\W+\w+){{0,{gap}}}?)\W+(?P<verb>{'|'.join(map(re.escape, self.rel))})\b"
            rf"(?P<rest>(?:\W+\w+){{0,{gap}}}?)\W+(?P<sq2>{SQUARE})\b", re.IGNORECASE)
        self.reach = self._reachable(pack)
        def alt(ws: list[str]) -> str:
            return "|".join(map(re.escape, ws))

        phrase = (rf"\b(?P<piece>{piece})\b(?:\s+(?:{adjectives})\b){{0,2}}\s+(?:(?:in|su|di|da)\s+)?"
                  rf"(?P<sq>{SQUARE})\b")
        self.undef_re = re.compile(rf"{phrase}(?:\W+\w+){{0,{gap}}}?\W+(?:{'|'.join(cfg['undefended'])})\b",
                                   re.IGNORECASE)
        self.clause_end = re.compile(cfg["clause_end"], re.IGNORECASE)
        self.pin_res = [
            re.compile(rf"{phrase}(?:\W+\w+){{0,{gap}}}?\W+(?:{alt(cfg['pin_passive'])})\b", re.IGNORECASE),
            re.compile(rf"\b(?:{alt(cfg['pin_active'])})\b(?:\W+\w+){{0,{gap}}}?\W+{phrase}", re.IGNORECASE)]

    def _reachable(self, pack: dict) -> set[tuple[bool, int, int]]:
        """(colour, piece type, square) a piece gets to: legal moves from the root and every move of the lines.
        Also ``self.pinned``: (colour, piece type, square) pinned in the root or in a position of the lines."""
        out = set()
        self.pinned = pinned(self.root)
        for mv in self.root.legal_moves:
            p = self.root.piece_at(mv.from_square)
            out.add((p.color, mv.promotion or p.piece_type, mv.to_square))
        nodes = {n["id"]: n for n in pack["nodes"]}
        eng = pack["engine"]
        seqs = [(p["start_node"], p["plies"]) for p in eng["pvs"]]
        seqs += [(ln["start_node"], ln["plies"]) for ln in pack.get("filtered_lines", [])]
        seqs += [(n["id"], ln["pv"]) for n in pack["nodes"] for ln in n.get("multipv") or []]
        for r in eng["replies"]:
            seqs.append((eng["root"]["node"], [r["san"]]))
            for u in r["user_best"]:
                seqs.append((eng["root"]["node"], [r["san"], u["san"]]))
        for start, plies in seqs:
            if start not in nodes:
                continue
            b = chess.Board(nodes[start]["fen"])
            for san in plies:
                try:
                    mv = b.parse_san(san)
                except ValueError:
                    break
                p = b.piece_at(mv.from_square)
                out.add((p.color, mv.promotion or p.piece_type, mv.to_square))
                b.push(mv)
                self.pinned |= pinned(b)
        return out

    def _color(self, adj: str) -> bool | None:
        for w in adj.lower().split():
            if w in self.colors:
                return self.colors[w]
            if w in self.own:
                return self.user
            if w in self.opp:
                return not self.user
        return None

    def check(self, text: str, about_moves: bool = False, theory: bool = False) -> list[Claim]:
        """``about_moves``: the text describes a move (a cell of a move table). A text that cites a move with a
        token is about lines in all its sentences («la donna in d4 sembra regalata» after «dopo {{mv:R1}}»).
        ``theory``: a theory block talks about plans and systems («Donna in d3», «con l'alfiere in e2»). In both
        cases «piece in square» needs only to be reachable; «Alfiere f1» (the square right after the piece) always
        names where the piece stands now."""
        out: list[Claim] = []
        about_moves = about_moves or bool(MOVE_TOKEN.search(text))
        for sentence in re.split(r"(?<=[.;!?])\s+|\n", text):
            words = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']+", TOKEN.sub(" ", sentence))}
            words |= {w.split("'")[-1] for w in words if "'" in w}
            hypothetical = about_moves or bool(words & self.hyp)
            sentence = TOKEN.sub(" ", sentence)
            for m in self.claim_re.finditer(sentence):
                ptype = self.names[m.group("piece").lower()]
                color = self._color(f"{m.group('pre') or ''} {m.group('adj')}")
                for sq_name in re.findall(SQUARE, m.group("squares")):
                    sq = chess.parse_square(sq_name)
                    there = self.root.piece_at(sq)
                    if there and there.piece_type == ptype and (color is None or there.color == color):
                        continue
                    loose = (hypothetical or theory) and m.group("prep") is not None
                    if loose and any((c, ptype, sq) in self.reach for c in ((color,) if color is not None
                                                                                   else (True, False))):
                        continue
                    found = self._describe(there, sq_name)
                    out.append(Claim(m.group(0), f"{found}: «{m.group('piece')} in {sq_name}» non è vero"
                                     + (" né in una linea del pacchetto" if loose else " nella posizione analizzata")))
            for m in (m for r in self.pin_res for m in r.finditer(sentence)):
                ptype = self.names[m.group("piece").lower()]
                sq = chess.parse_square(m.group("sq"))
                if not any((c, ptype, sq) in self.pinned for c in (True, False)):
                    out.append(Claim(m.group(0), f"nessun pezzo così in {m.group('sq')} è inchiodato, né ora né "
                                                 "nelle linee del pacchetto"))
            if about_moves:
                continue

            def before_hypothesis(m: re.Match) -> bool:
                """A word of movement or hypothesis before the end of the claim («se il Nero la attacca» after it
                does not make «la donna in c4 non ha difensori» hypothetical)."""
                head = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']+", sentence[:m.end()])}
                head |= {w.split("'")[-1] for w in head if "'" in w}
                return bool(head & self.hyp)

            for m in self.rel_re.finditer(sentence):
                if before_hypothesis(m):
                    continue
                ptype = self.names[m.group("piece").lower()]
                sq1 = chess.parse_square(m.group("sq1"))
                p = self.root.piece_at(sq1)
                if p is None or p.piece_type != ptype:
                    continue
                # every square hit by the verb in its clause: «attacca la casa g2 e la donna in c4»
                clause = self.clause_end.split(sentence[m.end("verb"):], maxsplit=1)[0]
                kind = self.rel[m.group("verb").lower()]
                for name in re.findall(rf"\b{SQUARE}\b", clause):
                    sq2 = chess.parse_square(name)
                    if sq2 != sq1 and sq2 not in self.root.attacks(sq1):
                        verb = "non attacca" if kind == "attack" else "non difende"
                        out.append(Claim(m.group(0), f"il pezzo in {m.group('sq1')} {verb} {name}"))
            for m in self.undef_re.finditer(sentence):
                if before_hypothesis(m):
                    continue
                ptype = self.names[m.group("piece").lower()]
                sq = chess.parse_square(m.group("sq"))
                p = self.root.piece_at(sq)
                if p is None or p.piece_type != ptype:
                    continue
                guards = sorted(chess.square_name(g) for g in self.root.attackers(p.color, sq))
                if guards:
                    out.append(Claim(m.group(0), f"il pezzo in {m.group('sq')} è difeso da {', '.join(guards)}"))
        return out

    def _describe(self, piece: chess.Piece | None, sq: str) -> str:
        if piece is None:
            return f"{sq} è vuota"
        w = self.words
        sym = piece.symbol().lower()
        gender = "color_f" if sym in w["feminine"] else "color_m"
        return f"in {sq} c'è {'la' if sym in w['feminine'] else 'il'} {w['names'][sym]} {w[gender]['w' if piece.color else 'b']}"


def pinned(board: chess.Board) -> set[tuple[bool, int, int]]:
    """Pieces pinned to their king, or in front of a more valuable piece of their side on the line of an enemy
    bishop, rook or queen (the pin a player calls a pin) when the pin matters (``pin_matters``)."""
    from chessanalyst.features.motifs import pin_matters
    from chessanalyst.features.values import piece_value

    out = set()
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING:
            continue
        if board.is_pinned(p.color, sq):
            out.add((p.color, p.piece_type, sq))
            continue
        for a in board.attackers(not p.color, sq):
            if board.piece_type_at(a) not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                continue
            beyond = sorted((s for s in chess.SquareSet(chess.ray(a, sq)) if sq in chess.SquareSet(chess.between(a, s))),
                            key=lambda s: chess.square_distance(a, s))
            behind = next((s for s in beyond if board.piece_at(s)), None)       # the first piece behind ``sq``
            if behind is not None:
                q = board.piece_at(behind)
                if q.color == p.color and piece_value(q.piece_type) > piece_value(p.piece_type) \
                        and pin_matters(board, a, behind):
                    out.add((p.color, p.piece_type, sq))
    return out
