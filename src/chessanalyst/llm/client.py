"""Model clients (§9.1, §9.3 network part, D-61, D-64).

``llm.provider`` chooses ``OpenRouterClient`` (default, chat completions in
OpenAI format, key in ``OPENROUTER_API_KEY``) or ``AnthropicClient`` (official
SDK with ``max_retries=0``, key in ``ANTHROPIC_API_KEY``). Both speak the
Messages format to the rest of the program and apply the same network policy:
on connection errors and 408/429/500/502/503/504/529 up to
``llm.network_attempts`` attempts, waiting ``llm.network_backoff_s`` (plus
``retry-after``); 400/401/402/403 stop at once. ``FakeLLM`` replays recorded
responses (tests, §12.1).

The key is read only from the environment and never written or logged.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

from chessanalyst.config import Config
from chessanalyst.errors import EnvironmentProblem, ModelError

log = logging.getLogger(__name__)

RETRYABLE_STATUS = (408, 429, 500, 502, 503, 504, 529)
API_KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY"}


class LLMClient(Protocol):
    model: str

    def create(self, *, system: list[dict], messages: list[dict], tools: list[dict], tool_choice: dict,
               max_tokens: int) -> dict:
        """One call. Requests and responses use the Messages format (``tool_use``/``tool_result``
        blocks); the response is a plain dict (``stop_reason``, ``content``, ...)."""


class _Transient(Exception):
    def __init__(self, what: str, wait: float = 0.0) -> None:
        super().__init__(what)
        self.wait = wait


class _TemperatureRejected(Exception):
    pass


def _fatal(status: int | None, detail: str) -> ModelError:
    if status in (401, 403):
        return ModelError("Chiave API non valida o non autorizzata")
    if status == 402:
        return ModelError("Credito insufficiente presso il fornitore del modello")
    return ModelError(f"Richiesta rifiutata dall'API ({status}): {detail}")


def _require_key(provider: str) -> str:
    key = os.environ.get(API_KEY_ENV[provider])
    if not key:
        raise EnvironmentProblem(f"Chiave API assente: imposta la variabile d'ambiente {API_KEY_ENV[provider]}")
    return key


class _RetryingClient:
    """Network policy shared by the providers (§9.3, D-61)."""

    def __init__(self, cfg: Config, sleep: Callable[[float], None]) -> None:
        llm = cfg.default.llm
        self.model = llm.model
        self.temperature = llm.temperature
        self.attempts = llm.network_attempts
        self.backoff = list(llm.network_backoff_s)
        self.sleep = sleep
        self.temperature_rejected = False
        for name in ("anthropic", "httpx", "httpx2", "httpcore", "urllib3"):   # no request dumps in run.log
            logging.getLogger(name).setLevel(logging.WARNING)

    def _attempt(self, request: dict, temperature: bool) -> dict:
        raise NotImplementedError

    def _once(self, request: dict) -> dict:
        try:
            return self._attempt(request, not self.temperature_rejected)
        except _TemperatureRejected:
            # §9.1: parameter rejected for this model → repeat once without it
            self.temperature_rejected = True
            log.warning("Il modello %s non accetta temperature: richiesta ripetuta senza", self.model)
            return self._attempt(request, False)

    def create(self, *, system: list[dict], messages: list[dict], tools: list[dict], tool_choice: dict,
               max_tokens: int) -> dict:
        request = {"system": system, "messages": messages, "tools": tools, "tool_choice": tool_choice,
                   "max_tokens": max_tokens}
        last = ""
        for attempt in range(1, self.attempts + 1):
            try:
                return self._once(request)
            except _Transient as e:
                last, wait = str(e), e.wait
            log.warning("API non raggiungibile (tentativo %d di %d): %s", attempt, self.attempts, last)
            if attempt < self.attempts:
                self.sleep(self.backoff[min(attempt - 1, len(self.backoff) - 1)] + wait)
        raise ModelError(f"API non raggiungibile dopo {self.attempts} tentativi ({last})")


def _retry_after(headers: Any) -> float:
    try:
        return float(headers.get("retry-after", 0) or 0)
    except (AttributeError, TypeError, ValueError):
        return 0.0


class AnthropicClient(_RetryingClient):
    """Official SDK (``anthropic``) with ``max_retries=0``."""

    def __init__(self, cfg: Config, sleep: Callable[[float], None] = time.sleep, sdk_client: Any = None) -> None:
        super().__init__(cfg, sleep)
        if sdk_client is None:
            import anthropic

            _require_key("anthropic")
            sdk_client = anthropic.Anthropic(max_retries=0, timeout=cfg.default.llm.anthropic.timeout_s)
        self.sdk = sdk_client

    def _attempt(self, request: dict, temperature: bool) -> dict:
        import anthropic

        extra = {"extra_body": {"temperature": self.temperature}} if temperature else {}
        try:
            return self.sdk.messages.create(model=self.model, **request, **extra).model_dump(mode="json",
                                                                                           exclude_none=True)
        except anthropic.BadRequestError as e:
            if temperature and "temperature" in str(e).lower():
                raise _TemperatureRejected() from None
            raise _fatal(400, str(e)) from None
        except anthropic.APIStatusError as e:
            if e.status_code in RETRYABLE_STATUS:
                raise _Transient(f"HTTP {e.status_code}", _retry_after(e.response.headers)) from None
            log.error("API: errore %s", e.status_code)
            raise _fatal(e.status_code, str(e)) from None
        except anthropic.APIConnectionError as e:          # includes timeouts
            raise _Transient(type(e).__name__) from None


# -- OpenRouter (D-64): chat completions, OpenAI format --------------------------------------

FINISH_TO_STOP = {"tool_calls": "tool_use", "length": "max_tokens", "stop": "end_turn",
                  "content_filter": "refusal", "error": "error"}

Transport = Callable[[str, dict, bytes, float], tuple[int, dict, bytes]]


def urllib_transport(url: str, headers: dict, body: bytes, timeout: float) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def to_openai(model: str, request: dict, temperature: float | None, cache_control: bool = True,
              extra: dict | None = None) -> dict:
    """Messages-format request → chat completions body (``cache_control`` kept only when the model supports it)."""
    system = [dict(b) if cache_control else {k: v for k, v in b.items() if k != "cache_control"}
              for b in request["system"]]
    msgs: list[dict] = [{"role": "system", "content": system}]
    for m in request["messages"]:
        content = m["content"]
        if isinstance(content, str):
            msgs.append({"role": m["role"], "content": content})
            continue
        if m["role"] == "assistant":
            text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
            calls = [{"id": b["id"], "type": "function",
                      "function": {"name": b["name"], "arguments": json.dumps(b.get("input"), ensure_ascii=False)}}
                     for b in content if b.get("type") == "tool_use"]
            msg: dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                msg["tool_calls"] = calls
            msgs.append(msg)
            continue
        texts = [b for b in content if b.get("type") == "text"]
        for b in content:
            if b.get("type") == "tool_result":
                msgs.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": b["content"]})
        if texts:   # one user message: parts with their breakpoints, or (no cache_control) the joined text
            msgs.append({"role": "user", "content": [dict(b) for b in texts] if cache_control
                         else "\n".join(b["text"] for b in texts)})
    body = {"model": model, "messages": msgs, "max_tokens": request["max_tokens"],
            "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                         "parameters": t["input_schema"]}} for t in request["tools"]],
            "tool_choice": {"type": "function", "function": {"name": request["tool_choice"]["name"]}}}
    if temperature is not None:
        body["temperature"] = temperature
    for k, v in (extra or {}).items():
        body.setdefault(k, v)
    return body


PREMATURE_CLOSE = "]}"


def parse_arguments(text: str) -> tuple[dict | None, int]:
    """The tool arguments and the number of repairs (D-70). A model seen in the logs (DeepSeek via some
    providers) closes ``sections`` and the root object after the first section and then goes on writing the
    other sections: ``…}]}]}, {"id": "S02", …``. Each time the decoder stops on «Extra data» right after a
    ``]}``, that ``]}`` is removed and the text is read again; anything else stays invalid (V01)."""
    repairs = 0
    while True:
        try:
            out = json.loads(text)
            return (out if isinstance(out, dict) else None), repairs
        except json.JSONDecodeError as e:
            head = text[:e.pos].rstrip()
            if e.msg != "Extra data" or not head.endswith(PREMATURE_CLOSE):
                return None, repairs
            text = head[: -len(PREMATURE_CLOSE)] + text[e.pos:]
            repairs += 1


def from_openai(data: dict) -> dict:
    """Chat completions response → Messages-format dict (the original is kept under ``provider_response``)."""
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content: list[dict] = []
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})
    for call in message.get("tool_calls") or []:
        fn = call.get("function", {})
        args, repaired = parse_arguments(fn.get("arguments") or "")      # invalid JSON → None → V01
        block = {"type": "tool_use", "id": call.get("id", ""), "name": fn.get("name"), "input": args}
        if repaired:
            block["repaired"] = repaired
        content.append(block)
    return {"stop_reason": FINISH_TO_STOP.get(choice.get("finish_reason"), choice.get("finish_reason")),
            "content": content, "model": data.get("model"), "usage": data.get("usage"), "provider_response": data}


class OpenRouterClient(_RetryingClient):
    """OpenRouter chat completions (``POST {base_url}/chat/completions``), standard library HTTP."""

    def __init__(self, cfg: Config, sleep: Callable[[float], None] = time.sleep, transport: Transport | None = None,
                 api_key: str | None = None) -> None:
        super().__init__(cfg, sleep)
        o = cfg.default.llm.openrouter
        self.url = o.base_url.rstrip("/") + "/chat/completions"
        self.timeout = o.timeout_s
        self.cache_control = any(self.model.startswith(p) for p in o.cache_control_prefixes)
        self.extra = dict(o.extra_body)
        if self.model in o.provider_by_model:            # the providers chosen for this model (phase D)
            self.extra["provider"] = {**self.extra.get("provider", {}), **o.provider_by_model[self.model]}
        self.transport = transport or urllib_transport
        self._key = api_key if api_key is not None else _require_key("openrouter")

    def _attempt(self, request: dict, temperature: bool) -> dict:
        body = to_openai(self.model, request, self.temperature if temperature else None, self.cache_control, self.extra)
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        try:
            status, resp_headers, raw = self.transport(self.url, headers, json.dumps(body).encode("utf-8"),
                                                       self.timeout)
        except (OSError, urllib.error.URLError, http.client.HTTPException) as e:   # connection errors, timeouts,
            # and a response cut off mid-body (IncompleteRead, seen on OpenRouter in phase D)
            raise _Transient(type(e).__name__) from None
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            data = {}
        err = data.get("error") if isinstance(data, dict) else None
        if status == 200 and not err:
            return from_openai(data)
        if status == 200 and err:            # error reported inside a 200 response
            status = int(err.get("code") or 502) if str(err.get("code", "")).isdigit() else 502
        detail = (err or {}).get("message", "") if isinstance(err, dict) else ""
        if status in RETRYABLE_STATUS:
            raise _Transient(f"HTTP {status}", _retry_after({k.lower(): v for k, v in resp_headers.items()}))
        if status == 400 and temperature and "temperature" in detail.lower():
            raise _TemperatureRejected()
        log.error("API: errore %s", status)
        raise _fatal(status, detail)


class FakeLLM:
    """Replays recorded responses (``fixtures/recorded/llm/*.json``) in order and keeps the requests."""

    def __init__(self, responses: Iterable[dict], model: str = "fake-llm") -> None:
        self.responses = list(responses)
        self.model = model
        self.requests: list[dict] = []

    @classmethod
    def from_files(cls, paths: Iterable[Path], model: str = "fake-llm") -> "FakeLLM":
        return cls([json.loads(Path(p).read_text(encoding="utf-8")) for p in paths], model)

    def create(self, *, system: list[dict], messages: list[dict], tools: list[dict], tool_choice: dict,
               max_tokens: int) -> dict:
        self.requests.append(json.loads(json.dumps({"system": system, "messages": messages, "tools": tools,
                                                    "tool_choice": tool_choice, "max_tokens": max_tokens})))
        if not self.responses:
            raise ModelError("FakeLLM: nessuna risposta registrata rimasta")
        return self.responses.pop(0)


def make_client(cfg: Config) -> LLMClient:
    """Client of the provider chosen in ``llm.provider`` (D-64: OpenRouter by default)."""
    if cfg.default.llm.provider == "anthropic":
        return AnthropicClient(cfg)
    return OpenRouterClient(cfg)
