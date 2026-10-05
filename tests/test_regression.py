"""Prompt regression (§12.2, M5): summary per pack and comparison with the previous one."""

from __future__ import annotations

import json

from chessanalyst.llm.client import FakeLLM
from chessanalyst.llm.regression import compare, run_regression, summarize, write_regression
from tests.llm.test_record_llm import real_fixture


def test_regression_on_recorded_responses(cfg, tmp_path, monkeypatch):
    responses = []
    for name in cfg.calibration["regression"]["packs"]:
        responses += json.loads(real_fixture(name).read_text(encoding="utf-8"))["responses"]
    summary = run_regression(cfg, FakeLLM(responses, model="deepseek"), progress=lambda s: None, runs=1)
    packs = {p["pack"]: p for p in summary["packs"]}
    assert list(packs) == cfg.calibration["regression"]["packs"]
    assert all(p["n"] == 1 and len(p["runs"][0]["attempts"]) <= 3 for p in packs.values())
    assert packs["najdorf_w_1500"]["complete"] == 1 and packs["najdorf_w_1500"]["removed"] == 0
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    pcfg = cfg.model_copy(update={"project_root": root})
    j1, m1 = write_regression(pcfg, summary)
    assert "primo riferimento" in m1.read_text(encoding="utf-8")
    later = dict(summary, created_utc="2099-01-01T00:00:00+00:00")
    j2, m2 = write_regression(pcfg, later)
    text = m2.read_text(encoding="utf-8")
    assert f"confronto con il {summary['created_utc']}" in text and "| najdorf_w_1500 | complete 1/1" in text


def test_failed_pack_is_reported(cfg):
    from chessanalyst.llm.regression import aggregate

    s = aggregate("x", [summarize("x", None, 0, "nessuna risposta")] * 2)
    new = {"created_utc": "t", "model": "m", "config_hash": "h", "packs": [s]}
    assert "nessuna risposta valida in 2 giri" in compare(new, None)


def test_mean_cost_in_totals():
    from chessanalyst.llm.regression import aggregate

    run = {"pack": "x", "attempts": [{}], "retries": 0, "complete": True, "removed": 0, "marked": 0,
           "sections_off_budget": 0, "theory_share": 0, "usage": {"cost_usd": 0.02, "output_tokens": 100}}
    s = aggregate("x", [run, dict(run, usage={"cost_usd": 0.04}), summarize("x", None, 0, "errore")])
    text = compare({"created_utc": "t", "model": "m", "config_hash": "h", "packs": [s]}, None)
    assert "costo medio per analisi 0.0300 $ (2 analisi)" in text and "costo medio 0.0300 $" in text
