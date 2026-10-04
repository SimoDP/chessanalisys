"""Model call, verification retries and degraded mode (§9.1, §9.3, §10.2).

After every response V01–V10 run. With errors and retries left (``llm.max_retries``;
at most one retry when the only errors are V07(d)) the response is appended as
it was received and the errors are sent back in a ``tool_result`` with
``is_error: true`` (E.3). After the last retry the degraded mode is applied to
the last response that passed V01; if none did: exit code 5.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from chessanalyst.config import Config
from chessanalyst.errors import ModelError
from chessanalyst.llm.client import LLMClient
from chessanalyst.llm.fewshot import Example, example_for
from chessanalyst.llm.prompt import SYSTEM_PROMPT, build_user_message, retry_message
from chessanalyst.llm.schema import TOOL_NAME, tool_definition
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


def run_model(cfg: Config, pack: dict, client: LLMClient, *, example: Example | None = None,
              warnings: list[str] | None = None, raw: list[dict] | None = None) -> CycleResult:
    """``raw`` collects every response as it arrives (saved in ``llm_raw.json`` even on failure)."""
    llm = cfg.default.llm
    hints = cfg.wording["verify_hints"]
    example = example or example_for(cfg, pack)
    checker = Checker(cfg, pack, fewshot_epd=example.epd, terms=example.terms)
    system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
    messages: list[dict] = [{"role": "user", "content": build_user_message(cfg, pack, example)}]
    tools = [tool_definition()]
    tool_choice = {"type": "tool", "name": TOOL_NAME}

    raw = [] if raw is None else raw
    attempts: list[Result] = []
    retries = budget_retries = 0
    while True:
        log.info("Chiamata al modello %s (tentativo %d)", client.model, len(attempts) + 1)
        response = client.create(system=system, messages=messages, tools=tools, tool_choice=tool_choice,
                                 max_tokens=llm.max_tokens)
        raw.append(response)
        res = checker.check(response)
        attempts.append(res)
        log.info("Verifica: %s", ", ".join(error_lines(res.errors, {})) or "nessun errore")
        if not res.errors:
            break
        only_d = _only_word_budget(res)
        if retries >= llm.max_retries or (only_d and budget_retries >= 1):
            break
        retries += 1
        budget_retries += only_d
        messages += _retry_turn(response, retry_message(error_lines(res.errors, hints)))

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
                      warnings=(degraded.warnings if degraded else []) + list(warnings or []),
                      theory_blocks=len(final.theory_blocks), theory_share=final.theory_share)
    document = render_markdown(cfg, pack, output, info)
    vj = verification_json(attempts, degraded, hints, final)
    if critic is not None:
        vj["critic"] = {"findings": critic.findings, "marked": critic.marked, "error": critic.error}
    return CycleResult(document, vj, raw, retries, degraded is not None)
