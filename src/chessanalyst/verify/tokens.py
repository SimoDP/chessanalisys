"""Token grammar (§9-bis.2, D-41): parsing only, no pack access."""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field

TOKEN_RE = re.compile(r"\{\{([^{}]*)\}\}")
INT = r"[1-9][0-9]*"
CID = rf"C{INT}"
RID = rf"R{INT}"
RUID = rf"R{INT}\.u{INT}"
NID = rf"N{INT}"
PVID = rf"PV{INT}"
LID = rf"L{INT}"            # filtered line (§5-bis.3, M3)
SQ = r"[a-h][1-8]"
# SAN of python-chess, with the annotation characters "+#!?" accepted and ignored
SAN = r"(?:O-O-O|O-O|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h](?:x[a-h])?[1-8](?:=[QRBN])?)[+#!?]*"
MOVE_AT = rf"({SAN})@({NID})"

PATTERNS: dict[str, re.Pattern] = {
    "mv": re.compile(rf"mv:({CID}|{RUID}|{RID})(:bare)?"),
    "m": re.compile(rf"m:{MOVE_AT}(:num)?"),
    "ev": re.compile(rf"ev:(?:({CID}|{RUID}|{RID}|{NID}|{LID})|{MOVE_AT})"),
    "loss": re.compile(rf"loss:(?:({CID}|{RUID}|{LID})|{MOVE_AT})"),
    "pct": re.compile(rf"pct:(?:({CID})\.(p_user|p_up)|({RUID})\.(p_user)|({RID})\.(p_opp)|root\.(win|draw|loss)"
                      rf"|{MOVE_AT})"),
    "pv": re.compile(rf"pv:({PVID}|{LID}):({INT})"),
    "plan": re.compile(rf"plan:([wb]):({SAN}(?:,{SAN})*)@({NID})"),
    "diag": re.compile(rf"diag:({SQ})-({SQ})"),
    "elo": re.compile(r"elo:(user|opp)(:full)?"),
    "opening": re.compile(r"opening:(name|eco)"),
    "txt": re.compile(r"txt:(opp|me|p_up_group)"),
    "sc": re.compile(r"sc:([a-z_]+)\.(T|R)"),
}


def clean_san(san: str) -> str:
    return san.rstrip("+#!?")


@dataclass
class Token:
    raw: str                       # the whole "{{...}}"
    kind: str
    ref: str | None = None         # main ID argument (CID, RID, RUID, NID, PVID, "root")
    field: str | None = None       # p_user, p_up, p_opp, win/draw/loss, name/eco, user/opp, ...
    san: str | None = None         # MOVE_AT
    node: str | None = None        # MOVE_AT / plan
    n: int | None = None           # pv
    flag: str | None = None        # ":bare", ":num", ":full"
    side: str | None = None        # plan
    moves: list[str] = dc_field(default_factory=list)   # plan
    squares: tuple[str, str] | None = None           # diag


class TokenSyntaxError(ValueError):
    pass


def find_tokens(text: str) -> list[str]:
    return [m.group(0) for m in TOKEN_RE.finditer(text)]


def parse_token(raw: str) -> Token:
    """``raw`` = ``{{kind:arg}}``. Raises TokenSyntaxError (V02)."""
    inner = raw[2:-2]
    kind = inner.split(":", 1)[0]
    pat = PATTERNS.get(kind)
    m = pat.fullmatch(inner) if pat else None
    if m is None:
        raise TokenSyntaxError(f"token non valido: {raw}")
    g = m.groups()
    t = Token(raw=raw, kind=kind)
    if kind == "mv":
        t.ref, t.flag = g[0], g[1]
    elif kind == "m":
        t.san, t.node, t.flag = clean_san(g[0]), g[1], g[2]
    elif kind in ("ev", "loss"):
        if g[0]:
            t.ref = g[0]
        else:
            t.san, t.node = clean_san(g[1]), g[2]
    elif kind == "pct":
        if g[0]:
            t.ref, t.field = g[0], g[1]
        elif g[2]:
            t.ref, t.field = g[2], g[3]
        elif g[4]:
            t.ref, t.field = g[4], g[5]
        elif g[6]:
            t.ref, t.field = "root", g[6]
        else:
            t.san, t.node = clean_san(g[7]), g[8]
    elif kind == "pv":
        t.ref, t.n = g[0], int(g[1])
    elif kind == "plan":
        t.side, t.node = g[0], g[-1]
        t.moves = [clean_san(x) for x in g[1].split(",")]
    elif kind == "diag":
        t.squares = (g[0], g[1])
    elif kind in ("elo", "txt", "opening"):
        t.field = g[0]
        t.flag = g[1] if kind == "elo" else None
    elif kind == "sc":
        t.ref, t.field = g[0], g[1]
    return t


CITING_KINDS = ("mv", "m", "ev", "loss", "pct", "pv")


def token_refs(raw: str) -> set[str]:
    """What a data token is about (D-72): its ID (C1, R1.u1, N4, L2, PV3, ``root``) or ``SAN@N`` for a move in a
    node. Tokens that cite no move or value (plan, diag, elo, txt, opening, sc) give the empty set."""
    try:
        t = parse_token(raw)
    except TokenSyntaxError:
        return set()
    if t.kind not in CITING_KINDS:
        return set()
    if t.ref:
        return {t.ref}
    return {f"{t.san}@{t.node}"} if t.san and t.node else set()
