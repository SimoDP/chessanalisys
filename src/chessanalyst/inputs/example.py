"""Example position (examples/example.fen)."""

from __future__ import annotations

from chessanalyst.config import Config
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.position import Position


def example_position(cfg: Config) -> Position:
    path = cfg.resolve_path(cfg.default.input.example_fen_file)
    board = parse_fen(path.read_text(encoding="utf-8"), cfg.wording["errors"])
    return Position(board=board, source="example")
