"""Confirmation screen before the engines (§2-bis.5)."""

from __future__ import annotations

import chess

from chessanalyst.inputs.position import Position


def ascii_board(board: chess.Board) -> str:
    rows = str(board).splitlines()
    out = [f"{8 - i}  {row}" for i, row in enumerate(rows)]
    out.append("   a b c d e f g h")
    return "\n".join(out)


def castling_text(board: chess.Board) -> str:
    rights = board.castling_xfen()
    return "nessuno" if rights == "-" else rights


def confirmation_text(pos: Position, opening: dict | None) -> str:
    b = pos.board
    side = "il Bianco" if b.turn == chess.WHITE else "il Nero"
    ep = chess.square_name(b.ep_square) if b.ep_square is not None and b.has_legal_en_passant() else "nessuna"
    lines = [
        ascii_board(b),
        "",
        f"FEN: {pos.fen}",
        f"Tratto: {side}",
    ]
    if pos.source == "pgn":
        lines.append(f"Ultima mossa: {pos.last_move_san or 'nessuna'} · semimosse giocate: {pos.plies}")
    lines.append("Apertura: " + (f"{opening['eco']} {opening['name']}" if opening else "non riconosciuta"))
    lines.append(f"Arrocco: {castling_text(b)} · en passant: {ep}")
    return "\n".join(lines)
