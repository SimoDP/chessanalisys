"""Bench (OQ-BENCH): position specs, scoring of one analysis, report and comparison. No engines, no network."""

from __future__ import annotations

import json

import chess
import pytest

from chessanalyst import bench
from chessanalyst.cli import main
from chessanalyst.llm.client import FakeLLM

CASE = "fixtures/user_cases/e4_wins_w_1700"


def _response(output: dict) -> dict:
    return {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "toolu_bench",
                                                    "name": "submit_analysis", "input": output}]}


def _node_board(pack: dict, node: str) -> chess.Board:
    return chess.Board(next(n["fen"] for n in pack["nodes"] if n["id"] == node))


def test_every_bench_position_has_a_valid_spec_and_pack(cfg):
    bc = bench.bench_cfg(cfg)
    assert len(bc["positions"]) == len(set(bc["positions"]))
    for name in bc["positions"]:
        spec = bench.load_spec(cfg, name)
        assert spec["id"] == name and name.isascii()
        pack = bench.load_pack(cfg, spec)
        idx = bench.move_index(pack)
        nodes = {n["id"] for n in pack["nodes"]}
        assert spec["verdict"]["bands"] and spec["must_not"], name
        assert 2 <= len(spec["must_say"]) <= 4, name
        if "fen" in spec:
            assert pack["position"]["fen"] == chess.Board(spec["fen"]).fen()     # en passant only if legal
            assert pack["user"]["color"] == spec["user"]["color"]
        for k in spec["must_say"]:
            assert k["text"] and k["all"], (name, k["id"])
            for t in [u for t in k["all"] for u in t.get("any", [t])]:
                assert len(t.keys() - {"node"}) == 1 and t.keys() & {"ref", "move", "text"}, (name, t)
                if "ref" in t and not t["ref"].startswith("diag:"):
                    assert t["ref"] in idx or t["ref"] in nodes, (name, t)
                if "move" in t and "node" in t:          # a legal move where it is played
                    _node_board(pack, t["node"]).parse_san(t["move"])


@pytest.fixture
def case(cfg, root):
    pack = json.loads((root / f"{CASE}.pack.json").read_text(encoding="utf-8"))
    out = json.loads((root / f"{CASE}.deepseek.json").read_text(encoding="utf-8"))
    return bench.load_spec(cfg, "e4_wins_w_1700"), pack, out


def test_key_points_need_all_terms_in_one_section(cfg, case):
    spec, pack, _ = case
    out = {"sections": [
        {"id": "S01", "blocks": [{"type": "p", "source": "engine", "text": "Il Nero vince con {{mv:R5}}.",
                                  "assertions": [{"kind": "eval_band", "ref": "N1", "band": "decisive_minus"}]}]},
        {"id": "S07", "blocks": [{"type": "ul", "items": [
            {"text": "Dopo {{mv:R1}} rispondi {{mv:R1.u1}}.", "source": "engine"},
            {"text": "Non prendere: {{m:Qxd4@N3}} perde.", "source": "engine"}]}]},
    ]}
    kp = bench.key_points(spec, pack, out)
    assert kp == {"e4_vince": True, "qd4_solo_kh1": True, "qxd4_trappola": False}   # the trap is its ID, not the move
    assert bench.verdict_ok(cfg, spec, out) == (True, [])
    out["sections"][1]["blocks"][0]["items"][1]["text"] = "Non prendere: {{mv:R1.u3}} perde."
    out["sections"][0]["blocks"][0]["text"] = "Posizione equilibrata, ma {{m:e4@N1}} vince."
    assert bench.key_points(spec, pack, out) == {"e4_vince": True, "qd4_solo_kh1": True, "qxd4_trappola": True}
    assert bench.verdict_ok(cfg, spec, out) == (False, ["equilibrat"])


def test_bench_scores_the_real_deepseek_answer(cfg, case, tmp_path):
    """The real answer of the user case: «equilibrata» at -4,77 and invented pieces (V12): the run fails."""
    _, _, out = case
    client = FakeLLM([_response(out)] * (cfg.default.llm.max_retries + 1), model="deepseek")
    s = bench.run_bench(cfg, client, runs=1, positions=["e4_wins_w_1700"], progress=lambda m: None)
    p = s["positions"][0]
    run = p["runs"][0]
    assert run["passed"] is False and run["verdict"] is False     # the verdict paragraph was removed (V12)
    assert run["v12_final"] > 0 and run["complete"] is False and run["words"] > 0
    assert p["passed"] == 0 and p["n"] == 1
    assert bench.goal_reached(cfg, s)[0] is False

    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    pcfg = cfg.model_copy(update={"project_root": root})
    _, m1 = bench.write_bench(pcfg, s)
    assert "primo riferimento" in m1.read_text(encoding="utf-8")
    later = dict(s, created_utc="2099-01-01T00:00:00+00:00")
    _, m2 = bench.write_bench(pcfg, later)
    text = m2.read_text(encoding="utf-8")
    assert f"confronto con il {s['created_utc']}" in text and "| e4_wins_w_1700 | superati 0/1" in text
    assert "traguardo non raggiunto" in text


def test_goal_needs_every_position_and_the_cost(cfg):
    runs = bench.bench_cfg(cfg)["runs"]
    need = bench.bench_cfg(cfg)["goal"]["min_passing_runs"]
    cheap = {"passed": True, "cost_usd": bench.bench_cfg(cfg)["goal"]["max_mean_cost_usd"] / 2}
    good = {"passed": need, "runs": [cheap] * runs}
    s = {"runs": runs, "positions": [good, dict(good)]}
    assert bench.goal_reached(cfg, s)[0] is True
    s["positions"][1] = dict(good, passed=need - 1)
    assert bench.goal_reached(cfg, s)[0] is False
    dear = dict(cheap, cost_usd=bench.bench_cfg(cfg)["goal"]["max_mean_cost_usd"] * 2)
    s["positions"] = [dict(good, runs=[dear] * runs)]
    assert bench.goal_reached(cfg, s)[0] is False


def test_failed_run_counts_as_not_passed(cfg, case):
    spec, pack, _ = case
    r = bench.score_run(cfg, spec, pack, None, None, 1.0, "nessuna risposta")
    p = bench.aggregate("x", spec, [r])
    assert p["failed"] == 1 and p["passed"] == 0 and p["words"] is None


def test_cli_rejects_zero_runs():
    assert main(["bench", "--runs", "0"]) == 2
