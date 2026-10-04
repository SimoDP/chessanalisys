"""Model client (§9.1, §9.3 network part, D-61).

``AnthropicClient`` wraps the official SDK with ``max_retries=0`` and applies
the network policy itself: on connection errors and 429/500/502/503/504/529 up
to ``llm.network_attempts`` attempts, waiting ``llm.network_backoff_s`` (plus
``retry-after`` when present); 400/401/403 stop at once. ``FakeLLM`` replays
recorded responses (tests, §12.1).

The API key is read only from ``ANTHROPIC_API_KEY`` and never written or logged.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

from chessanalyst.config import Config
from chessanalyst.errors import EnvironmentProblem, ModelError

log = logging.getLogger(__name__)

RETRYABLE_STATUS = (429, 500, 502, 503, 504, 529)
API_KEY_ENV = "ANTHROPIC_API_KEY"


class LLMClient(Protocol):
    model: str

    def create(self, *, system: list[dict], messages: list[dict], tools: list[dict], tool_choice: dict,
               max_tokens: int) -> dict:
        """One call; returns the response as a plain dict (``stop_reason``, ``content``, ...)."""


def _retry_after(exc: Any) -> float:
    try:
        return float(exc.response.headers.get("retry-after", 0) or 0)
    except (AttributeError, TypeError, ValueError):
        return 0.0


class AnthropicClient:
    def __init__(self, cfg: Config, sleep: Callable[[float], None] = time.sleep, sdk_client: Any = None) -> None:
        llm = cfg.default.llm
        self.model = llm.model
        self.temperature = llm.temperature
        self.attempts = llm.network_attempts
        self.backoff = list(llm.network_backoff_s)
        self.sleep = sleep
        self.temperature_rejected = False
        if sdk_client is None:
            import anthropic

            if not os.environ.get(API_KEY_ENV):
                raise EnvironmentProblem(f"Chiave API assente: imposta la variabile d'ambiente {API_KEY_ENV}")
            sdk_client = anthropic.Anthropic(max_retries=0)      # the key is read by the SDK from the environment
        self.sdk = sdk_client
        for name in ("anthropic", "httpx", "httpx2", "httpcore"):   # no request dumps in run.log
            logging.getLogger(name).setLevel(logging.WARNING)

    def _call(self, kwargs: dict) -> Any:
        import anthropic

        extra = {} if self.temperature_rejected else {"extra_body": {"temperature": self.temperature}}
        try:
            return self.sdk.messages.create(**kwargs, **extra)
        except anthropic.BadRequestError as e:
            if extra and "temperature" in str(e).lower():
                # §9.1: parameter rejected for this model → repeat once without it
                self.temperature_rejected = True
                log.warning("Il modello %s non accetta temperature: richiesta ripetuta senza", self.model)
                return self.sdk.messages.create(**kwargs)
            raise

    def create(self, *, system: list[dict], messages: list[dict], tools: list[dict], tool_choice: dict,
               max_tokens: int) -> dict:
        import anthropic

        kwargs = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages,
                  "tools": tools, "tool_choice": tool_choice}
        last: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                return self._call(kwargs).model_dump(mode="json", exclude_none=True)
            except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
                log.error("API: %s (status %s)", type(e).__name__, getattr(e, "status_code", None))
                raise ModelError("Chiave API non valida o non autorizzata") from None
            except anthropic.BadRequestError as e:
                log.error("API: richiesta rifiutata (400): %s", e)
                raise ModelError(f"Richiesta rifiutata dall'API (400): {e}") from None
            except anthropic.APIStatusError as e:
                if e.status_code not in RETRYABLE_STATUS:
                    log.error("API: errore %s", e.status_code)
                    raise ModelError(f"Errore dell'API ({e.status_code})") from None
                last, wait = e, _retry_after(e)
            except anthropic.APIConnectionError as e:          # includes timeouts
                last, wait = e, 0.0
            log.warning("API non raggiungibile (tentativo %d di %d): %s", attempt, self.attempts, type(last).__name__)
            if attempt < self.attempts:
                self.sleep(self.backoff[min(attempt - 1, len(self.backoff) - 1)] + wait)
        raise ModelError(f"API non raggiungibile dopo {self.attempts} tentativi ({type(last).__name__})")


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
    return AnthropicClient(cfg)
