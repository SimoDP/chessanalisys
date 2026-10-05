"""Token usage and cost of the model calls of one analysis (M6, cost optimisation).

OpenRouter returns the cost of every call (``usage.cost``, USD) and the cached input tokens; the Anthropic API
returns only tokens, and the cost is computed only if ``llm.prices`` has the model (no invented prices).
"""

from __future__ import annotations

from typing import Any

from chessanalyst.config import Config

PRICE_UNIT_TOKENS = 1_000_000          # llm.prices are per million tokens (unit of the configuration)


def _call(u: dict[str, Any]) -> tuple[int, int, int, float | None]:
    """(input, cached input, output, cost or None) of one response's ``usage``."""
    if "prompt_tokens" in u:                                   # OpenRouter (chat completions)
        cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
        return u.get("prompt_tokens") or 0, cached, u.get("completion_tokens") or 0, u.get("cost")
    cached = (u.get("cache_read_input_tokens") or 0)           # Anthropic Messages
    inp = (u.get("input_tokens") or 0) + cached + (u.get("cache_creation_input_tokens") or 0)
    return inp, cached, u.get("output_tokens") or 0, None


def usage_summary(cfg: Config, responses: list[dict], model: str | None = None) -> dict[str, Any]:
    calls = inp = cached = out = 0
    cost: float | None = 0.0
    price = cfg.default.llm.prices.get(model or cfg.default.llm.model)
    for r in responses:
        u = r.get("usage")
        if not u:
            continue
        calls += 1
        i, c, o, k = _call(u)
        inp, cached, out = inp + i, cached + c, out + o
        if k is None and price is not None:
            k = ((i - c) * price.input + c * price.cached_input + o * price.output) / PRICE_UNIT_TOKENS
        cost = None if (cost is None or k is None) else cost + k
    return {"calls": calls, "input_tokens": inp, "cached_tokens": cached, "output_tokens": out,
            "cost_usd": None if cost is None or calls == 0 else round(cost, 6)}
