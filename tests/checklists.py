"""Checklists of the non-Najdorf positions (§8-bis.6): ``fixtures/checklists/<id>.yaml``.

A checklist names the expected sections (matrix of §8.2 for the position's profile), three moves that
must appear in the tokens of the model's answer and two typical errors the text must cite: a move (SAN,
cited by a token) or a concept (``{concept, pattern}``, a regular expression searched in the sections).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from chessanalyst.render.report import REPORT_TITLE
from chessanalyst.verify.checker import extract_output, iter_units
from chessanalyst.verify.resolve import ResolveError, Resolver
from chessanalyst.verify.tokens import find_tokens

ROOT = Path(__file__).resolve().parents[1]
CHECKLISTS = ROOT / "fixtures" / "checklists"
SAN_RE = re.compile(r"O-O-O|O-O|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h]x[a-h][1-8](?:=[QRBN])?|[a-h][1-8](?:=[QRBN])?")


def checklist_ids() -> list[str]:
    return sorted(p.stem for p in CHECKLISTS.glob("*.yaml"))


def load_checklist(name: str) -> dict:
    return yaml.safe_load((CHECKLISTS / f"{name}.yaml").read_text(encoding="utf-8"))


def cited_moves(cfg, pack: dict, output: dict) -> set[str]:
    """SAN of every move named by a token of the answer (mv, m, plan, pv)."""
    r = Resolver(pack, cfg.wording)
    moves: set[str] = set()
    for u in iter_units(output):
        for raw in find_tokens(u.text):
            try:
                res = r.resolve(raw)
            except ResolveError:
                continue
            if res.data in ("move", "plan", "pv"):
                moves |= {m.rstrip("+#") for m in SAN_RE.findall(res.text)}
    return moves


def final_output(raw: list[dict]) -> dict:
    """The last answer that passed the schema (the one the document comes from)."""
    from chessanalyst.llm.schema import AnalysisOutput

    for resp in reversed(raw):
        out, errs = extract_output(resp)
        if out is not None and not errs:
            try:
                return AnalysisOutput.model_validate(out).model_dump()
            except Exception:  # noqa: BLE001
                continue
    raise AssertionError("nessuna risposta valida")


def body(document: str) -> str:
    """The document without the technical report."""
    return document.split(f"## {REPORT_TITLE}")[0]
