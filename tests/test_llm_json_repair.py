"""D-70: tool arguments closed after the first section (real DeepSeek responses served by one OpenRouter
provider, ``fixtures/recorded/llm/deepseek_premature_close.json``) are repaired; anything else stays V01."""

from __future__ import annotations

import json

import pytest

from chessanalyst.llm.client import from_openai, parse_arguments
from chessanalyst.verify.checker import extract_output

FIXTURE = "fixtures/recorded/llm/deepseek_premature_close.json"


def test_real_responses_are_repaired(root):
    for data in json.loads((root / FIXTURE).read_text(encoding="utf-8")):
        raw = data["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)
        msg = from_openai(data)
        [block] = msg["content"]
        out = block["input"]
        assert isinstance(out, dict) and block["repaired"] == 1
        assert [s["id"] for s in out["sections"]][0] == "S01" and set(out) == {"schema_version", "sections", "notes"}
        assert extract_output(msg)[1] == []
    long = from_openai(json.loads((root / FIXTURE).read_text(encoding="utf-8"))[1])["content"][0]["input"]
    assert [s["id"] for s in long["sections"]] == ["S01", "S02", "S05", "S06", "S07", "S09", "S10", "S13"]


@pytest.mark.parametrize("text,repairs,ok", [
    ('{"a": 1}', 0, True),
    ('{"s": [{"id": "S01", "b": []}]}, {"id": "S02", "b": []}], "n": []}', 1, True),
    ('{"s": [{"id": "S01"}]}, {"id": "S02"}]}, {"id": "S03"}], "n": []}', 2, True),     # closed twice
    ('{"s": [1, 2}', 0, False),                    # other errors are not guessed
    ('{"a": 1} trailing', 0, False),               # extra data not after "]}"
    ('[1, 2]', 0, False),                          # not an object
])
def test_parse_arguments(text, repairs, ok):
    out, n = parse_arguments(text)
    assert (out is not None) == ok and n == repairs


def test_constant_keys_are_filled():
    out, errs = extract_output({"stop_reason": "tool_use", "content": [
        {"type": "tool_use", "name": "submit_analysis", "input": {"sections": []}}]})
    assert errs == [] and out == {"sections": [], "schema_version": "1", "notes": []}
