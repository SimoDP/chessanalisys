"""FEN validation (§2-bis.3)."""

from __future__ import annotations

import chess

from chessanalyst.errors import InputError
from chessanalyst.inputs.detect import clean

# Checked in this order; the first flag present gives the message.
# A pawn on the back rank also counts as an extra pawn: report the back rank first.
_STATUS_ORDER = (
    "STATUS_NO_WHITE_KING", "STATUS_NO_BLACK_KING", "STATUS_TOO_MANY_KINGS", "STATUS_PAWNS_ON_BACKRANK",
    "STATUS_TOO_MANY_WHITE_PAWNS", "STATUS_TOO_MANY_BLACK_PAWNS",
    "STATUS_TOO_MANY_WHITE_PIECES", "STATUS_TOO_MANY_BLACK_PIECES", "STATUS_BAD_CASTLING_RIGHTS", "STATUS_INVALID_EP_SQUARE",
    "STATUS_OPPOSITE_CHECK", "STATUS_TOO_MANY_CHECKERS", "STATUS_IMPOSSIBLE_CHECK",
)


def complete_fields(fen: str) -> str:
    """4 fields → ``0 1`` appended; 5 fields → ``1`` appended."""
    fields = fen.split()
    if len(fields) == 4:
        fields += ["0", "1"]
    elif len(fields) == 5:
        fields.append("1")
    return " ".join(fields)


def check_status(board: chess.Board, messages: dict[str, str]) -> None:
    status = board.status()
    if status == chess.STATUS_VALID:
        return
    for name in _STATUS_ORDER:
        if status & getattr(chess, name):
            raise InputError(messages[name])
    raise InputError(messages["invalid_status"].format(detail=repr(status)))


def check_terminal(board: chess.Board, messages: dict[str, str]) -> None:
    if board.is_checkmate():
        raise InputError(messages["terminal_checkmate"])
    if board.is_stalemate():
        raise InputError(messages["terminal_stalemate"])
    if board.is_insufficient_material():
        raise InputError(messages["terminal_insufficient"])


def parse_fen(text: str, messages: dict[str, str], allow_terminal: bool = False) -> chess.Board:
    fen = complete_fields(clean(text))
    try:
        board = chess.Board(fen)
    except ValueError as e:
        raise InputError(messages["malformed_fen"].format(detail=e)) from e
    check_status(board, messages)  # before the terminal check (G.2 #12)
    if not allow_terminal:
        check_terminal(board, messages)
    return chess.Board(board.fen(en_passant="legal"))
