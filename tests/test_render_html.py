"""HTML page of an analysis (M6): clickable moves and lines, board drawn from the FEN, same text as the
Markdown document."""

from __future__ import annotations

import json
import re
import shutil

import chess

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.render.html import folder_parts, html_page, md_to_html, render_html_part, write_html
from chessanalyst.render.markdown import RenderInfo, render_markdown

FEWSHOT = "examples/golden/fewshot/najdorf_w_1900.json"


def _part(cfg, root):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = json.loads((root / FEWSHOT).read_text(encoding="utf-8"))
    return pack, out, render_html_part(cfg, pack, out, RenderInfo())


def _visible(html_text: str) -> str:
    import html

    return html.unescape(re.sub(r"<[^>]+>", " ", html_text))


def test_markdown_subset():
    out = md_to_html("# T\n\nuno **due** *tre* `q<r`\nquattro\n\n> a\n> b\n\n- x\n- y\n\n1. p\n2. q\n\n"
                     "| A | B |\n| --- | --- |\n| 1 \\| 2 | <s> |\n\n---")
    assert "<h1>T</h1>" in out and "<p>uno <strong>due</strong> <em>tre</em> <code>q&lt;r</code><br>quattro</p>" in out
    assert "<blockquote>a<br>b</blockquote>" in out and "<ul><li>x</li><li>y</li></ul>" in out
    assert "<ol><li>p</li><li>q</li></ol>" in out and "<td>1 | 2</td><td>&lt;s&gt;</td>" in out and "<hr>" in out


def test_links_and_positions(cfg, root):
    pack, out, part = _part(cfg, root)
    assert "" not in part.body and "{{" not in part.body
    links = re.findall(r'<a href="#" class="mv" data-i="(\d+)">([^<]*)</a>', part.body)
    assert len(links) == len(part.positions) > 50
    assert sorted(int(i) for i, _ in links) == list(range(len(part.positions)))
    for i, label in links:
        p = part.positions[int(i)]
        board = chess.Board(p["fen"])
        assert board.is_valid()
        san = re.sub(r"^\d+\.(\.\.)?", "", label).lstrip(".")
        if p["last"] and re.match(r"^[KQRBNa-h]", san):         # a move: the position after it
            assert board.piece_at(chess.Move.from_uci(p["last"]).to_square) is not None
    # the text is the same as the Markdown document, without the marks
    md = render_markdown(cfg, pack, out, RenderInfo())
    md = re.sub(r"(?m)^\d+\. ", "", md).replace("\\|", "|")             # <ol> numbers its items itself

    def plain(s):
        return re.sub(r"[\s|*#>`-]+", "", s)

    assert plain(_visible(part.body)) == plain(md)


def test_a_line_is_one_group_in_order(cfg, root):
    _pack, _out, part = _part(cfg, root)
    groups = {}
    for i, p in enumerate(part.positions):
        if p["g"] is not None:
            groups.setdefault(p["g"], []).append(i)
    assert groups
    for idx in groups.values():
        assert idx == list(range(idx[0], idx[-1] + 1))          # consecutive: the arrows step through the line
        for i, j in zip(idx, idx[1:]):                          # each position follows from the previous one
            b = chess.Board(part.positions[i]["fen"])
            b.push(chess.Move.from_uci(part.positions[j]["last"]))
            assert b.fen() == part.positions[j]["fen"]


def test_t1_move_cells_are_links(cfg, root):
    pack, _out, part = _part(cfg, root)
    for c in pack["engine"]["candidates"][:3]:
        cell = rf'<td>(<strong>)?<a href="#" class="mv" data-i="(\d+)">[^<]*{re.escape(c["san"])}</a>'
        m = re.search(cell, part.body)
        assert m, c["san"]
        assert part.positions[int(m.group(2))]["last"] == c["uci"]


def test_page_offline_and_escaped(cfg, root):
    _pack, _out, part = _part(cfg, root)
    page = html_page(cfg.wording["html"], [part, part])
    assert "http://" not in page.replace("http://www.w3.org/2000/svg", "") and "https://" not in page
    assert page.count('<section class="part">') == 2
    idx = [int(i) for i in re.findall(r'data-i="(\d+)"', page)]
    data = json.loads(re.search(r'<script id="pos" type="application/json">(.*?)</script>', page, re.S).group(1))
    assert max(idx) == len(data) - 1 == 2 * len(part.positions) - 1
    groups = {p["g"] for p in data if p["g"] is not None}
    assert len(groups) == 2 * len({p["g"] for p in part.positions if p["g"] is not None})   # no shared groups
    assert 'id="white-king"' in page and cfg.wording["html"]["pieces_credit"].split(" ")[0] in page


def test_write_html_from_folder_and_failure(cfg, root, tmp_path):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    out = json.loads((root / FEWSHOT).read_text(encoding="utf-8"))
    (tmp_path / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
    (tmp_path / "render.json").write_text(json.dumps({"output": out, "info": RenderInfo().__dict__}), encoding="utf-8")
    assert len(folder_parts(cfg, tmp_path)) == 1
    assert write_html(cfg, tmp_path) == tmp_path / "analysis.html"
    (tmp_path / "render.json").write_text("{", encoding="utf-8")          # fault injection: the page is an extra
    (tmp_path / "analysis.html").unlink()
    assert write_html(cfg, tmp_path) is None and not (tmp_path / "analysis.html").exists()
    shutil.rmtree(tmp_path)
