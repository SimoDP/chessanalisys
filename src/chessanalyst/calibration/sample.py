"""Sample of positions from rapid games of the Lichess open database (M5).

The monthly dump (``.pgn.zst``) is read as a stream: no full download. Only rated rapid games between players
within ``max_rating_gap``; one position per game, at a half-move drawn uniformly (fixed seed) with at least
``tail_plies`` half-moves after it; positions are kept until each Elo band of the side to move has
``per_band`` of them. Player names are not kept (only the public game ID, the ratings and the moves).
"""

from __future__ import annotations

import io
import json
import random
import urllib.request
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import chess
import chess.pgn

from chessanalyst import elo
from chessanalyst.config import BAND_KEYS, Config

POSITIONS_FILE = Path("fixtures/calibration/positions.jsonl")


def stream_games(url: str) -> Iterator[chess.pgn.Game]:
    import zstandard   # optional dependency (extra «calibration»)

    with urllib.request.urlopen(url, timeout=120) as resp:
        text = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(resp), encoding="utf-8")
        while True:
            game = chess.pgn.read_game(text)
            if game is None:
                return
            yield game


def _rating(game: chess.pgn.Game, tag: str) -> int | None:
    v = game.headers.get(tag, "")
    return int(v) if v.isdigit() else None


def pick_position(cfg: Config, game: chess.pgn.Game, rng: random.Random) -> dict[str, Any] | None:
    sp = cfg.calibration["sample"]
    w, b = _rating(game, "WhiteElo"), _rating(game, "BlackElo")
    if w is None or b is None or abs(w - b) > sp["max_rating_gap"] or game.errors:
        return None
    moves = list(game.mainline_moves())
    hi = min(sp["ply_max"], len(moves) - sp["tail_plies"])
    if hi < sp["ply_min"]:
        return None
    ply = rng.randint(sp["ply_min"], hi)
    board = chess.Board()
    for mv in moves[:ply]:
        board.push(mv)
    if board.is_game_over():
        return None
    side = "w" if board.turn == chess.WHITE else "b"
    self_elo, opp_elo = (w, b) if side == "w" else (b, w)
    band = elo.band_of(elo.lichess_to_fide(self_elo, cfg), cfg)
    site = game.headers.get("Site", "")
    return {
        "id": site.rsplit("/", 1)[-1], "time_control": game.headers.get("TimeControl"),
        "result": game.headers.get("Result"), "white_elo": w, "black_elo": b, "ply": ply, "side": side,
        "elo_self": self_elo, "elo_opp": opp_elo, "band": band,
        "moves": [m.uci() for m in moves[: ply + sp["tail_plies"]]],
    }


def sample_positions(cfg: Config, games: Iterator[chess.pgn.Game] | None = None,
                     progress: Callable[[str], None] = lambda s: None) -> list[dict[str, Any]]:
    src, sp = cfg.calibration["source"], cfg.calibration["sample"]
    rng = random.Random(sp["seed"])
    if games is None:
        games = stream_games(src["url"].format(month=src["month"]))
    out: dict[str, list[dict]] = {b: [] for b in BAND_KEYS}
    for n, game in enumerate(games, 1):
        if n > src["max_games"] or all(len(v) >= sp["per_band"] for v in out.values()):
            break
        if game.headers.get("Event") != src["event"]:
            continue
        pos = pick_position(cfg, game, rng)
        if pos is not None and len(out[pos["band"]]) < sp["per_band"]:
            pos["month"] = src["month"]
            out[pos["band"]].append(pos)
            if sum(len(v) for v in out.values()) % 10 == 0:
                progress(f"{n} partite lette · " + " · ".join(f"{b} {len(v)}" for b, v in out.items()))
    return [p for b in BAND_KEYS for p in out[b]]


def write_positions(cfg: Config, positions: list[dict[str, Any]]) -> Path:
    path = cfg.project_root / POSITIONS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(p, separators=(",", ":")) + "\n" for p in positions), encoding="utf-8")
    return path


def read_positions(cfg: Config) -> list[dict[str, Any]]:
    path = cfg.project_root / POSITIONS_FILE
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
