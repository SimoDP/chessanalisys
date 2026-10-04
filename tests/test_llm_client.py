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
