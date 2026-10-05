"""Checks V01–V10 on one model response (§10.1, D-46, D-47, D-51, D-52).

All errors are collected (no stop at the first one), each with code, section,
block index (1-based), cell and the offending text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from chessanalyst.config import Config
from chessanalyst.llm.schema import AnalysisOutput
from chessanalyst.verify.board_claims import BoardClaims
from chessanalyst.verify.assertions import eval_band_of, check_assertion
from chessanalyst.verify.contamination import Contamination
from chessanalyst.verify.resolve import ResolveError, Resolved, Resolver
from chessanalyst.verify.scan import Scanner
from chessanalyst.verify.tokens import TokenSyntaxError, find_tokens, parse_token, token_refs
from chessanalyst.verify.wordcount import count_words, tolerance

MOVE_TABLES = ("T1", "T2")          # D-71: tables whose rows are moves (candidates or replies)
NOTE_CELL = "nota"                  # cell of an error in ``notes`` (section and block are None)
CODES = ("V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V10", "V12", "V13")
THEORY_FORBIDDEN = {"ev", "loss", "pct_maia", "pct_root", "pv", "sc"}
SOURCE_RULES = {   # §10.1, V10: (needs one of, may not contain)
    "engine": ({"ev", "loss", "pv", "pct_root", "line"}, {"pct_maia", "plan", "sc"}),
    "maia": ({"pct_maia"}, {"ev", "loss", "pv", "plan"}),
    "feature": ({"feature"}, {"ev", "loss", "pct_maia", "pct_root", "pv", "plan"}),
    "theory": (set(), THEORY_FORBIDDEN),
    "mixed": ({"ev", "loss", "pv", "pct_maia", "pct_root", "assertion", "line", "sc"}, set()),
}


@dataclass
class VError:
    code: str
    section: str | None
    block: int | None
    cell: str | None
    text: str
    detail: str = ""
    sub: str | None = None          # V07: "a" | "b" | "c" | "d"

    def to_dict(self, hints: dict) -> dict:
        return {"code": self.code + (f"({self.sub})" if self.sub else ""), "section": self.section,
                "block": self.block, "cell": self.cell, "text": self.text, "detail": self.detail,
                "hint": hints.get(self.code, "")}

    def line(self, hints: dict) -> str:
        """``V03 · S06 · blocco 2 · «...Nc6» · <suggerimento>`` (§9.3)."""
        parts = [self.code + (f"({self.sub})" if self.sub else "")]
        if self.section:
            parts.append(self.section)
        if self.block is not None:
            parts.append(f"blocco {self.block}" + (f", {self.cell}" if self.cell else ""))
        elif self.cell and self.cell.startswith(NOTE_CELL + " "):
            parts.append(self.cell)
        elif self.cell and self.code == "V01":         # schema error: the path of the field (sections.0.blocks.2…)
            parts.append(f"campo {self.cell}")
        parts.append(f"«{self.text}»")
        if self.detail:
            parts.append(self.detail)
        parts.append(hints.get(self.code, ""))
        return " · ".join(p for p in parts if p)


@dataclass
class Unit:
    """One text written by the model, with its location."""
    section: str
    block: int
    cell: str | None
    text: str
    source: str | None              # None for TextTable headers
    assertions: list[dict]
    in_line: bool = False
    move_cell: bool = False         # D-71: a text cell of a move table (T1, T2): it describes a move
    ref: dict | None = field(default=None, repr=False, compare=False)   # the dict of the output holding ``source``


@dataclass
class Result:
    errors: list[VError] = field(default_factory=list)
    output: dict | None = None
    words_by_section: dict[str, dict[str, int | None]] = field(default_factory=dict)
    theory_blocks: list[dict] = field(default_factory=list)
    theory_share: float = 0.0
    passed_schema: bool = False
    relabeled: list[str] = field(default_factory=list)      # D-71: sources fixed by the checker

    @property
    def codes(self) -> set[str]:
        return {e.code for e in self.errors}

    def has_retry_errors(self) -> bool:
        return any(e.code != "V07" or e.sub != "d" for e in self.errors)


def data_class(raw: str) -> str | None:
    """Data class of a token from its syntax alone (None if the syntax is invalid)."""
    try:
        t = parse_token(raw)
    except TokenSyntaxError:
        return None
    if t.kind == "pct":
        return "pct_root" if t.ref == "root" else "pct_maia"
    return {"ev": "ev", "loss": "loss", "pv": "pv", "plan": "plan", "sc": "sc", "m": "move", "mv": "move"}.get(
        t.kind, "other")


def extract_output(response: dict) -> tuple[dict | None, list[VError]]:
    """The ``input`` of the ``submit_analysis`` tool_use block of a recorded API response.
    A bare output (``schema_version`` at top level) is accepted as is."""
    if "schema_version" in response:
        return response, []
    if response.get("stop_reason") == "max_tokens":
        return None, [VError("V01", None, None, None, "stop_reason = max_tokens", "risposta troncata")]
    for block in response.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == "submit_analysis":
            if not isinstance(block.get("input"), dict):     # arguments that are not valid JSON (OQ-M1c-9)
                return None, [VError("V01", None, None, None, "argomenti di submit_analysis",
                                     "non sono un oggetto JSON valido")]
            out = dict(block["input"])
            # D-70: the two constant keys are filled in, a retry for them only re-sends the whole analysis
            out.setdefault("schema_version", "1")    # the only version of Appendix F
            out.setdefault("notes", [])
            return out, []
    return None, [VError("V01", None, None, None, "tool_use assente", "nessun blocco submit_analysis")]


def iter_units(output: dict) -> list[Unit]:
    units: list[Unit] = []
    for sec in output["sections"]:
        sid = sec["id"]
        for b, blk in enumerate(sec["blocks"], 1):
            t = blk["type"]
            if t == "p":
                units.append(Unit(sid, b, None, blk["text"], blk["source"], blk.get("assertions") or [], ref=blk))
            elif t in ("ul", "ol"):
                for k, it in enumerate(blk["items"], 1):
                    units.append(Unit(sid, b, f"voce {k}", it["text"], it["source"], it.get("assertions") or [], ref=it))
            elif t == "line" and blk.get("caption"):
                c = blk["caption"]
                units.append(Unit(sid, b, "didascalia", c["text"], c["source"], c.get("assertions") or [],
                                  in_line=True, ref=c))
            elif t == "table":
                for row, cols in (blk.get("text_cells") or {}).items():
                    for col, c in cols.items():
                        units.append(Unit(sid, b, f"{row}/{col}", c["text"], c["source"], c.get("assertions") or [],
                                          move_cell=blk.get("ref") in MOVE_TABLES, ref=c))
            elif t == "text_table":
                for k, h in enumerate(blk["columns"], 1):
                    units.append(Unit(sid, b, f"intestazione {k}", h, None, []))
                for r, row in enumerate(blk["rows"], 1):
                    for k, c in enumerate(row, 1):
                        units.append(Unit(sid, b, f"riga {r}, colonna {k}", c["text"], c["source"],
                                          c.get("assertions") or [], ref=c))
    return units


class Checker:
    def __init__(self, cfg: Config, pack: dict, *, fewshot_epd: str | None = None,
                 terms: list[list[str]] | None = None) -> None:
        self.cfg = cfg
        self.pack = pack
        self.wording = cfg.wording
        self.resolver = Resolver(pack, cfg.wording)
        self.board_claims = BoardClaims(pack, cfg.wording["pieces"], cfg.verify["v12"])
        root = pack["engine"]["root"]
        try:
            self._root_band = eval_band_of(root["eval_user_cp"], root["mate_user"], cfg.wording["eval_bands"])
        except (KeyError, TypeError, ValueError):
            self._root_band = None
        self._root_band_text = self._band_words(self._root_band)
        self.scanner = Scanner(cfg.verify, cfg.wording["v03_allowed_literals"])
        self.plan = {s["id"]: s for s in pack["section_plan"]}
        self.word_re = cfg.verify["word"]
        check_v09 = fewshot_epd is not None and terms is not None and pack["position"]["epd"] != fewshot_epd
        name = pack["opening"]["name"] if pack["opening"] else None
        self.contamination = Contamination(terms, name) if check_v09 else None

    # ------------------------------------------------------------------------
    def check(self, response: dict) -> Result:
        res = Result()
        raw, errs = extract_output(response)
        if raw is None:
            res.errors = errs
            return res
        try:
            out = AnalysisOutput.model_validate(raw).model_dump()
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                res.errors.append(VError("V01", None, None, loc, str(err.get("input"))[:80], err["msg"]))
            return res
        res.passed_schema = True
        res.output = out
        errors: list[VError] = []
        units = iter_units(out)
        sec_cites: dict[str, set[str]] = {}
        words: dict[str, int] = {}
        theory_words = total_words = 0
        for u in units:
            fixed = self._relabel(u)
            if fixed:
                res.relabeled.append(f"{u.section} · blocco {u.block}" + (f", {u.cell}" if u.cell else "")
                                     + f": {u.source} → {fixed}")
                u.source = u.ref["source"] = fixed
            errors += self._check_unit(u, sec_cites.setdefault(u.section, set()))
            n = count_words(u.text, self.word_re)
            words[u.section] = words.get(u.section, 0) + n
            total_words += n
            if u.source == "theory":
                theory_words += n
                res.theory_blocks.append({"section": u.section, "block": u.block, "cell": u.cell,
                                          "text": u.text, "words": n})
        errors += self._check_notes(out)
        errors += self._check_lines(out)
        errors += self._check_tables(out)
        errors += self._check_structure(out, sec_cites, words, res)
        res.theory_share = round(theory_words / total_words, 3) if total_words else 0.0
        cap = self.cfg.thresholds.theory_max_share[self.pack["user"]["anchor"]]
        if res.theory_share > cap:
            errors.append(VError("V08", None, None, None, f"quota theory {res.theory_share:.2f}",
                                 f"tetto {cap:.2f}"))
        res.errors = sorted(errors, key=lambda e: CODES.index(e.code))
        return res

    # ------------------------------------------------------------------------
    def _relabel(self, u: Unit) -> str | None:
        """D-71: ``source`` is a label of what the block cites, so a mix-up between engine, maia and feature is
        fixed instead of costing a retry or a removal: data of more than one kind → ``mixed``; no data at all →
        ``theory`` where theory is allowed. Anything else stays a V10 (or V08) error."""
        if u.source is None or u.ref is None:
            return None
        data = {data_class(raw) for raw in find_tokens(u.text)} - {None, "move", "other"}
        if u.assertions:
            data.add("assertion")
        if any(a["kind"] == "feature" for a in u.assertions):
            data.add("feature")
        if u.in_line:
            data.add("line")
        need, forbid = SOURCE_RULES[u.source]
        if not ((need and not data & need) or data & forbid):
            return None
        # a theory block with data and a plan outside theory/mixed stay errors (AC-16, AC-23): they say something
        # about what is verified, not only about the label
        if u.source == "theory" or "plan" in data:
            return None
        if data & SOURCE_RULES["mixed"][0]:
            return "mixed" if u.source != "mixed" else None
        theory_ok = u.section in self.plan and self.plan[u.section]["theory_allowed"]
        if not data and theory_ok and u.source != "theory":
            return "theory"
        return None

    def _band_words(self, band: str | None) -> str:
        if band is None:
            return ""
        family, _, sign = band.partition("_")
        b = self.wording["eval_bands"].get(family, {})
        return b.get("text") or b.get(f"text_{sign}", band)

    def _verdict_conflicts(self, u: Unit) -> list[str]:
        """D-71: in the first section, no verdict that contradicts a clear evaluation of the root (N1)."""
        vc = self.cfg.verify["v12"]["verdict"]
        if u.section != vc["section"] or not self._root_band:
            return []
        family, _, sign = self._root_band.partition("_")
        if family not in vc["from_bands"]:
            return []
        low = u.text.lower()
        return [w for w in vc[f"{sign}_forbidden"] if w in low]

    def _check_unit(self, u: Unit, cites: set[str]) -> list[VError]:
        errs: list[VError] = []
        E = lambda code, text, detail="": VError(code, u.section, u.block, u.cell, text, detail)  # noqa: E731
        for hit in self.scanner.markup_hits(u.text):
            errs.append(E("V01", hit, "markup non ammesso"))
        resolved: list[Resolved] = []
        failed: set[str] = set()
        max_plies = self.plan[u.section]["max_pv_plies"] if u.section in self.plan else None
        allowed = self.plan.get(u.section, {}).get("cites_allowed")      # D-72: one fact, one section
        for raw in find_tokens(u.text):
            refs = token_refs(raw)
            cites |= refs
            out = sorted(refs - set(allowed)) if allowed is not None else []
            if out:
                errs.append(E("V13", raw, f"{', '.join(out)} non è un dato di questa sezione"))
            try:
                r = self.resolver.resolve(raw)
            except ResolveError as e:
                errs.append(E(e.code, raw, e.message))
                kind = data_class(raw)          # an unresolved token still counts for V08/V10
                if kind:
                    failed.add(kind)
                continue
            resolved.append(r)
            cites |= r.cites
            if r.data == "pv" and max_plies is not None and r.value > max_plies:
                errs.append(E("V05", raw, f"{r.value} semimosse, massimo {max_plies}"))
        for hit in self.scanner.v03_hits(u.text):
            errs.append(E("V03", hit))
        for claim in self.board_claims.check(u.text, about_moves=u.move_cell,
                                                    theory=u.source == "theory"):     # D-71
            errs.append(E("V12", claim.text, claim.detail))
        for word in self._verdict_conflicts(u):
            errs.append(E("V12", word, f"la posizione è «{self._root_band_text}» (banda di N1)"))
        for a in u.assertions:
            why = check_assertion(a, self.pack, self.resolver, self.wording)
            if why:
                errs.append(E("V06", f"{a['kind']} {a.get('key') or a.get('ref') or a.get('id')}", why))
        if u.source is None:
            return errs
        data = {r.data for r in resolved} | failed
        if u.in_line:
            data.add("line")
        if u.source == "theory":
            if u.section in self.plan and not self.plan[u.section]["theory_allowed"]:
                errs.append(E("V08", u.text[:60], "theory non ammessa in questa sezione"))
            bad = sorted(data & THEORY_FORBIDDEN)
            if bad:
                errs.append(E("V08", u.text[:60], "token di dati in un blocco theory: " + ", ".join(bad)))
        if self.contamination is not None:
            for term in self.contamination.hits(u.text):
                errs.append(E("V09", term))
        need, forbid = SOURCE_RULES[u.source]
        have = set(data)
        if u.assertions:
            have.add("assertion")
        if any(a["kind"] == "feature" for a in u.assertions):
            have.add("feature")
        if need and not have & need:
            errs.append(E("V10", u.text[:60], f"source {u.source} senza i dati richiesti"))
        bad = sorted(have & forbid)
        if bad:
            errs.append(E("V10", u.text[:60], f"source {u.source} con " + ", ".join(bad)))
        return errs

    def _check_notes(self, out: dict) -> list[VError]:
        """V03 on ``notes`` (OQ-M1c-10): they are copied into the report as written, so no
        token (not even a valid one), move, digit or chain in clear."""
        errs = []
        for k, note in enumerate(out["notes"], 1):
            cell = f"{NOTE_CELL} {k}"
            if "{{" in note or "}}" in note:
                shown = ", ".join(find_tokens(note)) or note[:60]
                errs.append(VError("V03", None, None, cell, shown, "nelle note niente token: scrivi a parole"))
            for hit in self.scanner.v03_hits(note):
                errs.append(VError("V03", None, None, cell, hit))
        return errs

    def _check_lines(self, out: dict) -> list[VError]:
        errs = []
        for sec in out["sections"]:
            mp = self.plan[sec["id"]]["max_pv_plies"] if sec["id"] in self.plan else None
            for b, blk in enumerate(sec["blocks"], 1):
                if blk["type"] != "line":
                    continue
                pv = self.resolver.pvs.get(blk["pv"]) or self.resolver.lines.get(blk["pv"])
                desc = f"line {blk['pv']}:{blk['plies']}"
                if pv is None:
                    errs.append(VError("V02", sec["id"], b, None, desc, "variante inesistente"))
                elif blk["plies"] > len(pv["plies"]):
                    errs.append(VError("V02", sec["id"], b, None, desc, f"la variante ha {len(pv['plies'])} semimosse"))
                if mp is not None and blk["plies"] > mp:
                    errs.append(VError("V05", sec["id"], b, None, desc, f"massimo {mp} semimosse"))
        return errs

    def _check_tables(self, out: dict) -> list[VError]:
        """Text cells of data tables: existing row, text column (V02)."""
        errs = []
        tables = self.pack["tables"]
        for sec in out["sections"]:
            for b, blk in enumerate(sec["blocks"], 1):
                if blk["type"] != "table" or blk["ref"] not in tables:
                    continue
                t = tables[blk["ref"]]
                rows = {r["id"] for r in t["rows"]}
                text_cols = {c["key"] for c in t["columns"] if c["kind"] == "text"}
                for row, cols in (blk.get("text_cells") or {}).items():
                    for col in cols:
                        if row not in rows or col not in text_cols:
                            errs.append(VError("V02", sec["id"], b, f"{row}/{col}", f"{blk['ref']} {row}/{col}",
                                               "riga o colonna di testo inesistente"))
        return errs

    def _check_structure(self, out: dict, sec_cites: dict[str, set[str]], words: dict[str, int],
                         res: Result) -> list[VError]:
        errs = []
        required = [s["id"] for s in self.pack["section_plan"] if s["required"]]
        got = [s["id"] for s in out["sections"]]
        V7 = lambda sub, sid, text, detail="", block=None: VError("V07", sid, block, None, text, detail, sub)  # noqa: E731
        for sid in required:
            if sid not in got:
                errs.append(V7("a", sid, sid, "sezione mancante"))
        for sid in got:
            if sid not in required:
                errs.append(V7("a", sid, sid, "sezione non prevista"))
        common = [s for s in got if s in required]
        if common != [s for s in required if s in got] or len(set(got)) != len(got):
            errs.append(V7("a", None, " ".join(got), "ordine o duplicati: atteso " + " ".join(required)))
        # (b) tables
        where: dict[str, list[tuple[str, int]]] = {}
        for sec in out["sections"]:
            for b, blk in enumerate(sec["blocks"], 1):
                if blk["type"] == "table":
                    where.setdefault(blk["ref"], []).append((sec["id"], b))
        planned = {t: s["id"] for s in self.pack["section_plan"] if s["required"] for t in s["tables"]}
        for t, sid in planned.items():
            n = sum(1 for s, _ in where.get(t, []) if s == sid)
            if n != 1 and sid in got:
                errs.append(V7("b", sid, t, f"la tabella compare {n} volte (attesa una)"))
        for t, locs in where.items():
            for s, b in locs:
                if planned.get(t) != s:
                    errs.append(V7("b", s, t, "tabella non prevista in questa sezione", b))
        # (c) must_cover, (d) words
        tol = self.cfg.verify["word_tolerance"]
        for s in self.pack["section_plan"]:
            if not s["required"]:
                continue
            sid = s["id"]
            actual = words.get(sid, 0)
            res.words_by_section[sid] = {"budget": s["word_budget"], "actual": actual}
            if sid not in got:
                continue
            missing = [x for x in s["must_cover"] if x not in sec_cites.get(sid, set())]
            if missing:
                errs.append(V7("c", sid, ", ".join(missing), "ID di must_cover non citati"))
            if s["word_budget"] is not None and abs(actual - s["word_budget"]) > tolerance(s["word_budget"], tol):
                errs.append(V7("d", sid, f"{actual} parole", f"budget {s['word_budget']}"))
        return errs


def restrict_plan(pack: dict, sections: set[str]) -> dict:
    """A pack whose plan requires only ``sections`` (fragments such as ``_s07_alt.json``)."""
    plan = [dict(s, required=s["required"] and s["id"] in sections) for s in pack["section_plan"]]
    return {**pack, "section_plan": plan}


def verify_response(cfg: Config, pack: dict, response: dict, *, fewshot_epd: str | None = None,
                    terms: list[list[str]] | None = None) -> Result:
    return Checker(cfg, pack, fewshot_epd=fewshot_epd, terms=terms).check(response)


def error_lines(errors: list[VError], hints: dict[str, Any]) -> list[str]:
    return [e.line(hints) for e in errors]
