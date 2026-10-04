"""Calibration report (M5): ``chessanalyst calibrate --fit`` → ``docs/CALIBRATION_REPORT.md`` and
``fixtures/calibration/fit.json`` (the numbers of the report, read by the tests)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from chessanalyst.config import BAND_KEYS, Config
from chessanalyst.calibration import fit as F

REPORT_FILE = Path("docs/CALIBRATION_REPORT.md")
FIT_FILE = Path("fixtures/calibration/fit.json")


def compute(cfg: Config) -> dict[str, Any]:
    recs = F.read_annotations(cfg)
    if any("maia_top" not in r for r in recs):           # older records: from the stored packs
        tops = F.maia_tops(cfg)
        for r in recs:
            r.setdefault("maia_top", tops.get(r["id"]))
    fitc = cfg.calibration["fit"]
    grid = F.grid_t(cfg, recs)
    base = F.evaluate_t(cfg, recs, 1.0, 1.0, 0.0)
    best = grid[0]
    gain = (best["mean_auc"] or 0) - (base["mean_auc"] or 0)
    adopt = gain >= fitc["min_auc_gain"]
    chosen = best if adopt else base
    data = {
        "positions": len(recs),
        "by_band": {b: sum(r["band"] == b for r in recs) for b in BAND_KEYS},
        "errors_by_band": {b: sum(F.error_event(cfg, r) for r in recs if r["band"] == b) for b in BAND_KEYS},
        "played_cost_by_band": {b: round(mean([r["played"][0]["cost_cp"] for r in recs if r["band"] == b] or [0]), 1)
                                for b in BAND_KEYS},
        "error_categories": dict(Counter(t for r in recs for p in r["played"]
                                         if p["cost_cp"] >= fitc["error_cp"] for t in p["tags"])),
        "t_baseline": base, "t_best": best, "t_gain": round(gain, 4), "t_adopted": adopt,
        "t_top5": grid[:5],
        "bins_baseline": F.t_bins(cfg, recs),
        "bins_chosen": F.t_bins(cfg, recs, chosen["theta_scale"], chosen["k_scale"], chosen["w_delta"]),
        "selection": {},
    }
    for band in BAND_KEYS:
        bp = cfg.thresholds.band_params[band]
        cur = F.evaluate_selection(cfg, recs, band, bp.A, bp.L_max)
        scores = F.grid_selection(cfg, recs, band, fitc["a_values"], fitc["l_max_values"])
        ok = [s for s in scores if s.best_in >= cur.best_in]
        top = max(ok, key=lambda s: (s.coverage, -abs(s.A - bp.A), -abs(s.L_max - bp.L_max)))
        data["selection"][band] = {"current": cur.__dict__, "best": top.__dict__,
                                   "grid": [s.__dict__ for s in scores]}
    return data


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.0f}%"


def render(cfg: Config, d: dict[str, Any]) -> str:
    fitc = cfg.calibration["fit"]
    src = cfg.calibration["source"]
    L = [
        "# Relazione di calibrazione (M5)", "",
        f"Campione: {d['positions']} posizioni da partite rapid valutate del database aperto di Lichess "
        f"({src['month']}), {cfg.calibration['sample']['per_band']} per fascia del giocatore al tratto; "
        f"annotazione automatica con Stockfish e Maia-2 (profilo `{cfg.calibration['annotate']['profile']}`). "
        f"Errore = una delle {cfg.calibration['annotate']['own_moves']} mosse successive del giocatore perde almeno "
        f"{fitc['error_cp']} cp.", "",
        "## Campione", "",
        "| Fascia | Posizioni | Con un errore | Costo medio della mossa giocata (cp) |",
        "| --- | --- | --- | --- |",
    ]
    for b in BAND_KEYS:
        L.append(f"| {b} | {d['by_band'][b]} | {d['errors_by_band'][b]} | {d['played_cost_by_band'][b]} |")
    cats = ", ".join(f"{k} {v}" for k, v in sorted(d["error_categories"].items(), key=lambda x: -x[1]))
    L += ["", f"Categorie degli errori (tag della confutazione): {cats or 'nessuna'}.", "",
          "## Tranquillità T (θ, k_c, w_c)", "",
          "Misura: AUC di 100 − T nel prevedere un errore della categoria (0,5 = nessuna capacità, 1 = perfetta), "
          f"media sulle categorie con almeno {fitc['min_events']} errori.", "",
          "| Parametri | AUC media | Per categoria |", "| --- | --- | --- |"]
    def row(label, r):
        per = ", ".join(f"{c} {v['auc']:.2f} ({v['events']})" for c, v in r["per_category"].items()
                        if v["auc"] is not None)
        return f"| {label} | {r['mean_auc']} | {per or '—'} |"
    L.append(row("attuali (θ × 1, k × 1, w + 0)", d["t_baseline"]))
    for r in d["t_top5"]:
        L.append(row(f"θ × {r['theta_scale']}, k × {r['k_scale']}, w {r['w_delta']:+}", r))
    L += ["", (f"**Adottato** il migliore (guadagno {d['t_gain']:+.3f} ≥ {fitc['min_auc_gain']})." if d["t_adopted"]
               else f"**Valori attuali mantenuti**: il guadagno del migliore ({d['t_gain']:+.3f}) è sotto la soglia "
                    f"{fitc['min_auc_gain']}."), "",
          "Tasso di errore per banda di T (tutte le categorie insieme, una riga per posizione e categoria):", "",
          "| Banda di T | Righe | Errori | Tasso (attuali) | Tasso (scelti) |", "| --- | --- | --- | --- | --- |"]
    for a, b in zip(d["bins_baseline"], d["bins_chosen"]):
        L.append(f"| {a['band']} | {a['n']} | {a['errors']} | {_pct(a['rate'])} | {_pct(b['rate'])} |")
    L += ["", "## Selezione delle candidate (A, L_max)", "",
          "Misura: quota di posizioni in cui la mossa giocata è tra le candidate spiegate, con la migliore di "
          "Stockfish sempre tra le spiegate quanto con i valori attuali.", "",
          "| Fascia | Attuali (A, L_max) | Copertura | Migliore della griglia | Copertura |",
          "| --- | --- | --- | --- | --- |"]
    for b, s in d["selection"].items():
        c, t = s["current"], s["best"]
        L.append(f"| {b} | {c['A']}, {c['L_max']} | {_pct(c['coverage'])} | {t['A']}, {t['L_max']} | {_pct(t['coverage'])} |")
    return "\n".join(L) + "\n"


def write_report(cfg: Config) -> Path:
    d = compute(cfg)
    (cfg.project_root / FIT_FILE).write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    path = cfg.project_root / REPORT_FILE
    path.write_text(render(cfg, d), encoding="utf-8")
    return path
