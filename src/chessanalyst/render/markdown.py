"""Markdown render (§8.6, §9-bis.1): tokens replaced by the data, tables from
``pack.tables``, titles, header, fixed sentences and technical report.

The input is a (possibly degraded) output dict: a block or unit carrying
``_unverified`` gets the V06 mark; a section carrying ``_unavailable`` is
rendered with the fixed text ``section_unavailable`` (§10.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chessanalyst.config import Config
from chessanalyst.render.report import REPORT_TITLE, header_lines, report_lines
from chessanalyst.verify.resolve import Resolver
from chessanalyst.verify.tokens import TOKEN_RE


class RenderBug(Exception):
    """V11: the final document breaks a deterministic rule (exit code 1)."""


@dataclass
class RenderInfo:
    llm_model: str | None = None
    references_validated: bool = True
    retries: int = 0
    checks: dict[str, str] = field(default_factory=dict)      # code → "superato" / "avviso" / ...
    removed: list[str] = field(default_factory=list)
    marked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    theory_blocks: int = 0
    theory_share: float = 0.0
    critic: int | None = None          # M4: number of findings of the critic (None = not run or failed)
    usage: dict | None = None          # M6: tokens and cost of the model calls (llm/usage.py)
    document: str = "sections"         # D-72: «keypoints» = the plan comes from plan/outline.py


class Renderer:
    def __init__(self, cfg: Config, pack: dict) -> None:
        self.cfg = cfg
        self.pack = pack
        self.fixed = cfg.wording["fixed"]
        self.resolver = Resolver(pack, cfg.wording)
        self.theory_used = False

    def text(self, unit: dict, mark_theory: bool = True) -> str:
        out = TOKEN_RE.sub(lambda m: self.resolver.resolve(m.group(0)).text, unit["text"])
        if unit.get("source") == "theory" and mark_theory:
            self.theory_used = True
            out += " †"
        if unit.get("_unverified"):
            out += f" {self.fixed['unverified_mark']}"
        return out

    @staticmethod
    def _cell(s: str) -> str:
        return s.replace("|", "\\|").replace("\n", " ")

    def data_table(self, blk: dict) -> list[str]:
        t = self.pack["tables"][blk["ref"]]
        cells = blk.get("text_cells") or {}
        empty = self.cfg.tables["empty_text_cell"]
        out = ["| " + " | ".join(self._cell(c["header"]) for c in t["columns"]) + " |",
               "| " + " | ".join("---" for _ in t["columns"]) + " |"]
        for row in t["rows"]:
            vals = []
            for c in t["columns"]:
                if c["kind"] == "data":
                    vals.append(row["cells"].get(c["key"]) or "")
                else:
                    u = cells.get(row["id"], {}).get(c["key"])
                    vals.append(self.text(u) if u else empty)
            out.append("| " + " | ".join(self._cell(v) for v in vals) + " |")
        if t["footnote"]:
            out += ["", t["footnote"]]
        return out

    def text_table(self, blk: dict) -> list[str]:
        out = ["| " + " | ".join(self._cell(self.text({"text": h})) for h in blk["columns"]) + " |",
               "| " + " | ".join("---" for _ in blk["columns"]) + " |"]
        for row in blk["rows"]:
            vals = [self.text(c, mark_theory=False) for c in row]
            if any(c["source"] == "theory" for c in row):   # one † per row of a text table
                self.theory_used = True
                vals[-1] += " †"
            out.append("| " + " | ".join(self._cell(v) for v in vals) + " |")
        return out

    def block(self, blk: dict) -> list[str]:
        t = blk["type"]
        if t == "p":
            return [self.text(blk)]
        if t in ("ul", "ol"):
            return [(f"{k}. " if t == "ol" else "- ") + self.text(it) for k, it in enumerate(blk["items"], 1)]
        if t == "line":
            line = f"**{self.resolver.pv_text(blk['pv'], blk['plies'])}**"
            return [line + (f" — {self.text(blk['caption'])}" if blk.get("caption") else "")]
        if t == "table":
            return self.data_table(blk)
        return self.text_table(blk)

    def section(self, entry: dict, sec: dict | None) -> list[str]:
        out = [f"## {entry['title']}", ""]
        if entry["maia_low_confidence"]:
            out += [self.fixed["maia_low_confidence"], ""]
        if sec is None or sec.get("_unavailable"):
            return out + [self.fixed["section_unavailable"], ""]
        for blk in sec["blocks"]:
            out += self.block(blk) + [""]
        for t in entry.get("auto_tables") or []:          # D-72: the render places the tables of the point
            if t in self.pack["tables"]:
                out += self.data_table({"type": "table", "ref": t}) + [""]
        return out

    def document(self, output: dict, info: RenderInfo) -> str:
        secs = {s["id"]: s for s in output["sections"]}
        lines = header_lines(self.cfg, self.pack, info)
        for entry in self.pack["section_plan"]:
            if entry["required"]:
                lines += self.section(entry, secs.get(entry["id"]))
        lines += report_lines(self.cfg, self.pack, output, info)
        if self.theory_used:
            lines += ["---", "", self.fixed["theory_footnote"], ""]
        doc = "\n".join(lines).rstrip() + "\n"
        check_document(self.cfg, self.pack, doc)
        return doc


def check_document(cfg: Config, pack: dict, doc: str) -> None:
    """V11 (§10.1): fixed low-confidence sentence where expected, unstable nodes
    in the report, no unresolved token."""
    if "{{" in doc or "}}" in doc:
        raise RenderBug("V11: token non risolto nel documento")
    sentence = cfg.wording["fixed"]["maia_low_confidence"]
    for e in pack["section_plan"]:
        if e["required"] and e["maia_low_confidence"]:
            head = f"## {e['title']}\n\n{sentence}"
            if head not in doc:
                raise RenderBug(f"V11: frase di bassa confidenza assente all'inizio di {e['id']}")
    report = doc.split(f"## {REPORT_TITLE}", 1)[-1]
    for n in pack["nodes"]:
        if n["unstable_depth"] and n["id"] not in report:
            raise RenderBug(f"V11: nodo instabile {n['id']} non elencato nel rapporto")


def render_markdown(cfg: Config, pack: dict, output: dict, info: RenderInfo | None = None) -> str:
    return Renderer(cfg, pack).document(output, info or RenderInfo())
