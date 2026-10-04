"""Degraded mode after the last retry (§10.2, ``llm.on_fail``).

``mark``: blocks (or cells, list items, captions) with V01/V02/V03/V04/V05/
V08/V09/V10 errors are removed; V06 blocks are kept with the «non verificato»
mark; V07 (a) missing sections get the fixed text, extra ones are dropped and
the order follows the plan; (b) a missing table is appended, a duplicate is
dropped; (c), (d) and the theory share become warnings. A note with V03 is
removed in both modes (OQ-M1c-10).
``drop``: every section with an error is replaced by the fixed text.
Every removal or mark is listed: nothing is ever dropped silently.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from chessanalyst.verify.checker import NOTE_CELL, VError

REMOVE = {"V01", "V02", "V03", "V04", "V05", "V08", "V09", "V10"}


@dataclass
class Degraded:
    output: dict
    removed: list[str] = field(default_factory=list)
    marked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _where(e: VError) -> str:
    return " · ".join(str(x) for x in (e.section, f"blocco {e.block}" if e.block else None, e.cell) if x)


def degrade(pack: dict, output: dict, errors: list[VError], on_fail: str = "mark") -> Degraded:
    out = copy.deepcopy(output)
    d = Degraded(out)
    plan = [s for s in pack["section_plan"] if s["required"]]
    by_id: dict[str, dict] = {}
    for s in out["sections"]:
        by_id.setdefault(s["id"], s)          # a duplicated section: the first one is kept

    bad_notes = {e.cell for e in errors if e.section is None and (e.cell or "").startswith(NOTE_CELL + " ")}
    if bad_notes:                         # in both modes: a note with V03 is never copied into the report
        out["notes"] = [n for k, n in enumerate(out["notes"], 1) if f"{NOTE_CELL} {k}" not in bad_notes]
        d.removed += [f"{c} del modello (V03)" for c in sorted(bad_notes, key=lambda c: int(c.split()[-1]))]

    if on_fail == "drop":
        bad = {e.section for e in errors if e.section and not (e.code == "V07" and e.sub in ("c", "d"))}
        for sid in bad:
            if sid in by_id:
                by_id[sid] = {"id": sid, "blocks": [], "_unavailable": True}
                d.removed.append(f"{sid} (sezione sostituita dal testo fisso)")
    else:
        # removals: (section, block) → set of cells (None = whole block)
        rm: dict[tuple[str, int], set] = {}
        mk: dict[tuple[str, int], set] = {}
        for e in errors:
            if e.section is None or e.block is None:
                continue
            target = rm if e.code in REMOVE else mk if e.code == "V06" else None
            if target is not None:
                target.setdefault((e.section, e.block), set()).add(e.cell)
                (d.removed if target is rm else d.marked).append(f"{_where(e)} ({e.code})")
        for sid, sec in by_id.items():
            blocks = []
            for b, blk in enumerate(sec["blocks"], 1):
                cells = rm.get((sid, b), set())
                marks = mk.get((sid, b), set())
                blk = _apply(blk, cells, marks)
                if blk is not None:
                    blocks.append(blk)
            sec["blocks"] = blocks
            if not blocks:
                sec["_unavailable"] = True

    sections = []
    seen_tables: set[str] = set()
    for entry in plan:
        sid = entry["id"]
        sec = by_id.get(sid)
        if sec is None:
            sec = {"id": sid, "blocks": [], "_unavailable": True}
            d.removed.append(f"{sid} mancante: testo fisso")
        if not sec.get("_unavailable"):
            kept = []
            for blk in sec["blocks"]:
                if blk["type"] == "table":
                    if blk["ref"] not in entry["tables"] or blk["ref"] in seen_tables:
                        d.removed.append(f"{sid} tabella {blk['ref']} doppia o fuori posto")
                        continue
                    seen_tables.add(blk["ref"])
                kept.append(blk)
            for t in entry["tables"]:
                if t not in seen_tables:
                    kept.append({"type": "table", "ref": t})
                    seen_tables.add(t)
                    d.warnings.append(f"{sid}: tabella {t} aggiunta in coda")
            sec["blocks"] = kept
        sections.append(sec)
    for s in out["sections"]:
        if s["id"] not in {e["id"] for e in plan}:
            d.removed.append(f"{s['id']} non prevista: eliminata")
    out["sections"] = sections
    for e in errors:
        if e.code == "V07" and e.sub in ("c", "d"):
            d.warnings.append(f"{e.section}: {e.detail} ({e.text})")
        elif e.code == "V08" and e.section is None:
            d.warnings.append(f"{e.text} oltre il {e.detail}")
    return d


def _apply(blk: dict, cells: set, marks: set) -> dict | None:
    if None in cells:
        return None
    blk = copy.deepcopy(blk)
    t = blk["type"]
    if t in ("ul", "ol"):
        items = [it for k, it in enumerate(blk["items"], 1) if f"voce {k}" not in cells]
        for k, it in enumerate(blk["items"], 1):
            if f"voce {k}" in marks:
                it["_unverified"] = True
        if not items:
            return None
        blk["items"] = items
    elif t == "line":
        if "didascalia" in cells:
            blk.pop("caption", None)
        elif "didascalia" in marks and blk.get("caption"):
            blk["caption"]["_unverified"] = True
    elif t == "table":
        tc = blk.get("text_cells") or {}
        for row in list(tc):
            for col in list(tc[row]):
                if f"{row}/{col}" in cells:
                    del tc[row][col]
                elif f"{row}/{col}" in marks:
                    tc[row][col]["_unverified"] = True
    elif t == "text_table":
        if cells:
            return None
        if marks:
            for row in blk["rows"]:
                for c in row:
                    c["_unverified"] = True
    elif None in marks:
        blk["_unverified"] = True
    return blk
