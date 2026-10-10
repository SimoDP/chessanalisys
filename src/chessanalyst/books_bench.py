"""Utility bench on the book cards marked ``verifica``: does the analysis find what the book says?

For each card: the verdict of N1 within the bands of the book's class (from the side to move), every key move
of the book cited at N1, every theme of the closed list named in the text. The plans written in words are not
scored. The scoring reuses ``bench.score_run``; the specs and frozen packs live next to the cards (outside the
repository).
"""

from __future__ import annotations

from datetime import datetime, timezone

from chessanalyst import books
from chessanalyst.bench import _mean


def make_spec(card: dict, s: dict) -> dict:
    b = s["bench"]
    sign = 1 if card["lato"] == "Bianco" else -1
    book = s["verdicts"].get(card.get("giudizio"))
    all_bands = sorted({x for v in b["verdict_bands"].values() for x in v})
    bands = all_bands if book is None else b["verdict_bands"][str(book * sign)]
    must = [{"id": f"mossa_{m['san']}", "text": m.get("perche", ""), "all": [{"move": m["san"], "node": "N1"}]}
            for m in card.get("mosse_chiave") or []]
    must += [{"id": f"tema_{t}", "text": t, "all": [{"text": b["theme_patterns"][t]}]}
             for t in card.get("temi") or [] if t in b["theme_patterns"]]
    return {"id": card["id"], "fen": card["fen"],
            "user": {"color": "w" if sign == 1 else "b", "elo": max(int(card.get("livello") or 0), b["elo_min"]),
                     "elo_scale": "fide"},
            "verdict": {"bands": bands}, "must_say": must, "must_not": []}


def summarize(results: list[dict]) -> dict:
    """Totals over the positions: verdict, key moves, themes, V12, cost."""
    runs = [(p, r) for p in results for r in p["runs"] if not r.get("failed")]
    moves = [v for p, r in runs for k, v in r["key_points"].items() if k.startswith("mossa_")]
    themes = [v for p, r in runs for k, v in r["key_points"].items() if k.startswith("tema_")]
    return {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "positions": len(results), "runs": len(runs),
            "failed": sum(p["failed"] for p in results),
            "verdict": sum(r["verdict"] for _, r in runs),
            "key_moves": [sum(moves), len(moves)], "themes": [sum(themes), len(themes)],
            "v12_zero": sum(r["v12_final"] == 0 for _, r in runs),
            "cost_usd": _mean([r["cost_usd"] for _, r in runs])}


def report(summary: dict, results: list[dict]) -> str:
    def pct(a, n):
        return f"{round(100 * a / n)} %" if n else "–"
    n = summary["runs"]
    km, th = summary["key_moves"], summary["themes"]
    lines = ["# Banco di utilità sulle schede dei libri", "",
             f"{summary['positions']} posizioni «verifica», {n} analisi riuscite, {summary['failed']} fallite.", "",
             "| Misura | Risultato |", "| --- | --- |",
             f"| Verdetto nelle bande del giudizio del libro | {summary['verdict']}/{n} ({pct(summary['verdict'], n)}) |",
             f"| Mosse chiave del libro citate | {km[0]}/{km[1]} ({pct(*km)}) |",
             f"| Temi del libro nominati | {th[0]}/{th[1]} ({pct(*th)}) |",
             f"| Analisi senza frasi false (V12) | {summary['v12_zero']}/{n} |",
             f"| Costo medio | {summary['cost_usd']:.4f} $ |" if summary["cost_usd"] is not None else "| Costo medio | – |",
             "", "## Per posizione", "", "| Scheda | Verdetto | Mosse chiave | Temi |", "| --- | --- | --- | --- |"]
    for p in results:
        r = next((x for x in p["runs"] if not x.get("failed")), None)
        if r is None:
            lines.append(f"| {p['position']} | fallita | | |")
            continue
        mv = [k[6:] for k, v in r["key_points"].items() if k.startswith("mossa_") and not v]
        tm = [k[5:] for k, v in r["key_points"].items() if k.startswith("tema_") and not v]
        lines.append(f"| {p['position']} | {'sì' if r['verdict'] else 'no'} | "
                     f"{'tutte' if not mv else 'mancano ' + ', '.join(mv)} | {'tutti' if not tm else 'mancano ' + ', '.join(tm)} |")
    return "\n".join(lines) + "\n"


def verification_cards(books_dir) -> list[dict]:
    out = []
    for book, card, _ in books.read_cards(books_dir):
        if book != "catalogo" and card is not None and card.get("split") == "verifica":
            card["libro"] = book
            out.append(card)
    return out
