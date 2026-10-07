"""Computed chess facts for the model (D-71): where every piece stands and what each move and line of the pack
does on the board, so that the text never has to read the FEN or guess a tactic.

- ``board_text``: occupied squares → «donna bianca», «cavallo nero», …;
- ``move_facts``: one move from a position — capture, check, enemy pieces newly attacked (by the moved piece or
  discovered behind it, with whether they are defended), pieces newly pinned, own pieces left hanging;
- ``line_facts``: a line — captures in its first plies and the material balance at its end, for the user.

Only python-chess and the piece values of §5.1 (``features/values.py``).
"""

from __future__ import annotations

import chess

from chessanalyst.features.values import piece_value

SIDE = {chess.WHITE: "w", chess.BLACK: "b"}


def piece_name(piece: chess.Piece, words: dict) -> str:
    sym = piece.symbol().lower()
    gender = "color_f" if sym in words["feminine"] else "color_m"
    return f"{words['names'][sym]} {words[gender][SIDE[piece.color]]}"


def board_text(board: chess.Board, words: dict) -> dict[str, str]:
    return {chess.square_name(sq): piece_name(p, words) for sq, p in sorted(board.piece_map().items())}


def _defended(board: chess.Board, sq: chess.Square) -> bool:
    piece = board.piece_at(sq)
    return piece is not None and bool(board.attackers(piece.color, sq))


def _hanging(board: chess.Board, color: chess.Color) -> list[chess.Square]:
    """Pieces of ``color`` attacked and either undefended or attacked by a cheaper piece (kings excluded)."""
    out = []
    for sq, p in board.piece_map().items():
        if p.color != color or p.piece_type == chess.KING:
            continue
        attackers = board.attackers(not color, sq)
        if not attackers:
            continue
        cheapest = min(piece_value(board.piece_type_at(a)) for a in attackers)
        if not _defended(board, sq) or cheapest < piece_value(p.piece_type):
            out.append(sq)
    return out


def move_facts(board: chess.Board, san: str, words: dict) -> dict:
    """What ``san`` does in ``board`` (the side to move plays it)."""
    mv = board.parse_san(san)
    me = board.turn
    moved = board.piece_at(mv.from_square)
    captured = board.piece_at(mv.to_square)
    if board.is_en_passant(mv):
        captured = chess.Piece(chess.PAWN, not me)
    after = board.copy(stack=False)
    after.push(mv)
    out: dict = {"move": san, "by": SIDE[me], "piece": piece_name(moved, words),
                 "from": chess.square_name(mv.from_square), "to": chess.square_name(mv.to_square)}
    if captured is not None:
        out["captures"] = piece_name(captured, words)
    if mv.promotion:
        out["promotes_to"] = words["names"][chess.piece_symbol(mv.promotion)]
    if after.is_checkmate():
        out["checkmate"] = True
    elif after.is_check():
        out["check"] = True
    attacks = []
    for sq, p in after.piece_map().items():
        if p.color == me or p.piece_type == chess.KING:
            continue
        now = after.attackers(me, sq)
        before = board.attackers(me, sq) if board.piece_at(sq) == p else chess.SquareSet()
        new = [a for a in now if a not in before and a != mv.from_square]
        if not new:
            continue
        attacks.append({"square": chess.square_name(sq), "piece": piece_name(p, words),
                        "by": [chess.square_name(a) for a in sorted(new)],
                        "discovered": any(a != mv.to_square for a in new),
                        "defended": _defended(after, sq)})
    if attacks:
        out["attacks"] = sorted(attacks, key=lambda a: -piece_value(after.piece_type_at(chess.parse_square(a["square"]))))
    pins = [chess.square_name(sq) for sq, p in after.piece_map().items()
            if p.color != me and after.is_pinned(not me, sq) and not board.is_pinned(not me, sq)]
    if pins:
        out["pins"] = [f"{piece_name(after.piece_at(chess.parse_square(s)), words)} in {s}" for s in sorted(pins)]
    left = [sq for sq in _hanging(after, me) if sq not in _hanging(board, me) or sq == mv.to_square]
    if left:
        out["leaves_hanging"] = [f"{piece_name(after.piece_at(s), words)} in {chess.square_name(s)}"
                                 for s in sorted(left)]
    return out


def line_facts(board: chess.Board, plies: list[str], first: int, user: chess.Color, words: dict) -> dict:
    """Captures and checks in the first ``first`` plies; material balance for the user at the end of the line
    (all its plies, so an exchange is not cut in the middle)."""
    b = board.copy(stack=False)
    start = _balance(b, user)
    captures, checks = [], 0
    for k, san in enumerate(plies):
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        if k < first:
            victim = b.piece_at(mv.to_square) or (chess.Piece(chess.PAWN, not b.turn) if b.is_en_passant(mv) else None)
            if victim is not None:
                captures.append(f"{san}: {piece_name(victim, words)}")
        b.push(mv)
        if k < first and b.is_check():
            checks += 1
    out: dict = {"material_change_for_user": _balance(b, user) - start}
    if captures:
        out["captures"] = captures
    if checks:
        out["checks"] = checks
    if b.is_checkmate():
        out["ends_in_checkmate"] = True
    return out


def _balance(board: chess.Board, user: chess.Color) -> int:
    mine = sum(piece_value(p.piece_type) for p in board.piece_map().values() if p.color == user)
    theirs = sum(piece_value(p.piece_type) for p in board.piece_map().values() if p.color != user)
    return mine - theirs


def pack_facts(pack: dict, words: dict, first_plies: int) -> dict:
    """The facts of every move and line the text can cite."""
    root = chess.Board(pack["position"]["fen"])
    user = chess.WHITE if pack["user"]["color"] == "w" else chess.BLACK
    eng = pack["engine"]
    nodes = {n["id"]: n for n in pack["nodes"]}
    moves: dict[str, dict] = {}
    for c in eng["candidates"]:
        moves[c["id"]] = move_facts(root, c["san"], words)
    for r in eng["replies"]:
        moves[r["id"]] = move_facts(root, r["san"], words)
        after = root.copy(stack=False)
        after.push_uci(r["uci"])
        for u in r["user_best"]:
            moves[u["id"]] = move_facts(after, u["san"], words)
    lines: dict[str, dict] = {}
    for ln in list(eng["pvs"]) + list(pack.get("filtered_lines", [])):
        start = nodes.get(ln["start_node"])
        if start is None:
            continue
        lines[ln["id"]] = line_facts(chess.Board(start["fen"]), ln["plies"], first_plies, user, words)
    out = {"board": board_text(root, words), "moves": moves, "lines": lines}
    null = (eng.get("null_move") or {}).get("node")
    if null:
        out["hypothetical_nodes"] = [null]
    return out


def pin_matters(board: chess.Board, pinner: int, behind: int) -> bool:
    """The user's rule (usefulness test, phase 2): a pin counts only if the piece behind is the king, is
    undefended, is worth more than the pinner (a queen behind a bishop's pin), or would be attacked more times
    than it is defended once the pinned piece moves (the pinner counts as one more attacker)."""
    q = board.piece_at(behind)
    if q.piece_type == chess.KING:
        return True
    defenders = len(board.attackers(q.color, behind))
    attackers = len(board.attackers(not q.color, behind)) + 1
    return defenders == 0 or piece_value(q.piece_type) > piece_value(board.piece_type_at(pinner)) \
        or attackers > defenders
