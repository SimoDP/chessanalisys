"""From a method + text to a :class:`Position` (non-interactive path)."""

from __future__ import annotations

from chessanalyst.config import Config
from chessanalyst.errors import InputError, UsageError
from chessanalyst.inputs.detect import detect_format
from chessanalyst.inputs.example import example_position
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.pgn import position_from_game, read_games, select_game
from chessanalyst.inputs.position import Position

FORMAT_NAMES = {"fen": "FEN", "pgn": "PGN"}


def detect_or_assume(text: str, method: str, msgs: dict[str, str]) -> str:
    """With FEN chosen, an unrecognised text is validated as a FEN (so that the
    user gets «FEN malformata: …» instead of «Formato non riconosciuto»)."""
    try:
        return detect_format(text, msgs)
    except InputError:
        if method == "fen":
            return "fen"
        raise


def load_position(cfg: Config, method: str, text: str | None = None, game_no: int | None = None,
                  at: str | None = None, ply: int | None = None, interactive_mismatch=None) -> Position:
    msgs = cfg.wording["errors"]
    if method == "example":
        return example_position(cfg)
    if text is None or not text.strip():
        raise InputError(msgs["empty_input"])
    detected = detect_or_assume(text, method, msgs)
    if detected != method:
        msg = msgs["format_mismatch"].format(chosen=FORMAT_NAMES[method], detected=FORMAT_NAMES[detected])
        if interactive_mismatch is None:
            raise UsageError(msg)
        if not interactive_mismatch(msg, detected):
            raise InputError(msg)
        method = detected
    if method == "fen":
        return Position(board=parse_fen(text, msgs), source="fen")
    games = read_games(text)
    game = select_game(games, game_no, msgs)
    return position_from_game(game, msgs, at=at, ply=ply)
