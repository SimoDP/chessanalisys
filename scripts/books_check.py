"""Merge and check the cards extracted from the chess books.

    python scripts/books_check.py /mnt/project-files/libri

Writes ``<dir>/catalogo/schede.jsonl`` (every card with a ``controllo`` field), ``controllo.md`` (summary and
disagreements) and ``campione.jsonl`` (the cards for the spot check). Stockfish answers are cached in
``catalogo/_stockfish.jsonl``, so an interrupted run resumes.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import chess  # noqa: E402

from chessanalyst import books  # noqa: E402
from chessanalyst.config import load_config  # noqa: E402
from chessanalyst.engines.factory import make_stockfish  # noqa: E402


def analyse(sf, card: dict, s: dict) -> dict:
    board = chess.Board(card["fen"])
    p = s["stockfish"]
    res = sf.analyse_node(board, p["multipv"], p["t_target"], p["d_min"], p["t_cap"])
    if not res.lines:                      # a slow first search can end before a complete iteration
        res = sf.analyse_node(board, p["multipv"], p["t_target"], p["d_min"], p["t_cap"] * p["retry_cap_factor"])
    best = res.lines[0]
    out = {"cp": best.eval_white_cp, "mate": best.mate_white, "best": [ln.san for ln in res.lines],
           "depth": res.depth, "keys": {}}
    sign = 1 if board.turn == chess.WHITE else -1
    for m in card.get("mosse_chiave") or []:
        try:
            mv = board.parse_san(m["san"])
        except (KeyError, ValueError):
            continue
        same = next((ln for ln in res.lines if ln.uci == mv.uci()), None)
        if same is None:
            lines = sf.analyse_node(board, 1, p["key_t_target"], 1, p["key_t_cap"], root_moves=[mv]).lines
            if not lines:
                continue
            same = lines[0]
        out["keys"][m["san"]] = sign * (best.eval_white_cp - same.eval_white_cp)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Unisce e controlla le schede dei libri")
    ap.add_argument("books_dir", type=Path)
    args = ap.parse_args(argv)
    s = books.load_settings(ROOT)
    out_dir = args.books_dir / "catalogo"
    out_dir.mkdir(exist_ok=True)
    cache_f = out_dir / "_stockfish.jsonl"
    cache = {}
    if cache_f.is_file():
        for line in cache_f.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            cache[d["id"]] = d["sf"]
    cards, broken = [], Counter()
    for book, card, _ in books.read_cards(args.books_dir):
        if book == "catalogo":
            continue
        if card is None:
            broken[book] += 1
            continue
        card["libro"] = book
        card["controllo"] = books.check_card(card)
        cards.append(card)
    cfg = load_config(ROOT)
    with make_stockfish(cfg) as sf, cache_f.open("a", encoding="utf-8") as cf:
        for i, card in enumerate(cards, 1):
            c = card["controllo"]
            if not c["fen_ok"]:
                continue
            if card["id"] not in cache:
                cache[card["id"]] = analyse(sf, card, s)
                cf.write(json.dumps({"id": card["id"], "sf": cache[card["id"]]}, ensure_ascii=False) + "\n")
                cf.flush()
                if i % 50 == 0:
                    print(f"{i}/{len(cards)}", flush=True)
            r = cache[card["id"]]
            c["stockfish"] = r
            c["accordo"] = books.agreement(card.get("giudizio"), books.eval_class(r["cp"], r["mate"], s), s)
            c["mosse_perdenti"] = [k for k, v in r["keys"].items() if v > s["key_move_loss_cp"]]
    with (out_dir / "schede.jsonl").open("w", encoding="utf-8") as f:
        for card in cards:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    with (out_dir / "campione.jsonl").open("w", encoding="utf-8") as f:
        for card in books.sample([c for c in cards if c["controllo"]["fen_ok"]], s):
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    (out_dir / "controllo.md").write_text(summary(cards, broken), encoding="utf-8")
    print(f"Schede: {len(cards)} in {out_dir}")
    return 0


def summary(cards: list[dict], broken: Counter) -> str:
    by = {}
    for c in cards:
        by.setdefault(c["libro"], []).append(c)
    lines = ["# Controllo delle schede dei libri", "",
             "| Libro | Schede | Righe illeggibili | FEN non valida | Lato sbagliato | Mosse illegali | "
             "Giudizio ok | Diverso | Contrario | Mossa chiave che perde |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for book, cs in sorted(by.items()):
        k = Counter(c["controllo"].get("accordo", "n/a") for c in cs)
        lines.append(
            f"| {book} | {len(cs)} | {broken[book]} | {sum(not c['controllo']['fen_ok'] for c in cs)} | "
            f"{sum(not c['controllo']['side_ok'] for c in cs)} | {sum(bool(c['controllo']['bad_moves']) for c in cs)} | "
            f"{k['ok']} | {k['diverso']} | {k['contrario']} | "
            f"{sum(bool(c['controllo'].get('mosse_perdenti')) for c in cs)} |")
    lines += ["", "## Giudizio contrario a Stockfish", ""]
    for c in cards:
        r = c["controllo"]
        if r.get("accordo") == "contrario":
            sf = r["stockfish"]
            ev = f"matto in {sf['mate']}" if sf["mate"] is not None else f"{sf['cp'] / 100:+.2f}"
            lines.append(f"- {c['id']} ({c.get('split')}): libro «{c.get('giudizio')}», Stockfish {ev}, "
                         f"migliore {sf['best'][0]} · `{c['fen']}`")
    lines += ["", "## Mosse chiave che perdono", ""]
    for c in cards:
        r = c["controllo"]
        for san in r.get("mosse_perdenti", []):
            lines.append(f"- {c['id']}: {san} perde {r['stockfish']['keys'][san] / 100:.2f} "
                         f"(migliore {r['stockfish']['best'][0]}) · `{c['fen']}`")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
