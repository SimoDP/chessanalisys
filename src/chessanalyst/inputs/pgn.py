"""PGN input (§2-bis.4)."""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

import chess
import chess.pgn

from chessanalyst.errors import InputError
from chessanalyst.inputs.fen import check_status, check_terminal, complete_fields
from chessanalyst.inputs.position import Position

AT_MOVE = re.compile(r"^(\d+)([wb])$")
AT_PLY = re.compile(r"^ply:(\d+)$")
KEPT_TAGS = ("Event", "Site", "Date", "Round", "White", "Black", "Result")
_BAD_SAN = re.compile(r"(?:illegal|invalid|ambiguous) san: '([^']*)'")


@dataclass
class GameInfo:
    index: int
    white: str
    black: str
    event: str
    date: str
    plies: int
    result: str

    def label(self) -> str:
        return f"{self.white} - {self.black}, {self.date}"


def read_games(text: str) -> list[chess.pgn.Game]:
    stream = io.StringIO(text.lstrip("﻿"))
    games = []
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        games.append(game)
    return games


def _start_board(game: chess.pgn.Game, messages: dict[str, str]) -> chess.Board:
    if game.headers.get("SetUp") == "1" or "FEN" in game.headers:
        fen = game.headers.get("FEN")
        if fen:
            try:
                board = chess.Board(complete_fields(fen))
            except ValueError as e:
                raise InputError(messages["malformed_fen"].format(detail=e)) from e
            check_status(board, messages)
    return game.board()


def check_game(game: chess.pgn.Game, messages: dict[str, str]) -> None:
    """Raise with ply, move number and text for illegal moves; other errors → unreadable."""
    if not game.errors:
        return
    err = game.errors[0]
    m = _BAD_SAN.search(str(err))
    if m:
        board = game.board()
        n = 0
        for mv in game.mainline_moves():
            board.push(mv)
            n += 1
        color = "Bianco" if board.turn == chess.WHITE else "Nero"
        raise InputError(messages["pgn_illegal_move"].format(
            ply=n + 1, move_no=board.fullmove_number, color=color, san=m.group(1)))
    raise InputError(messages["pgn_unreadable"].format(detail=err))


def game_infos(games: list[chess.pgn.Game]) -> list[GameInfo]:
    out = []
    for i, g in enumerate(games, 1):
        h = g.headers
        out.append(GameInfo(i, h.get("White", "?"), h.get("Black", "?"), h.get("Event", "?"),
                            h.get("Date", "?"), sum(1 for _ in g.mainline_moves()), h.get("Result", "*")))
    return out


def ply_of(spec: str | None, ply: int | None, start: chess.Board, total: int, messages: dict[str, str]) -> int:
    """Half-moves from the start of the game for ``--at``/``--ply`` (None = end)."""
    if ply is not None:
        k = ply
    elif spec is None or spec.strip() == "":
        return total
    else:
        s = spec.strip().lower()
        m_ply = AT_PLY.match(s)
        m_mv = AT_MOVE.match(s)
        if m_ply:
            k = int(m_ply.group(1))
        elif m_mv:
            n, c = int(m_mv.group(1)), m_mv.group(2)
            k = (n - start.fullmove_number) * 2 + (1 if c == "w" else 2) - (0 if start.turn == chess.WHITE else 1)
        else:
            raise InputError(messages["pgn_bad_at"].format(detail=spec))
    if k < 0 or k > total:
        raise InputError(messages["pgn_ply_out_of_range"].format(n=total))
    return k


def select_game(games: list[chess.pgn.Game], game_no: int | None, messages: dict[str, str]) -> chess.pgn.Game:
    if not games:
        raise InputError(messages["pgn_no_games"])
    if game_no is None:
        if len(games) > 1:
            raise InputError(messages["pgn_game_required"].format(n=len(games)))
        return games[0]
    if not 1 <= game_no <= len(games):
        raise InputError(messages["pgn_game_out_of_range"].format(n=len(games), k=game_no))
    return games[game_no - 1]


def position_from_game(game: chess.pgn.Game, messages: dict[str, str], at: str | None = None,
                       ply: int | None = None) -> Position:
    check_game(game, messages)
    start = _start_board(game, messages)
    moves = list(game.mainline_moves())
    k = ply_of(at, ply, start, len(moves), messages)
    board = start.copy()
    for mv in moves[:k]:
        board.push(mv)
    check_terminal(board, {**messages, "terminal_checkmate": messages["pgn_terminal"],
                           "terminal_stalemate": messages["pgn_terminal"],
                           "terminal_insufficient": messages["pgn_terminal"]})
    return Position(board=board, source="pgn", start_fen=start.fen(), plies=k, game=game)


def truncated_pgn(pos: Position) -> str:
    """game.pgn: the game up to the chosen position, no comments, only the kept tags."""
    assert pos.game is not None
    src = pos.game.headers
    out = chess.pgn.Game()
    out.headers.clear()
    for tag in KEPT_TAGS:
        out.headers[tag] = src.get(tag, "?" if tag != "Result" else "*")
    start = chess.Board(pos.start_fen) if pos.start_fen else chess.Board()
    if pos.start_fen and start.fen() != chess.STARTING_FEN:
        out.headers["SetUp"] = "1"
        out.headers["FEN"] = pos.start_fen
        out.setup(start)
    node = out
    for mv in pos.board.move_stack:
        node = node.add_variation(mv)
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return out.accept(exporter) + "\n"
