"""Bench of the motif detectors on Lichess puzzles (data plan, phase 1): selection, detection, report."""

from __future__ import annotations

from chessanalyst import motif_bench as mb
from tests.conftest import ROOT

CSV = """PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags
f1,r3k3/7p/8/3N4/8/8/8/6K1 b - - 0 1,h7h6 d5c7,1200,75,90,100,fork short,u,
c1,4k3/8/8/8/8/8/8/4K2R b - - 0 1,e8d8 h1h8,1300,75,90,100,short,u,
"""


def _puzzles():
    return list(mb.read_puzzles(CSV.splitlines(keepends=True)))


def _words(cfg):
    return cfg.wording["pieces"]


def test_select_takes_themes_and_control_in_file_order():
    chosen = mb.select(_puzzles(), ["fork"], per_theme=1, control=1)
    assert [p.pid for p in chosen] == ["f1", "c1"]
    assert [p.pid for p in mb.select(_puzzles(), ["fork"], per_theme=1, control=0)] == ["f1"]


def test_knight_fork_is_detected_on_the_first_solver_move(cfg):
    fork = _puzzles()[0]
    steps = mb.detect(fork, _words(cfg))
    assert "fork" in steps[0]


def test_run_counts_tagged_and_control_puzzles(cfg):
    settings = {"themes": {"fork": "fork"}, "rating_bands": [1500], "source_url": "u", "sample_file": "s"}
    res = mb.run(_puzzles(), settings, _words(cfg))
    row = res["rows"][("fork", "fork")]
    assert (row["n"], row["hit"], row["first"]) == (1, 1, 1)
    assert res["control"]["n"] == 1 and res["control"]["fired"]["fork"] == 0
    assert "| fork | fork | 1 | 100 % | 100 % |" in mb.report(res, settings)


def test_recorded_sample_runs_and_matches_the_committed_report(cfg):
    settings = mb.load_settings(ROOT)
    with (ROOT / settings["sample_file"]).open(encoding="utf-8") as f:
        puzzles = list(mb.read_puzzles(f))
    text = mb.report(mb.run(puzzles, settings, _words(cfg)), settings)
    assert text == (ROOT / settings["report_file"]).read_text(encoding="utf-8")
