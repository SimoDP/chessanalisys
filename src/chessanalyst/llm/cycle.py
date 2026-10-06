"""Model call, verification retries and degraded mode (§9.1, §9.3, §10.2).

After every response V01–V10 run. With errors and retries left (``llm.max_retries``;
at most one retry when the only errors are V07(d)) the response is appended as
it was received and the errors are sent back in a ``tool_result`` with
``is_error: true`` (E.3). After the last retry the degraded mode is applied to
the last response that passed V01; if none did: exit code 5.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field

from chessanalyst.config import Config
from chessanalyst.errors import ModelError
from chessanalyst.llm.client import LLMClient
from chessanalyst.llm.fewshot import Example, example_for
from chessanalyst.llm.usage import usage_summary
from chessanalyst.llm.prompt import SYSTEM_PROMPT, build_user_blocks, retry_message
from chessanalyst.llm.prompt_kp import SYSTEM_PROMPT_KP, build_user_message_kp, prune_assertions
from chessanalyst.llm.schema import TOOL_NAME, tool_definition
from chessanalyst.plan.outline import DOCUMENT, outline_pack
from chessanalyst.render.markdown import RenderInfo, render_markdown
from chessanalyst.verify.checker import Checker, Result, error_lines
from chessanalyst.verify.degrade import Degraded, degrade
from chessanalyst.verify.report import check_outcomes, verification_json
from chessanalyst.verify.trim import trim_response
from chessanalyst.verify.wordcount import tolerance

log = logging.getLogger(__name__)


@dataclass
class CycleResult:
    document: str
    verification: dict
    raw: list[dict] = field(default_factory=list)
    retries: int = 0
    degraded: bool = False
    output: dict | None = None         # M6: final output and render information, for the HTML page and exports
    info: RenderInfo | None = None


def _only_word_budget(res: Result) -> bool:
    return bool(res.errors) and all(e.code == "V07" and e.sub == "d" for e in res.errors)


def _counts(errors, skip=lambda e: False) -> Counter:
    """Errors by code and section (a cut changes the text of V08, never adds a claim)."""
    return Counter((e.code, e.sub, e.section) for e in errors if not skip(e))


def _trimmed(cfg: Config, checker: Checker, response: dict, res: Result, loop: _Loop) -> Result:
    """D-74: the sections over the budget lose their last sentences; the cut response is kept only
    if it adds no error."""
    over = {e.section for e in res.errors if e.code == "V07" and e.sub == "d" and e.section
            and res.words_by_section.get(e.section, {}).get("actual", 0)
            > (res.words_by_section[e.section]["budget"] or 0)}
    if not over:
        return res
    plan = {s["id"]: s for s in checker.pack["section_plan"]}
    tol = cfg.verify["word_tolerance"]
    cut = trim_response(response, plan, over, checker.word_re, lambda b: tolerance(b, tol))
    if cut is None:
        return res
    new = checker.check(cut)
    allowed = _counts(res.errors, lambda e: e.code == "V07" and e.sub == "d" and e.section in over)
    if new.output is None or _counts(new.errors) - allowed:
        return res
    loop.trimmed += sorted(over)
    log.info("Sezioni accorciate dal codice: %s", ", ".join(sorted(over)))
    return new


def _retry_turn(response: dict, text: str) -> list[dict]:
    """The response as received, then the errors (tool_result with is_error, E.3)."""
    content = response.get("content", [])
    turns = [{"role": "assistant", "content": content}] if content else []
    tool_use = next((b for b in content if b.get("type") == "tool_use"), None)
    if tool_use is not None:
        turns.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use["id"],
                                                    "is_error": True, "content": text}]})
    else:
        turns.append({"role": "user", "content": text})
    return turns


@dataclass
class _Loop:
    attempts: list[Result] = field(default_factory=list)
    retries: int = 0
    json_repairs: int = 0
    pruned: int = 0
    trimmed: list[str] = field(default_factory=list)   # D-74: sections cut to budget by the code


def _call_loop(cfg: Config, client: LLMClient, checker: Checker, system: list[dict], messages: list[dict],
               raw: list[dict], hints: dict, prune: bool = False, trim: bool = False) -> _Loop:
    """One call, then the verification retries (E.3)."""
    llm = cfg.default.llm
    tools = [tool_definition()]
    tool_choice = {"type": "tool", "name": TOOL_NAME}
    loop = _Loop()
    budget_retries = 0
    while True:
        log.info("Chiamata al modello %s (tentativo %d)", client.model, len(loop.attempts) + 1)
        response = client.create(system=system, messages=messages, tools=tools, tool_choice=tool_choice,
                                 max_tokens=llm.max_tokens)
        raw.append(response)
        fixed = sum(b.get("repaired", 0) for b in response.get("content", []))
        if fixed:                       # D-70: tool arguments closed too early, repaired by the client
            loop.json_repairs += fixed
            log.warning("JSON della risposta riparato (%d chiusure anticipate)", fixed)
        if prune:                       # D-72: feature assertions on facts that are not features
            loop.pruned += prune_assertions(checker.pack, response)
        res = checker.check(response)
        if trim:
            res = _trimmed(cfg, checker, response, res, loop)
        loop.attempts.append(res)
        log.info("Verifica: %s", ", ".join(error_lines(res.errors, {})) or "nessun errore")
        if not res.errors:
            return loop
        only_d = _only_word_budget(res)
        if loop.retries >= llm.max_retries or (only_d and budget_retries >= 1):
            return loop
        loop.retries += 1
        budget_retries += only_d
        messages = messages + _retry_turn(response, retry_message(error_lines(res.errors, hints)))


def run_model(cfg: Config, pack: dict, client: LLMClient, *, example: Example | None = None,
              warnings: list[str] | None = None, raw: list[dict] | None = None) -> CycleResult:
    """``raw`` collects every response as it arrives (saved in ``llm_raw.json`` even on failure).
    With ``llm.document: keypoints`` (D-72) the pack is first turned into the document of the key points."""
    llm = cfg.default.llm
    hints = cfg.wording["verify_hints"]
    raw = [] if raw is None else raw
    keypoints = llm.document == DOCUMENT
    if keypoints:
        pack = outline_pack(cfg, pack)
        example = example or Example(anchor=pack["user"]["anchor"], output_json="", epd="", validated=False)
        system = [{"type": "text", "text": SYSTEM_PROMPT_KP, "cache_control": {"type": "ephemeral"}}]
        messages = [{"role": "user", "content": [{"type": "text", "text": build_user_message_kp(cfg, pack),
                                                  "cache_control": {"type": "ephemeral"}}]}]
        checker = Checker(cfg, pack, words_floor=cfg.thresholds.keypoints.words_floor)
        loop = _call_loop(cfg, client, checker, system, messages, raw, hints, prune=True, trim=True)
    else:
        example = example or example_for(cfg, pack)
        checker = Checker(cfg, pack, fewshot_epd=example.epd, terms=example.terms)
        system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
        # M6: two cache breakpoints, the example (shared by every pack of the anchor) and the whole first
        # message (re-read by every retry); clients without cache_control receive the same text as one string
        ephemeral = {"type": "ephemeral"}
        messages: list[dict] = [{"role": "user", "content": [
            {"type": "text", "text": part, "cache_control": ephemeral}
            for part in build_user_blocks(cfg, pack, example)]}]
        loop = _call_loop(cfg, client, checker, system, messages, raw, hints)
    attempts, retries, json_repairs = loop.attempts, loop.retries, loop.json_repairs

    final = next((r for r in reversed(attempts) if r.output is not None), None)
    if final is None:
        raise ModelError("Nessuna risposta valida del modello dopo i retry")
    degraded: Degraded | None = None
    output = final.output
    if final.errors:
        degraded = degrade(pack, final.output, final.errors, llm.on_fail)
        output = degraded.output
        log.warning("Modalità degradata: rimossi %s, marcati %s", degraded.removed, degraded.marked)
    critic = None
    if llm.critic:                      # M4, optional (§10.2): marks, never removes
        from chessanalyst.llm.critic import run_critic

        output, critic = run_critic(cfg, pack, output, client)
        if critic.raw is not None:
            raw.append(critic.raw)
    info = RenderInfo(llm_model=client.model, references_validated=example.validated, retries=retries,
                      checks=check_outcomes(final, degraded),
                      removed=degraded.removed if degraded else [],
                      marked=(degraded.marked if degraded else []) + (critic.marked if critic else []),
                      critic=None if critic is None else (None if critic.error else len(critic.findings)),
                      usage=usage_summary(cfg, raw, client.model),
                      warnings=(degraded.warnings if degraded else []) + list(warnings or []),
                      theory_blocks=len(final.theory_blocks), theory_share=final.theory_share,
                      document=llm.document)
    document = render_markdown(cfg, pack, output, info)
    vj = verification_json(attempts, degraded, hints, final)
    vj["usage"] = info.usage
    vj["json_repairs"] = json_repairs
    if keypoints:
        vj["pruned_assertions"] = loop.pruned
        vj["trimmed_sections"] = loop.trimmed
    if critic is not None:
        vj["critic"] = {"findings": critic.findings, "marked": critic.marked, "error": critic.error}
    return CycleResult(document, vj, raw, retries, degraded is not None, output, info)
