"""Model call, verification retries and degraded mode (§9.1, §9.3, §10.2).

After every response V01–V10 run. With errors and retries left (``llm.max_retries``;
at most one retry when the only errors are V07(d)) the response is appended as
it was received and the errors are sent back in a ``tool_result`` with
``is_error: true`` (E.3). After the last retry the degraded mode is applied to
the last response that passed V01; if none did: exit code 5.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from chessanalyst.config import Config
from chessanalyst.errors import ModelError
from chessanalyst.llm.client import LLMClient
from chessanalyst.llm.fewshot import Example, example_for
from chessanalyst.llm.usage import usage_summary
from chessanalyst.llm.prompt import SYSTEM_PROMPT, build_user_blocks, retry_message
from chessanalyst.llm.prompt_kp import SYSTEM_PROMPT_KP, build_user_message_kp
from chessanalyst.llm.schema import TOOL_NAME, tool_definition
from chessanalyst.plan.outline import DOCUMENT, outline_pack
from chessanalyst.render.markdown import RenderInfo, render_markdown
from chessanalyst.verify.checker import Checker, Result, error_lines
from chessanalyst.verify.degrade import Degraded, degrade
from chessanalyst.verify.report import check_outcomes, verification_json

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


def _call_loop(cfg: Config, client: LLMClient, checker: Checker, system: list[dict], messages: list[dict],
               raw: list[dict], hints: dict) -> _Loop:
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
        res = checker.check(response)
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


def _only_section(pack: dict, sid: str) -> dict:
    """The pack whose plan asks for one section only (D-72, one call per section)."""
    plan = [s if s["id"] == sid else dict(s, required=False, omitted=s.get("omitted") or "keypoints")
            for s in pack["section_plan"]]
    return dict(pack, section_plan=plan)


def _per_section(cfg: Config, pack: dict, client: LLMClient, raw: list[dict], hints: dict) -> _Loop:
    """D-72: one short call per section, in parallel; the sections are joined and verified together."""
    ids = [kp["section"] for kp in pack["key_points"]]

    def one(sid: str) -> tuple[_Loop, list[dict]]:
        sub_raw: list[dict] = []
        sub = _only_section(pack, sid)
        system = [{"type": "text", "text": SYSTEM_PROMPT_KP, "cache_control": {"type": "ephemeral"}}]
        messages = [{"role": "user", "content": build_user_message_kp(cfg, pack, [sid])}]
        return _call_loop(cfg, client, Checker(cfg, sub), system, messages, sub_raw, hints), sub_raw

    with ThreadPoolExecutor(max_workers=cfg.default.llm.max_parallel) as pool:
        done = list(pool.map(one, ids))
    sections, merged = [], _Loop()
    for sid, (loop, sub_raw) in zip(ids, done):
        raw += sub_raw
        merged.retries += loop.retries
        merged.json_repairs += loop.json_repairs
        final = next((r for r in reversed(loop.attempts) if r.output is not None), None)
        if final is not None:
            sections += [s for s in final.output["sections"] if s["id"] == sid]
    if sections:
        merged.attempts.append(Checker(cfg, pack).check({"schema_version": "1", "sections": sections,
                                                         "notes": []}))
    return merged


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
        if llm.calls == "per_section":
            loop = _per_section(cfg, pack, client, raw, hints)
        else:
            system = [{"type": "text", "text": SYSTEM_PROMPT_KP, "cache_control": {"type": "ephemeral"}}]
            messages = [{"role": "user", "content": [{"type": "text", "text": build_user_message_kp(cfg, pack),
                                                      "cache_control": {"type": "ephemeral"}}]}]
            loop = _call_loop(cfg, client, Checker(cfg, pack), system, messages, raw, hints)
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
    if critic is not None:
        vj["critic"] = {"findings": critic.findings, "marked": critic.marked, "error": critic.error}
    return CycleResult(document, vj, raw, retries, degraded is not None, output, info)
