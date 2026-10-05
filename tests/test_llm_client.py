"""Network policy of the model client (§9.3, D-61) with a fake SDK: no network."""

from __future__ import annotations

import anthropic
import httpx2
import pytest

from chessanalyst.errors import EnvironmentProblem, ModelError
from chessanalyst.llm.client import AnthropicClient

REQ = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status(code: int, msg: str = "errore", headers=None):
    resp = httpx2.Response(code, request=REQ, headers=headers or {})
    cls = {400: anthropic.BadRequestError, 401: anthropic.AuthenticationError, 403: anthropic.PermissionDeniedError,
           429: anthropic.RateLimitError, 529: anthropic.OverloadedError}.get(code, anthropic.InternalServerError)
    return cls(msg, response=resp, body=None)


class Msg:
    def __init__(self, data):
        self.data = data

    def model_dump(self, **kw):
        return self.data


class FakeSDK:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        o = self.outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return Msg(o)


OK = {"stop_reason": "tool_use", "content": []}
ARGS = dict(system=[], messages=[], tools=[], tool_choice={"type": "tool", "name": "submit_analysis"}, max_tokens=10)


def client(cfg, outcomes):
    waits = []
    sdk = FakeSDK(outcomes)
    return AnthropicClient(cfg, sleep=waits.append, sdk_client=sdk), sdk, waits


@pytest.mark.parametrize("err", [status(429), status(500), status(502), status(503), status(504), status(529),
                                 anthropic.APIConnectionError(request=REQ)])
def test_retryable_then_ok(cfg, err):
    c, sdk, waits = client(cfg, [err, err, OK])
    assert c.create(**ARGS) == OK
    assert len(sdk.calls) == 3 and waits == cfg.default.llm.network_backoff_s[:2]


def test_retry_after_is_added(cfg):
    c, _, waits = client(cfg, [status(429, headers={"retry-after": "3"}), OK])
    c.create(**ARGS)
    assert waits == [cfg.default.llm.network_backoff_s[0] + 3]


def test_gives_up_after_the_attempts(cfg):
    c, sdk, _ = client(cfg, [status(503)] * 5)
    with pytest.raises(ModelError) as e:
        c.create(**ARGS)
    assert e.value.exit_code == 5 and len(sdk.calls) == cfg.default.llm.network_attempts


@pytest.mark.parametrize("code", [401, 403])
def test_auth_errors_stop_at_once(cfg, code):
    c, sdk, _ = client(cfg, [status(code), OK])
    with pytest.raises(ModelError, match="Chiave API non valida o non autorizzata"):
        c.create(**ARGS)
    assert len(sdk.calls) == 1


def test_bad_request_stops_at_once(cfg):
    c, sdk, _ = client(cfg, [status(400, "invalid schema"), OK])
    with pytest.raises(ModelError):
        c.create(**ARGS)
    assert len(sdk.calls) == 1


def test_temperature_rejected_once(cfg, caplog):
    c, sdk, _ = client(cfg, [status(400, "temperature is not supported for this model"), OK, OK])
    assert c.create(**ARGS) == OK
    assert sdk.calls[0]["extra_body"] == {"temperature": cfg.default.llm.temperature}
    assert "extra_body" not in sdk.calls[1]
    c.create(**ARGS)
    assert "extra_body" not in sdk.calls[2]                 # not tried again
    assert "temperature" in caplog.text


def test_request_parameters(cfg):
    c, sdk, _ = client(cfg, [OK])
    c.create(**ARGS)
    kw = sdk.calls[0]
    assert kw["model"] == cfg.default.llm.model and kw["tool_choice"] == {"type": "tool", "name": "submit_analysis"}
    assert "thinking" not in kw


def test_missing_key_is_environment_error(cfg, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(EnvironmentProblem) as e:
        AnthropicClient(cfg)
    assert e.value.exit_code == 4


def test_sdk_client_without_internal_retries(cfg, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-a-real-key")
    c = AnthropicClient(cfg)
    assert c.sdk.max_retries == 0


# -- OpenRouter (D-64) --------------------------------------------------------------------

import json  # noqa: E402

from chessanalyst.llm.client import OpenRouterClient, from_openai, make_client, to_openai  # noqa: E402
from chessanalyst.llm.cycle import run_model  # noqa: E402

TOOL = {"name": "submit_analysis", "description": "d", "input_schema": {"type": "object"}}


def or_ok(args: dict | str, finish="tool_calls"):
    arguments = args if isinstance(args, str) else json.dumps(args)
    return {"id": "gen-1", "model": "anthropic/claude-sonnet-5.5", "choices": [{"finish_reason": finish, "message": {
        "role": "assistant", "content": None,
        "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "submit_analysis",
                                                                         "arguments": arguments}}]}}]}


class FakeTransport:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": json.loads(body), "timeout": timeout})
        o = self.outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        status, payload, *hdr = o
        return status, (hdr[0] if hdr else {}), json.dumps(payload).encode()


def or_client(cfg, outcomes):
    waits = []
    t = FakeTransport(outcomes)
    return OpenRouterClient(cfg, sleep=waits.append, transport=t, api_key="test-key"), t, waits


def test_openrouter_is_the_default(cfg, monkeypatch):
    assert cfg.default.llm.provider == "openrouter" and cfg.default.llm.model == "deepseek/deepseek-v4.1-flash"
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(EnvironmentProblem, match="OPENROUTER_API_KEY"):
        make_client(cfg)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    assert isinstance(make_client(cfg), OpenRouterClient)


def test_request_conversion(cfg):
    c, t, _ = or_client(cfg, [(200, or_ok({"schema_version": "1"}))])
    system = [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}]
    messages = [{"role": "user", "content": "MSG"},
                {"role": "assistant", "content": [{"type": "tool_use", "id": "call_0", "name": "submit_analysis",
                                                   "input": {"a": 1}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_0", "is_error": True,
                                              "content": "ERRORI"}]}]
    out = c.create(system=system, messages=messages, tools=[TOOL],
                   tool_choice={"type": "tool", "name": "submit_analysis"}, max_tokens=99)
    call = t.calls[0]
    assert call["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    b = call["body"]
    assert b["model"] == cfg.default.llm.model and b["max_tokens"] == 99
    assert b["reasoning"] == {"enabled": False}
    assert b["temperature"] == cfg.default.llm.temperature
    assert b["messages"][0] == {"role": "system", "content": [{"type": "text", "text": "SYS"}]}   # not a Claude model
    assert b["messages"][1] == {"role": "user", "content": "MSG"}
    assert b["messages"][2]["tool_calls"][0]["function"] == {"name": "submit_analysis", "arguments": '{"a": 1}'}
    assert b["messages"][3] == {"role": "tool", "tool_call_id": "call_0", "content": "ERRORI"}
    assert b["tools"] == [{"type": "function", "function": {"name": "submit_analysis", "description": "d",
                                                             "parameters": {"type": "object"}}}]
    assert b["tool_choice"] == {"type": "function", "function": {"name": "submit_analysis"}}
    assert out["stop_reason"] == "tool_use"
    assert out["content"] == [{"type": "tool_use", "id": "call_1", "name": "submit_analysis",
                               "input": {"schema_version": "1"}}]


def test_response_conversion():
    assert from_openai(or_ok({}, finish="length"))["stop_reason"] == "max_tokens"
    bad = from_openai(or_ok("{non json"))
    assert bad["content"][0]["input"] is None


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_openrouter_retryable(cfg, code):
    c, t, waits = or_client(cfg, [(code, {"error": {"code": code, "message": "x"}}), (200, or_ok({}))])
    assert c.create(system=[], messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert len(t.calls) == 2 and waits == [cfg.default.llm.network_backoff_s[0]]


def test_openrouter_connection_error_and_give_up(cfg):
    c, t, _ = or_client(cfg, [OSError("reset")] * 5)
    with pytest.raises(ModelError) as e:
        c.create(system=[], messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert e.value.exit_code == 5 and len(t.calls) == cfg.default.llm.network_attempts


@pytest.mark.parametrize("code,msg", [(401, "Chiave API non valida"), (403, "Chiave API non valida"),
                                      (402, "Credito insufficiente"), (400, "rifiutata")])
def test_openrouter_fatal(cfg, code, msg):
    c, t, _ = or_client(cfg, [(code, {"error": {"code": code, "message": "no"}}), (200, or_ok({}))])
    with pytest.raises(ModelError, match=msg):
        c.create(system=[], messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert len(t.calls) == 1


def test_openrouter_error_inside_200(cfg):
    c, t, _ = or_client(cfg, [(200, {"error": {"code": 502, "message": "upstream"}}), (200, or_ok({}))])
    c.create(system=[], messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert len(t.calls) == 2


def test_openrouter_temperature_rejected(cfg):
    c, t, _ = or_client(cfg, [(400, {"error": {"code": 400, "message": "temperature not supported"}}),
                              (200, or_ok({}))])
    c.create(system=[], messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert "temperature" in t.calls[0]["body"] and "temperature" not in t.calls[1]["body"]


def test_full_cycle_through_openrouter(cfg):
    """Retry round-trip in the OpenAI format: the defective answer comes back as a tool message."""
    from chessanalyst.golden.packs import load_frozen_pack
    from tests.llm_helpers import recorded

    bad = recorded("bad_chain.json")["content"][0]["input"]
    good = recorded("good_najdorf_1900.json")["content"][0]["input"]
    c, t, _ = or_client(cfg, [(200, or_ok(bad)), (200, or_ok(good))])
    res = run_model(cfg, load_frozen_pack(cfg, "najdorf_w_1900"), c)
    assert res.retries == 1 and not res.degraded
    second = t.calls[1]["body"]["messages"]
    assert [m["role"] for m in second] == ["system", "user", "assistant", "tool"]
    assert second[3]["content"].startswith("La consegna contiene errori")
    assert f"modello di linguaggio: {cfg.default.llm.model}" in res.document


def test_cache_control_kept_for_claude_models(cfg):
    llm = cfg.default.llm.model_copy(update={"model": "anthropic/claude-sonnet-5.5"})
    claude = cfg.model_copy(update={"default": cfg.default.model_copy(update={"llm": llm})})
    c, t, _ = or_client(claude, [(200, or_ok({}))])
    system = [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}]
    c.create(system=system, messages=[], tools=[TOOL], tool_choice={"name": "submit_analysis"}, max_tokens=1)
    assert t.calls[0]["body"]["messages"][0] == {"role": "system", "content": system}


def test_cache_breakpoints_on_the_first_message(cfg):
    """M6 (cost): the first user message has two parts with cache_control (example, then pack); a model
    without cache_control receives exactly the text of Appendix E.2 as one string."""
    from chessanalyst.golden.packs import load_frozen_pack
    from chessanalyst.llm.client import to_openai
    from chessanalyst.llm.fewshot import example_for
    from chessanalyst.llm.prompt import build_user_blocks, build_user_message

    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    ex = example_for(cfg, pack)
    a, b = build_user_blocks(cfg, pack, ex)
    assert a.startswith("<esempio") and a.endswith("</esempio>") and "<pacchetto>" in b
    eph = {"type": "ephemeral"}
    request = {"system": [{"type": "text", "text": "s", "cache_control": eph}],
               "messages": [{"role": "user", "content": [{"type": "text", "text": a, "cache_control": eph},
                                                         {"type": "text", "text": b, "cache_control": eph}]}],
               "tools": [{"name": "t", "description": "d", "input_schema": {}}],
               "tool_choice": {"type": "tool", "name": "t"}, "max_tokens": 10}
    plain = to_openai("deepseek/x", request, None, cache_control=False)
    assert plain["messages"][1] == {"role": "user", "content": build_user_message(cfg, pack, ex)}
    cached = to_openai("anthropic/x", request, None, cache_control=True)
    parts = cached["messages"][1]["content"]
    assert [p["text"] for p in parts] == [a, b] and all(p["cache_control"] == eph for p in parts)
