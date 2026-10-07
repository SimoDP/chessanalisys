"""Bench of the tactical motif detectors on Lichess puzzles (data plan, phase 1).

Each puzzle of the Lichess database (CC0) carries themes written by its generator: ``fork``, ``pin``,
``discoveredAttack``… This bench replays the solution and asks the detectors of the code
(``features/tactics.py``, ``features/motifs.py``) whether they see the motif somewhere along it:

- recall: share of the puzzles tagged with a theme in which the mapped detector fires;
- false alarms: share of the control puzzles (none of the measured themes) in which it fires anyway.

The Lichess tags are not exhaustive, so a «false alarm» is an upper bound: some of them are real motifs that
the generator did not tag. Puzzle format: ``FEN`` is the position before the opponent's move, ``Moves`` the
UCI moves starting with that move; the solver plays the moves at odd indices.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import chess
import yaml

from chessanalyst.features.motifs import move_facts
from chessanalyst.features.tactics import forks, hanging_squares, overloaded, skewers

COLUMNS = ("PuzzleId", "FEN", "Moves", "Rating", "Themes")
DETECTORS = ("fork", "pin", "pin_created", "skewer", "discovered_attack", "discovered_check", "hanging_piece",
             "overloaded_piece")


@dataclass(frozen=True)
class Puzzle:
    pid: str
    fen: str
    moves: tuple[str, ...]
    rating: int
    themes: frozenset[str]


def load_settings(root: Path) -> dict:
    return yaml.safe_load((root / "config" / "motif_bench.yaml").read_text(encoding="utf-8"))


def read_puzzles(lines: Iterable[str]) -> Iterator[Puzzle]:
    for row in csv.DictReader(lines):
        yield Puzzle(row["PuzzleId"], row["FEN"], tuple(row["Moves"].split()), int(row["Rating"]),
                     frozenset(row["Themes"].split()))


def select(puzzles: Iterable[Puzzle], themes: Iterable[str], per_theme: int, control: int) -> list[Puzzle]:
    """The first ``per_theme`` puzzles of each theme and the first ``control`` with none of them, in file order
    (the database is sorted by a random id, so file order is a random sample)."""
    themes = list(themes)
    wanted = {t: per_theme for t in themes}
    left_control = control
    out: list[Puzzle] = []
    for p in puzzles:
        hit = [t for t in themes if t in p.themes]
        if hit:
            if any(wanted[t] > 0 for t in hit):
                for t in hit:
                    wanted[t] -= 1
                out.append(p)
        elif left_control > 0:
            left_control -= 1
            out.append(p)
        if left_control <= 0 and all(v <= 0 for v in wanted.values()):
            break
    return out


def write_sample(puzzles: list[Puzzle], path: Path) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for p in puzzles:
        w.writerow([p.pid, p.fen, " ".join(p.moves), p.rating, " ".join(sorted(p.themes))])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buf.getvalue(), encoding="utf-8")


def _pinned(board: chess.Board, side: chess.Color) -> bool:
    king = board.king(side)
    return any(p.color == side and sq != king and board.is_pinned(side, sq) for sq, p in board.piece_map().items())


def detect(p: Puzzle, words: dict) -> list[set[str]]:
    """Detectors that fire on each of the solver's moves of ``p``, in order."""
    board = chess.Board(p.fen)
    board.push_uci(p.moves[0])
    me = board.turn
    opp = not me
    steps: list[set[str]] = []
    for k, uci in enumerate(p.moves[1:]):
        mv = chess.Move.from_uci(uci)
        if k % 2:                       # the opponent's replies inside the solution
            board.push(mv)
            continue
        before = board.copy(stack=False)
        after = board.copy(stack=False)
        after.push(mv)
        to = mv.to_square
        found: set[str] = set()
        if any(f[0] == to for f in forks(after, opp)):
            found.add("fork")
        if _pinned(before, opp) or _pinned(after, opp):
            found.add("pin")
        facts = move_facts(before, before.san(mv), words)
        if facts.get("pins"):
            found.add("pin_created")
        if any(s[0] == to for s in skewers(after, opp)):
            found.add("skewer")
        disc_check = after.is_check() and any(c != to for c in after.checkers())
        if disc_check:
            found.add("discovered_check")
        if disc_check or any(a["discovered"] for a in facts.get("attacks", [])):
            found.add("discovered_attack")
        if before.is_capture(mv) and to in hanging_squares(before, opp):
            found.add("hanging_piece")
        if overloaded(before, opp) or overloaded(after, opp):
            found.add("overloaded_piece")
        steps.append(found)
        board = after
    return steps


def _band(rating: int, cuts: list[int]) -> str:
    lo = None
    for c in cuts:
        if rating < c:
            return f"< {c}" if lo is None else f"{lo}–{c - 1}"
        lo = c
    return f">= {lo}"


def run(puzzles: list[Puzzle], settings: dict, words: dict) -> dict:
    """Counts per (theme, detector) and per rating band, and false alarms on the control puzzles."""
    themes: dict[str, str | list[str]] = settings["themes"]
    cuts = settings["rating_bands"]
    pairs = [(t, d) for t, ds in themes.items() for d in ([ds] if isinstance(ds, str) else ds)]
    if "pin" in themes:
        pairs.append(("pin", "pin_created"))
    rows = {pair: {"n": 0, "hit": 0, "first": 0, "bands": {}} for pair in pairs}
    control = {"n": 0, "fired": {d: 0 for d in DETECTORS}, "first": {d: 0 for d in DETECTORS}}
    misses: dict[tuple[str, str], list[str]] = {pair: [] for pair in pairs}
    for p in puzzles:
        steps = detect(p, words)
        found = set().union(*steps)
        first = steps[0] if steps else set()
        tagged = [t for t in themes if t in p.themes]
        if not tagged:
            control["n"] += 1
            for d in found:
                control["fired"][d] += 1
            for d in first:
                control["first"][d] += 1
            continue
        for t, d in pairs:
            if t not in p.themes:
                continue
            r = rows[(t, d)]
            b = r["bands"].setdefault(_band(p.rating, cuts), {"n": 0, "hit": 0})
            r["n"] += 1
            b["n"] += 1
            r["first"] += d in first
            if d in found:
                r["hit"] += 1
                b["hit"] += 1
            else:
                misses[(t, d)].append(p.pid)
    return {"rows": rows, "control": control, "misses": misses, "total": len(puzzles)}


def _pct(a: int, n: int) -> str:
    return f"{round(100 * a / n)} %" if n else "–"


def report(result: dict, settings: dict) -> str:
    rows = result["rows"]
    cuts = settings["rating_bands"]
    bands = [_band(x, cuts) for x in [cuts[0] - 1, *cuts]]
    ctl = result["control"]
    lines = [
        "# Banco dei motivi tattici sui problemi di Lichess",
        "",
        f"Campione: {result['total']} problemi da [{settings['source_url']}]({settings['source_url']}) (CC0), "
        f"file `{settings['sample_file']}`. Rigenera con `python scripts/motif_bench.py`.",
        "",
        "**Ritrovati**: quota dei problemi con quel tema in cui il rilevatore del codice scatta su almeno una mossa "
        "della soluzione; **alla prima mossa** conta solo la prima mossa del solutore, quella che l'app "
        "commenta come mossa candidata. **Falsi allarmi**: quota dei problemi di controllo (nessuno dei temi misurati) in cui "
        "scatta comunque; è un limite superiore, perché i temi di Lichess non sono completi.",
        "",
        "| Tema di Lichess | Rilevatore | Problemi | Ritrovati | Alla prima mossa | " + " | ".join(f"Punteggio {b}" for b in bands)
        + " | Falsi allarmi | Falsi allarmi alla prima mossa |",
        "| --- | --- | --- | --- | --- | " + " | ".join("---" for _ in bands) + " | --- | --- |",
    ]
    for (t, d), r in rows.items():
        cells = [_pct(r["bands"].get(b, {}).get("hit", 0), r["bands"].get(b, {}).get("n", 0)) for b in bands]
        lines.append(f"| {t} | {d} | {r['n']} | {_pct(r['hit'], r['n'])} | {_pct(r['first'], r['n'])} | " + " | ".join(cells)
                     + f" | {_pct(ctl['fired'][d], ctl['n'])} | {_pct(ctl['first'][d], ctl['n'])} |")
    lines += ["", f"Problemi di controllo: {ctl['n']}.", "", "## Primi problemi non ritrovati", ""]
    for (t, d), ids in result["misses"].items():
        if ids:
            shown = ", ".join(f"[{i}](https://lichess.org/training/{i})" for i in ids[:5])
            lines.append(f"- {t} / {d}: {shown}")
    return "\n".join(lines) + "\n"
