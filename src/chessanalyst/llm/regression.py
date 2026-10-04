"""Prompt regression (§12.2, M5): «ogni modifica a prompt o schema si rilancia sulle fixture e si confrontano i
rapporti».

``chessanalyst regression`` runs the model on the frozen packs listed in ``calibration.yaml: regression.packs``,
writes a summary (errors per attempt by code, retries, removed and marked items, words against the budgets,
theory share) to ``docs/regression/<date>.json`` and a comparison with the previous summary to ``….md``.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chessanalyst.config import Config
from chessanalyst.errors import ModelError
from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.cycle import run_model


def summarize(name: str, verification: dict[str, Any] | None, retries: int, error: str | None = None) -> dict:
    if verification is None:
        return {"pack": name, "failed": error}
    words = verification["words_by_section"]
    off = sum(1 for w in words.values() if w["budget"] and abs(w["actual"] - w["budget"]) > 0.25 * w["budget"])
    return {
        "pack": name,
        "attempts": [dict(Counter(e["code"] for e in a["errors"])) for a in verification["attempts"]],
        "retries": retries,
        "complete": not verification["attempts"][-1]["errors"],
        "removed": len(verification["final"]["removed"]),
        "marked": len(verification["final"]["marked"]),
        "sections_off_budget": off,
        "theory_share": verification["theory_share"],
    }


def run_regression(cfg: Config, client: Any, progress: Callable[[str], None] = print) -> dict[str, Any]:
    out = []
    for name in cfg.calibration["regression"]["packs"]:
        progress(f"{name} …")
        try:
            res = run_model(cfg, load_frozen_pack(cfg, name), client)
            out.append(summarize(name, res.verification, res.retries))
        except ModelError as e:
            out.append(summarize(name, None, 0, str(e)))
    return {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": client.model,
            "config_hash": cfg.config_hash, "packs": out}


def _line(s: dict) -> str:
    if s.get("failed"):
        return "nessuna risposta valida"
    att = " → ".join(str(sum(a.values())) for a in s["attempts"])
    return (f"errori {att} · {'completa' if s['complete'] else 'degradata'} · rimossi {s['removed']} · "
            f"marcati {s['marked']} · sezioni fuori budget {s['sections_off_budget']}")


def compare(new: dict, old: dict | None) -> str:
    rows = ["| Pacchetto | Prima | Adesso |", "| --- | --- | --- |"]
    prev = {p["pack"]: p for p in (old or {}).get("packs", [])}
    for p in new["packs"]:
        rows.append(f"| {p['pack']} | {_line(prev[p['pack']]) if p['pack'] in prev else '—'} | {_line(p)} |")
    head = [f"# Regressione del prompt — {new['created_utc']}", "",
            f"Modello: `{new['model']}` · config_hash `{new['config_hash']}`"
            + (f" · confronto con il {old['created_utc']}" if old else " · primo riferimento"), ""]
    totals = []
    for label, data in (("Prima", old), ("Adesso", new)):
        if data:
            ps = data["packs"]
            totals.append(f"- {label}: {sum(1 for p in ps if p.get('complete'))} complete su {len(ps)}, "
                          f"{sum(p.get('removed', 0) for p in ps)} rimozioni")
    return "\n".join(head + rows + [""] + totals) + "\n"


def write_regression(cfg: Config, summary: dict) -> tuple[Path, Path]:
    d = cfg.project_root / cfg.calibration["regression"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    olds = sorted(d.glob("*.json"))
    old = json.loads(olds[-1].read_text(encoding="utf-8")) if olds else None
    stamp = summary["created_utc"].replace(":", "").replace("-", "")[:15]
    j, m = d / f"{stamp}.json", d / f"{stamp}.md"
    j.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    m.write_text(compare(summary, old), encoding="utf-8")
    return j, m
