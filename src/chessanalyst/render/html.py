"""HTML page of an analysis (M6): the same document as ``analysis.md``, with every move, line and node position
clickable and a board next to the text.

The Markdown renderer runs in «link mode»: the text of a token that names a position is wrapped in private-use
markers (``\\ue000<index>\\ue001<text>\\ue002``) and the position goes to a table; a small converter for the
Markdown subset that the renderer writes (titles, paragraphs, lists, tables, quotes, bold, italic, code) turns the
document into HTML and the markers into links. The board is drawn in the browser from the FEN, with the piece
drawings of ``chess.svg`` embedded once, so the page works offline and stays small.
"""

from __future__ import annotations

import html
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chess
import chess.svg

from chessanalyst.config import Config
from chessanalyst.render.markdown import RenderInfo, Renderer
from chessanalyst.verify.tokens import TOKEN_RE, parse_token

log = logging.getLogger(__name__)

M_OPEN, M_MID, M_CLOSE = "", "", ""
MARK_RE = re.compile(f"{M_OPEN}(\\d+){M_MID}(.*?){M_CLOSE}")


@dataclass
class Positions:
    """Clickable positions of a document: FEN, last move, line group (for stepping with the arrows)."""
    items: list[dict[str, Any]] = field(default_factory=list)
    groups: int = 0

    def add(self, board: chess.Board, move: chess.Move | None, group: int | None = None) -> int:
        self.items.append({"fen": board.fen(), "last": move.uci() if move else None, "g": group})
        return len(self.items) - 1

    def new_group(self) -> int:
        self.groups += 1
        return self.groups


def _mark(i: int, text: str) -> str:
    return f"{M_OPEN}{i}{M_MID}{text}{M_CLOSE}"


class LinkRenderer(Renderer):
    """Markdown renderer whose move tokens carry the position they lead to."""

    def __init__(self, cfg: Config, pack: dict, positions: Positions) -> None:
        super().__init__(cfg, pack)
        self.pos = positions

    def _after(self, board: chess.Board, san: str) -> tuple[chess.Board, chess.Move]:
        b = board.copy(stack=False)
        mv = b.parse_san(san)
        b.push(mv)
        return b, mv

    def _line(self, start: chess.Board, plies: list[str]) -> str:
        """``6.Be3 e5 7.Nb3`` with every half-move linked, in one group."""
        g = self.pos.new_group()
        b = start.copy(stack=False)
        num, out = b.fullmove_number, []
        for i, san in enumerate(plies):
            label = f"{num}.{san}" if b.turn == chess.WHITE else (f"{num}...{san}" if i == 0 else san)
            if b.turn == chess.BLACK:
                num += 1
            mv = b.parse_san(san)
            b.push(mv)
            out.append(_mark(self.pos.add(b, mv, g), label))
        return " ".join(out)

    def _token(self, raw: str) -> str:
        r = self.resolver
        text = r.resolve(raw).text
        t = parse_token(raw)
        try:
            if t.kind == "mv":
                if t.ref in r.cands:
                    b, mv = self._after(r.root, r.cands[t.ref]["san"])
                elif t.ref in r.replies:
                    b, mv = self._after(r.root, r.replies[t.ref]["san"])
                else:
                    rep, u = r.ruids[t.ref]
                    b, mv = self._after(r._reply_board(rep), u["san"])
                return _mark(self.pos.add(b, mv), text)
            if t.kind == "m":
                b, mv = self._after(r.board(t.node), t.san)
                return _mark(self.pos.add(b, mv), text)
            if t.kind == "pv":
                pv = r.pvs.get(t.ref) or r.lines[t.ref]
                return self._line(chess.Board(r.nodes[pv["start_node"]]["fen"]), pv["plies"][: t.n])
            if t.kind == "ev" and t.ref and t.ref.startswith("N"):
                n = r.node(t.ref)
                return _mark(self.pos.add(chess.Board(n["fen"]), chess.Move.from_uci(n["via_uci"])
                                          if n.get("via_uci") else None), text)
            if t.kind == "ev" and t.ref is None:
                b, mv = self._after(r.board(t.node), t.san)
                return _mark(self.pos.add(b, mv), text)
        except (ValueError, KeyError):
            pass
        return text

    def text(self, unit: dict, mark_theory: bool = True) -> str:
        out = TOKEN_RE.sub(lambda m: self._token(m.group(0)), unit["text"])
        if unit.get("source") == "theory" and mark_theory:
            self.theory_used = True
            out += " †"
        if unit.get("_unverified"):
            out += f" {self.fixed['unverified_mark']}"
        return out

    def block(self, blk: dict) -> list[str]:
        if blk["type"] == "line":
            r = self.resolver
            pv = r.pvs.get(blk["pv"]) or r.lines[blk["pv"]]
            line = f"**{self._line(chess.Board(r.nodes[pv['start_node']]['fen']), pv['plies'][: blk['plies']])}**"
            return [line + (f" — {self.text(blk['caption'])}" if blk.get("caption") else "")]
        return super().block(blk)

    def data_table(self, blk: dict) -> list[str]:
        """T1: the move cell is linked to the position after the move."""
        out = super().data_table(blk)
        if blk["ref"] != "T1":
            return out
        t = self.pack["tables"]["T1"]
        key = t["columns"][0]["key"]
        r = self.resolver
        for k, row in enumerate(t["rows"]):
            cell = row["cells"].get(key) or ""
            move = r.cands.get(row["id"]) or r.replies.get(row["id"])
            if move is None or not cell:
                continue
            b, mv = self._after(r.root, move["san"])
            plain = cell.replace("**", "").split(" ")[0]
            linked = cell.replace(plain, _mark(self.pos.add(b, mv), plain), 1)
            out[k + 2] = out[k + 2].replace(self._cell(cell), self._cell(linked), 1)
        return out


# -- Markdown subset → HTML --------------------------------------------------------------------------------------


def _inline(s: str) -> str:
    s = html.escape(s, quote=False).replace("\\|", "|")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", s)
    return MARK_RE.sub(lambda m: f'<a href="#" class="mv" data-i="{m.group(1)}">{m.group(2)}</a>', s)


def _cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return parts[1:-1]


def md_to_html(md: str) -> str:
    out: list[str] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("## "):
            out.append(f"<h2>{_inline(ln[3:])}</h2>")
        elif ln.startswith("# "):
            out.append(f"<h1>{_inline(ln[2:])}</h1>")
        elif ln.strip() == "---":
            out.append("<hr>")
        elif ln.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(_inline(lines[i][2:]))
                i += 1
            out.append("<blockquote>" + "<br>".join(quote) + "</blockquote>")
            continue
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            head, body = _cells(rows[0]), [_cells(r) for r in rows[2:]]
            t = ["<div class=\"tw\"><table><thead><tr>" + "".join(f"<th>{_inline(c.strip())}</th>" for c in head) + "</tr></thead><tbody>"]
            t += ["<tr>" + "".join(f"<td>{_inline(c.strip())}</td>" for c in r) + "</tr>" for r in body]
            out.append("".join(t) + "</tbody></table></div>")
            continue
        elif re.match(r"^(- |\d+\. )", ln):
            ordered = not ln.startswith("- ")
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                items.append(_inline(re.sub(r"^(- |\d+\. )", "", lines[i])))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|> |\||- |\d+\. |---$)", lines[i]):
                para.append(_inline(lines[i]))
                i += 1
            out.append("<p>" + "<br>".join(para) + "</p>")
            continue
        i += 1
    return "\n".join(out)


# -- page --------------------------------------------------------------------------------------------------------


@dataclass
class HtmlPart:
    body: str                      # HTML of one document
    positions: list[dict]
    root_fen: str
    flip: bool                     # board seen from Black


def render_html_part(cfg: Config, pack: dict, output: dict, info: RenderInfo) -> HtmlPart:
    pos = Positions()
    md = LinkRenderer(cfg, pack, pos).document(output, info)
    return HtmlPart(md_to_html(md), pos.items, pack["position"]["fen"], pack["user"]["color"] == "b")


def _pieces_defs() -> str:
    return "".join(chess.svg.PIECES.values())


PAGE_CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1f;--muted:#666;--line:#ddd;--accent:#7a4b12;--light:#efe6d6;--dark:#b58863;
--hl:rgba(255,213,79,.55);--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#17171a;--fg:#e8e6e1;--muted:#a3a19c;--line:#38383d;--accent:#e0b46a;
--card:#202024}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,
"Segoe UI",Roboto,sans-serif}.wrap{display:flex;gap:32px;max-width:1280px;margin:0 auto;padding:24px 16px}
main{flex:1;min-width:0}aside{width:380px;flex:none}.panel{position:sticky;top:16px;background:var(--card);
border:1px solid var(--line);border-radius:10px;padding:12px}h1{font-size:1.6em;margin:.2em 0 .6em}
h2{font-size:1.25em;margin:1.6em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:.2em}
blockquote{margin:1em 0;padding:.5em 1em;border-left:3px solid var(--accent);color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:.93em}th,td{border:1px solid var(--line);
padding:6px 8px;text-align:left;vertical-align:top}th{background:rgba(127,127,127,.08)}.tw{overflow-x:auto;margin:1em 0}code{font-size:.85em;
word-break:break-all}a.mv{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent);
white-space:nowrap}a.mv:hover,a.mv.on{background:var(--hl);color:var(--fg)}#board svg{width:100%;height:auto;
display:block}.ctl{display:flex;gap:6px;margin-top:8px}.ctl button{flex:1;padding:6px;border:1px solid var(--line);
background:var(--bg);color:var(--fg);border-radius:6px;cursor:pointer;font-size:1em}#fen{font-size:.75em;
color:var(--muted);margin-top:8px;word-break:break-all}.part+.part{margin-top:3em;padding-top:1em;
border-top:3px double var(--line)}.credit{font-size:.7em;color:var(--muted);margin-top:6px}
@media (max-width:900px){.wrap{flex-direction:column-reverse}aside{width:100%}.panel{position:static}}
"""

PAGE_JS = """
const P=JSON.parse(document.getElementById('pos').textContent);let cur=null,flip=false;
function draw(fen,last){const rows=fen.split(' ')[0].split('/');let s='<svg viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">'
+'';const hl=last?[last.slice(0,2),last.slice(2,4)]:[];
for(let r=0;r<8;r++){let f=0;for(const ch of rows[r]){if(/\\d/.test(ch)){for(let k=0;k<+ch;k++){sq(r,f);f++}}else{sq(r,f,ch);f++}}}
function sq(r,f,p){const x=(flip?7-f:f)*45,y=(flip?7-r:r)*45,name='abcdefgh'[f]+(8-r);
const col=hl.includes(name)?'#d6b656':((r+f)%2?'var(--dark)':'var(--light)');
s+=`<rect x="${x}" y="${y}" width="45" height="45" fill="${col}"/>`;if(p){const c=p===p.toUpperCase()?'white':'black';
const n={p:'pawn',n:'knight',b:'bishop',r:'rook',q:'queen',k:'king'}[p.toLowerCase()];s+=`<use href="#${c}-${n}" transform="translate(${x},${y})"/>`}}
s+='</svg>';document.getElementById('board').innerHTML=s;document.getElementById('fen').textContent=fen}
function show(i){cur=i;document.querySelectorAll('a.mv.on').forEach(a=>a.classList.remove('on'));
document.querySelectorAll(`a.mv[data-i="${i}"]`).forEach(a=>a.classList.add('on'));draw(P[i].fen,P[i].last)}
document.addEventListener('click',e=>{const a=e.target.closest('a.mv');if(!a)return;e.preventDefault();show(+a.dataset.i)});
function step(d){if(cur===null)return;const g=P[cur].g;const j=cur+d;if(g!=null&&P[j]&&P[j].g===g)show(j)}
document.getElementById('prev').onclick=()=>step(-1);document.getElementById('next').onclick=()=>step(1);
document.getElementById('start').onclick=()=>{cur=null;document.querySelectorAll('a.mv.on').forEach(a=>a.classList.remove('on'));
draw(document.getElementById('root').textContent,null)};
document.getElementById('flipb').onclick=()=>{flip=!flip;if(cur!==null)draw(P[cur].fen,P[cur].last);else
draw(document.getElementById('root').textContent,null)};
document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')step(-1);if(e.key==='ArrowRight')step(1)});
flip=document.getElementById('root').dataset.flip==='1';draw(document.getElementById('root').textContent,null);
"""


def html_page(words: dict[str, str], parts: list[HtmlPart]) -> str:
    """One page with one or more documents («entrambi»: the two perspectives) and one board."""
    positions: list[dict] = []
    bodies = []
    for p in parts:
        off = len(positions)
        positions += [dict(x, g=None if x["g"] is None else f"{off}:{x['g']}") for x in p.positions]
        bodies.append('<section class="part">' + re.sub(
            r'data-i="(\d+)"', lambda m: f'data-i="{int(m.group(1)) + off}"', p.body) + "</section>")
    first = parts[0]
    w = {k: html.escape(v) for k, v in words.items()}
    pos_json = json.dumps(positions, separators=(",", ":")).replace("</", "<\\/")
    return (
        "<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{w['title']}</title><style>{PAGE_CSS}</style></head><body><div class=\"wrap\">"
        f"<main>{''.join(bodies)}</main>"
        "<aside><div class=\"panel\"><div id=\"board\"></div>"
        f"<div class=\"ctl\"><button id=\"start\" title=\"{w['start']}\">⟲</button>"
        f"<button id=\"prev\" title=\"{w['prev']}\">◀</button>"
        f"<button id=\"next\" title=\"{w['next']}\">▶</button>"
        f"<button id=\"flipb\" title=\"{w['flip']}\">⇅</button></div>"
        f"<div id=\"fen\"></div><div class=\"credit\">{w['pieces_credit']}</div></div></aside></div>"
        f"<svg width=\"0\" height=\"0\" style=\"position:absolute\" aria-hidden=\"true\"><defs>{_pieces_defs()}</defs></svg>"
        f"<script id=\"pos\" type=\"application/json\">{pos_json}</script>"
        f"<div id=\"root\" hidden data-flip=\"{1 if first.flip else 0}\">{html.escape(first.root_fen)}</div>"
        f"<script>{PAGE_JS}</script></body></html>\n"
    )


def folder_parts(cfg: Config, folder: Path) -> list[HtmlPart]:
    """The documents of an output folder: ``pack.json`` + ``render.json``, or the two colors of «entrambi»
    (the color to move first, as in ``analysis.md``)."""
    def load(name: str) -> dict:
        return json.loads((folder / name).read_text(encoding="utf-8"))

    if (folder / "pack.json").is_file():
        pairs = [(load("pack.json"), load("render.json"))]
    else:
        packs = {c: load(f"pack_{s}.json") for c, s in (("w", "white"), ("b", "black"))}
        first = "w" if chess.Board(packs["w"]["position"]["fen"]).turn == chess.WHITE else "b"
        order = [first, "b" if first == "w" else "w"]
        pairs = [(packs[c], load(f"render_{'white' if c == 'w' else 'black'}.json")) for c in order]
    return [render_html_part(cfg, pack, r["output"], RenderInfo(**r["info"])) for pack, r in pairs]


def write_html(cfg: Config, folder: Path) -> Path | None:
    """``analysis.html`` next to ``analysis.md``. The page is an extra: a failure is logged, the analysis stays."""
    try:
        parts = folder_parts(cfg, folder)
        path = folder / "analysis.html"
        path.write_text(html_page(cfg.wording["html"], parts), encoding="utf-8")
        log.info("analysis.html scritto")
        return path
    except Exception:                                       # noqa: BLE001 — the Markdown analysis is the product
        log.exception("analysis.html non scritto")
        return None
