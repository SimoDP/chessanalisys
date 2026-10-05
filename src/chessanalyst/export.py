"""``chessanalyst export`` (M6): an output folder as one portable file.

- ``html``: the page with clickable moves and the board (rebuilt from ``pack.json`` and ``render.json``);
- ``md``: the Markdown document;
- ``pgn``: the analysed position with the lines of the engine as variations — the candidates (or the replies),
  then the filtered lines of §5-bis that start from a reachable position — with the evaluation of each line from
  the user's point of view. No names: the headers carry only the position and the program.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import chess
import chess.pgn

from chessanalyst.config import Config
from chessanalyst.errors import UsageError
from chessanalyst.render.format_it import fmt_eval
from chessanalyst.render.html import write_html

FORMATS = ("html", "md", "pgn")


def _packs(folder: Path) -> list[dict]:
    """One pack, or the two of «entrambi» (White first)."""
    names = ["pack.json"] if (folder / "pack.json").is_file() else ["pack_white.json", "pack_black.json"]
    if not all((folder / n).is_file() for n in names):
        raise UsageError(f"{folder} non contiene pack.json")
    return [json.loads((folder / n).read_text(encoding="utf-8")) for n in names]


def _walk(game: chess.pgn.GameNode, sans: list[str]) -> chess.pgn.GameNode | None:
    """The node after ``sans`` from the root, adding the missing moves; None if a move is not playable."""
    node = game
    for san in sans:
        if san == "--":
            return None
        try:
            mv = node.board().parse_san(san)
        except ValueError:
            return None
        node = node.variation(mv) if node.has_variation(mv) else node.add_variation(mv)
    return node


def _add_line(cfg: Config, start: chess.pgn.GameNode, plies: list[str], first: str, last: str | None) -> None:
    node = start
    for k, san in enumerate(plies[: cfg.default.export.pgn_plies]):
        try:
            mv = node.board().parse_san(san)
        except ValueError:
            break
        node = node.variation(mv) if node.has_variation(mv) else node.add_variation(mv)
        if k == 0 and first:
            node.comment = (node.comment + " " + first).strip()
    if last:
        node.comment = (node.comment + " " + last).strip()


def pack_pgn(cfg: Config, pack: dict) -> chess.pgn.Game:
    w = cfg.wording["export"]
    game = chess.pgn.Game()
    for k in ("White", "Black", "Site", "Round", "Date"):
        game.headers[k] = "?"
    game.headers["Event"] = w["pgn_event"]
    game.setup(chess.Board(pack["position"]["fen"]))
    game.comment = w["pgn_intro"].format(color=cfg.wording["colors"][pack["user"]["color"]])
    eng = pack["engine"]
    pvs = {p["id"]: p for p in eng["pvs"]}
    nodes = {n["id"]: n for n in pack["nodes"]}
    for kind, moves in (("candidate", eng["candidates"]), ("reply", eng["replies"])):
        for m in moves:
            if not m.get("listed", True) or m.get("pv") not in pvs:
                continue
            ev = fmt_eval(m["eval_user_cp"], m.get("mate_user"))
            _add_line(cfg, game, pvs[m["pv"]]["plies"], w[kind].format(eval=ev), None)
    for ln in pack.get("filtered_lines") or []:
        start = _walk(game, nodes[ln["start_node"]]["path"]) if ln["start_node"] in nodes else None
        if start is None:                     # a threat line starts after a null move: not representable in PGN
            continue
        head = (w["line_threat"].format(id=ln["id"]) if ln["kind"] == "threat"
                else w["line_refutation"].format(id=ln["id"], entry=(ln.get("entry") or {}).get("san", "")))
        _add_line(cfg, start, ln["plies"], head,
                  w["line_end"].format(eval=fmt_eval(ln["eval_end_user_cp"], ln.get("mate_user"))))
    return game


def export(cfg: Config, folder: Path, fmt: str, to: Path | None = None) -> Path:
    if fmt not in FORMATS:
        raise UsageError(f"Formato non valido: {fmt} (ammessi: {', '.join(FORMATS)})")
    if not folder.is_dir():
        raise UsageError(f"Cartella non trovata: {folder}")
    dest_dir = to if to is not None else folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{folder.name}.{fmt}"
    if fmt == "md":
        if not (folder / "analysis.md").is_file():
            raise UsageError(f"{folder} non contiene analysis.md")
        shutil.copyfile(folder / "analysis.md", dest)
    elif fmt == "html":
        if not (folder / "render.json").is_file() and not (folder / "render_white.json").is_file():
            raise UsageError(f"{folder} non contiene render.json (analisi precedente a M6: usa `chessanalyst rerun`)")
        page = write_html(cfg, folder)
        if page is None:
            raise UsageError("Pagina HTML non scritta: vedi run.log")
        if page != dest:
            shutil.copyfile(page, dest)
    else:
        games = [str(pack_pgn(cfg, p)) for p in _packs(folder)]
        dest.write_text("\n\n".join(games) + "\n", encoding="utf-8")
    return dest
