"""Optional «critic» (§10.2, M4; O-7: the same model as the main call): a second call that looks for logical
inconsistencies between the sentences and the data and checks that each sentence matches its assertions.

The critic reads the text with the tokens already resolved (so it sees the numbers), the assertions of each
block and the reduced view of the pack. Each finding marks its block «⚠ non verificato», as V06 does; the
explanations stay in ``verification.json`` (free text of a model, never copied into the document). A failed
call is a warning, never an error of the analysis (OQ-M4-3).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chessanalyst.config import Config
from chessanalyst.errors import ModelError
from chessanalyst.llm.schema import _clean
from chessanalyst.pack.llm_view import llm_view_json
from chessanalyst.verify.resolve import ResolveError, Resolver
from chessanalyst.verify.tokens import TOKEN_RE

log = logging.getLogger(__name__)

CRITIC_TOOL = "submit_review"
CRITIC_SYSTEM = """Sei il revisore delle analisi di Chess Position Analyst. Ricevi un'analisi già scritta, con i numeri e
le mosse al loro posto, il pacchetto di dati da cui è stata scritta e, per ogni blocco, le asserzioni dichiarate.
Non riscrivi nulla: segnali soltanto, chiamando lo strumento submit_review.

Segnala un blocco quando:
- una frase contraddice i dati del pacchetto (per esempio chiama vantaggio una valutazione negativa per
  l'utente, dice «frequente» una mossa con probabilità bassa, consiglia una mossa diversa da recommendation.id,
  dà per sicuro un re che il radar dice critico);
- una frase contraddice un'altra frase dell'analisi;
- una frase non corrisponde alla sua asserzione (l'asserzione dice una cosa, la frase un'altra).

Le valutazioni sono sempre dal punto di vista dell'utente (positivo = meglio per lui), anche quando la frase
parla dell'avversario: non è un segno invertito. I numeri del testo vengono dal pacchetto e sono arrotondati.

Non segnalare lo stile, la lunghezza, le scelte di contenuto o la teoria scacchistica generale: solo incoerenze
verificabili con i dati. Elenca soltanto i blocchi con un'incoerenza: un blocco coerente non va elencato, e se
non trovi nulla consegna un elenco vuoto. Per ogni segnalazione indica la sezione, il numero del blocco e una
spiegazione breve."""


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Finding(_M):
    section: str = Field(pattern=r"^S(0[1-9]|1[0-3])$")
    block: int = Field(ge=1)
    kind: Literal["data", "internal", "assertion"]
    explanation: str


class Review(_M):
    findings: list[Finding]


def tool_definition() -> dict:
    return {"name": CRITIC_TOOL, "description": "Consegna le incoerenze trovate nell'analisi.",
            "input_schema": _clean(Review.model_json_schema())}


def _resolved(resolver: Resolver, text: str) -> str:
    def sub(m):
        try:
            return resolver.resolve(m.group(0)).text
        except ResolveError:
            return m.group(0)
    return TOKEN_RE.sub(sub, text)


def _block_texts(blk: dict) -> list[tuple[str, list[dict]]]:
    t = blk["type"]
    if t == "p":
        return [(blk["text"], blk.get("assertions") or [])]
    if t in ("ul", "ol"):
        return [(it["text"], it.get("assertions") or []) for it in blk["items"]]
    if t == "line":
        c = blk.get("caption")
        return [(c["text"], c.get("assertions") or [])] if c else []
    if t == "table":
        return [(c["text"], c.get("assertions") or []) for cols in (blk.get("text_cells") or {}).values()
                for c in cols.values()]
    if t == "text_table":
        return [(c["text"], c.get("assertions") or []) for row in blk["rows"] for c in row]
    return []


def critic_message(cfg: Config, pack: dict, output: dict) -> str:
    resolver = Resolver(pack, cfg.wording)
    lines = []
    for sec in output["sections"]:
        for b, blk in enumerate(sec["blocks"], 1):
            for text, asserts in _block_texts(blk):
                a = f" · asserzioni: {json.dumps(asserts, ensure_ascii=False)}" if asserts else ""
                lines.append(f"{sec['id']} · blocco {b}: {_resolved(resolver, text)}{a}")
    return "\n".join(["<pacchetto>", llm_view_json(pack, cfg.default.llm.view), "</pacchetto>", "",
                      "<analisi>", *lines, "</analisi>", "", "Chiama submit_review."])


@dataclass
class CriticResult:
    findings: list[dict] = field(default_factory=list)
    marked: list[str] = field(default_factory=list)
    error: str | None = None
    raw: dict | None = None


def mark(output: dict, findings: list[Finding]) -> tuple[dict, list[str]]:
    """Every text of a flagged block gets the «⚠ non verificato» mark."""
    out = json.loads(json.dumps(output))
    secs = {s["id"]: s for s in out["sections"]}
    marked = []
    for f in findings:
        sec = secs.get(f.section)
        if sec is None or f.block > len(sec["blocks"]):
            continue
        blk = sec["blocks"][f.block - 1]
        t = blk["type"]
        if t == "p":
            blk["_unverified"] = True
        elif t in ("ul", "ol"):
            for it in blk["items"]:
                it["_unverified"] = True
        elif t == "line" and blk.get("caption"):
            blk["caption"]["_unverified"] = True
        elif t == "table":
            for cols in (blk.get("text_cells") or {}).values():
                for c in cols.values():
                    c["_unverified"] = True
        elif t == "text_table":
            for row in blk["rows"]:
                for c in row:
                    c["_unverified"] = True
        else:
            continue
        label = f"{f.section} · blocco {f.block} (critico)"
        if label not in marked:
            marked.append(label)
    return out, marked


def run_critic(cfg: Config, pack: dict, output: dict, client: Any) -> tuple[dict, CriticResult]:
    """The output with the flagged blocks marked, and the outcome. Never raises for a model failure."""
    res = CriticResult()
    try:
        response = client.create(system=[{"type": "text", "text": CRITIC_SYSTEM}],
                                 messages=[{"role": "user", "content": critic_message(cfg, pack, output)}],
                                 tools=[tool_definition()], tool_choice={"type": "tool", "name": CRITIC_TOOL},
                                 max_tokens=cfg.default.llm.max_tokens)
    except ModelError as e:
        log.warning("Critico non disponibile: %s", e)
        res.error = str(e)
        return output, res
    res.raw = response
    block = next((b for b in response.get("content", [])
                  if b.get("type") == "tool_use" and b.get("name") == CRITIC_TOOL), None)
    try:
        review = Review.model_validate(block["input"] if block else None)
    except (ValidationError, TypeError) as e:
        log.warning("Risposta del critico non valida: %s", e)
        res.error = "risposta del critico non valida"
        return output, res
    output, res.marked = mark(output, review.findings)
    res.findings = [f.model_dump() for f in review.findings]
    log.info("Critico: %d segnalazioni", len(res.findings))
    return output, res
