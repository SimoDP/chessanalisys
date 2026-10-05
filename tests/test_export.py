"""``chessanalyst export`` (M6): HTML, Markdown and PGN of an output folder."""

from __future__ import annotations

import io
import json

import chess
import chess.pgn
import pytest

from chessanalyst.cli import main
from chessanalyst.errors import UsageError
from chessanalyst.export import export, pack_pgn
from chessanalyst.golden.packs import load_frozen_pack
from tests.m6_helpers import synthetic_stack


def _read(text: str) -> chess.pgn.Game:
    return chess.pgn.read_game(io.StringIO(text))


def test_pgn_of_a_pack(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1900")
    game = _read(str(pack_pgn(cfg, pack)))
    assert game.headers["FEN"] == pack["position"]["fen"] and game.headers["SetUp"] == "1"
    assert all(game.headers[k] == "?" for k in ("White", "Black", "Site"))        # no names
    listed = [c for c in pack["engine"]["candidates"] if c["listed"]]
    assert [v.san() for v in game.variations] == [c["san"] for c in listed]       # the best one is the main line
    from chessanalyst.render.format_it import fmt_eval

    for v, c in zip(game.variations, listed):
        assert v.comment == cfg.wording["export"]["candidate"].format(eval=fmt_eval(c["eval_user_cp"], c["mate_user"]))
    first = game.variations[0]
    depth = 0
    node = first
    while node.variations:
        node = node.variations[0]
        depth += 1
    assert depth + 1 == cfg.default.export.pgn_plies                               # PV cut to export.pgn_plies


def test_pgn_lines_grafted_and_threats_skipped(cfg, root):
    pack = json.loads((root / "fixtures/packs/fried_liver_w_1500.pack.json").read_text(encoding="utf-8"))
    text = str(pack_pgn(cfg, pack))
    nodes = {n["id"]: n for n in pack["nodes"]}
    for ln in pack["filtered_lines"]:
        reachable = "--" not in nodes[ln["start_node"]]["path"]
        assert (f"{ln['id']}:" in text) == reachable, ln["id"]
    assert _read(text).errors == []


def test_export_formats(cfg, monkeypatch, tmp_path):
    synthetic_stack(cfg, monkeypatch, tmp_path)
    assert main(["analyze", "--yes", "--elo", "1900", "--budget", "fast", "--out", str(tmp_path / "o")]) == 0
    [folder] = list((tmp_path / "o").iterdir())
    for fmt in ("md", "pgn", "html"):
        dest = export(cfg, folder, fmt, tmp_path / "x")
        assert dest == tmp_path / "x" / f"{folder.name}.{fmt}" and dest.stat().st_size > 0
    assert (tmp_path / "x" / f"{folder.name}.md").read_text(encoding="utf-8") == \
        (folder / "analysis.md").read_text(encoding="utf-8")
    assert main(["export", str(folder), "--format", "pgn"]) == 0 and (folder / f"{folder.name}.pgn").is_file()
    # an analysis made before M6 has no render.json: html refused with a hint, the others still work
    (folder / "render.json").unlink()
    with pytest.raises(UsageError, match="rerun"):
        export(cfg, folder, "html")
    assert export(cfg, folder, "pgn")


def test_export_errors(cfg, tmp_path, capsys):
    with pytest.raises(UsageError):
        export(cfg, tmp_path / "missing", "md")
    with pytest.raises(UsageError):
        export(cfg, tmp_path, "pdf")
    assert main(["export", str(tmp_path / "missing"), "--format", "md"]) == 2
    with pytest.raises(SystemExit) as e:
        main(["export", str(tmp_path), "--format", "pdf"])
    assert e.value.code == 2
