"""Fit of the numbers on the annotated positions (M5), without engines.

T calibration (§5-bis.4, «una T alta non deve precedere errori frequenti a quel livello, e viceversa»): for
every combination of θ (scale of the band thresholds), k_c (common scale) and w_c (common shift), T of the
user is recomputed from the stored lines and static parts; the score of a category is the AUC of 100 − T in
predicting an error of the player (one of their next moves losing at least ``error_cp``) whose refutation has
the tag of the category. The objective is the mean AUC over the categories with at least ``min_events``
errors.

Selection (§3-ter.3): for A and L_max per band the explained candidates are recomputed from the stored root
rows; the measure is how often the move actually played is among them, with the best move of Stockfish
always among them. B (weight of complexity in the recommendation) has no ground truth in game data and is not
fitted (M5_REPORT).
"""

from __future__ import annotations

import itertools
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chessanalyst.config import Config
from chessanalyst.explore.select import BandSel, RootRow, select_candidates

ANNOTATIONS_FILE = Path("fixtures/calibration/annotations.jsonl")
PACKS_DIR = Path("data/calibration/packs")


def read_annotations(cfg: Config) -> list[dict[str, Any]]:
    path = cfg.project_root / ANNOTATIONS_FILE
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# -- T ---------------------------------------------------------------------------------------------------------


def user_t(cfg: Config, rec: dict, cat: str, theta_scale: float, k_scale: float, w_delta: float) -> float:
    """T of the user for one category, as in scoring/categories.py, with the scaled parameters."""
    sc = cfg.thresholds.scoring
    me = rec["side"]
    theta = sc.theta[rec["band"]] * theta_scale
    kept = [ln for ln in rec["lines"]
            if ln["risk"] >= theta or ln["mate"] or ln["impact_cp"] >= sc.decisive_cp]
    mine = [ln for ln in kept if cat in ln["tags"] and ln["defender"] == me]
    t_dyn = 100.0 * math.exp(-sum(ln["risk"] for ln in mine) / (sc.k[cat] * k_scale))
    w = min(1.0, max(0.0, sc.w[cat] + w_delta))
    t = w * t_dyn + (1 - w) * rec["t_stat"][cat][me]
    if any((ln["mate"] or ln["impact_cp"] >= sc.decisive_cp) and ln["p_att"] >= sc.override.p_att_min
           and ln["primary"] == cat for ln in mine):
        t = min(t, sc.override.t_max)
    return t


def error_event(cfg: Config, rec: dict, cat: str | None = None) -> bool:
    e = cfg.calibration["fit"]["error_cp"]
    return any(p["cost_cp"] >= e and (cat is None or cat in p["tags"]) for p in rec["played"])


def auc(scores: list[float], labels: list[bool]) -> float | None:
    """Probability that a random positive scores higher than a random negative (ties count one half)."""
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def t_categories(cfg: Config) -> list[str]:
    return [c for c in cfg.thresholds.scoring.categories if c != "practical_complexity"]


def evaluate_t(cfg: Config, recs: list[dict], theta_scale: float, k_scale: float, w_delta: float) -> dict[str, Any]:
    fit = cfg.calibration["fit"]
    per_cat = {}
    for cat in t_categories(cfg):
        labels = [error_event(cfg, r, cat) for r in recs]
        if sum(labels) < fit["min_events"]:
            continue
        scores = [100 - user_t(cfg, r, cat, theta_scale, k_scale, w_delta) for r in recs]
        per_cat[cat] = {"auc": auc(scores, labels), "events": sum(labels)}
    vals = [v["auc"] for v in per_cat.values() if v["auc"] is not None]
    return {"theta_scale": theta_scale, "k_scale": k_scale, "w_delta": w_delta, "per_category": per_cat,
            "mean_auc": round(sum(vals) / len(vals), 4) if vals else None}


def grid_t(cfg: Config, recs: list[dict]) -> list[dict[str, Any]]:
    fit = cfg.calibration["fit"]
    out = [evaluate_t(cfg, recs, a, b, c)
           for a, b, c in itertools.product(fit["theta_scale"], fit["k_scale"], fit["w_delta"])]
    return sorted(out, key=lambda r: (-(r["mean_auc"] or 0), abs(math.log(r["theta_scale"])) + abs(math.log(r["k_scale"]))
                                      + abs(r["w_delta"])))


def t_bins(cfg: Config, recs: list[dict], theta_scale: float = 1.0, k_scale: float = 1.0,
           w_delta: float = 0.0) -> list[dict[str, Any]]:
    """Error rate of the player by band of T (all categories pooled, one row per position and category)."""
    edges = cfg.calibration["fit"]["t_bins"]
    rows: Counter = Counter()
    errs: Counter = Counter()
    for r in recs:
        for cat in t_categories(cfg):
            t = user_t(cfg, r, cat, theta_scale, k_scale, w_delta)
            b = sum(t >= e for e in edges)
            rows[b] += 1
            errs[b] += error_event(cfg, r, cat)
    labels = [f"< {edges[0]}"] + [f"{lo}–{hi}" for lo, hi in zip(edges, edges[1:])] + [f">= {edges[-1]}"]
    return [{"band": labels[b], "n": rows[b], "errors": errs[b],
             "rate": round(errs[b] / rows[b], 3) if rows[b] else None} for b in range(len(labels))]


# -- selection (A, L_max) ----------------------------------------------------------------------------------------


def maia_tops(cfg: Config) -> dict[str, str | None]:
    """Maia-2's top move at the root of every annotated position, from the stored packs (not versioned)."""
    out = {}
    for f in sorted((cfg.project_root / PACKS_DIR).glob("*.pack.json")):
        pol = json.loads(f.read_text(encoding="utf-8"))["nodes"][0]["maia"]["policy"]
        out[f.name.split(".")[0]] = pol[0]["uci"] if pol else None
    return out


def selection(rec: dict, bp: BandSel) -> list[str]:
    e0 = [RootRow(c["san"], c["uci"], c["eval_user_cp"], "e0", c["e0_rank"], c["p_user"])
          for c in rec["candidates"] if c["source"] == "e0"]
    e4 = [RootRow(c["san"], c["uci"], c["eval_user_cp"], "e4", None, c["p_user"])
          for c in rec["candidates"] if c["source"] == "e4"]
    policy = {c["uci"]: c["p_user"] for c in rec["candidates"]}
    if rec.get("maia_top") and rec["maia_top"] not in policy:
        policy[rec["maia_top"]] = max(policy.values(), default=0.0) + 1e-6   # unevaluated top (warning in the app)
    return select_candidates(e0, e4, policy, bp).explained


@dataclass
class SelScore:
    A: float
    L_max: int
    coverage: float           # played move among the explained
    best_in: float            # best move of Stockfish among the explained
    n: int


def evaluate_selection(cfg: Config, recs: list[dict], band: str, A: float, L_max: int) -> SelScore:
    bp0 = cfg.thresholds.band_params[band]
    bp = BandSel(bp0.K, bp0.explained_min, bp0.listed_max, L_max, A)
    rs = [r for r in recs if r["band"] == band and r["candidates"]]
    cov = best = 0
    for r in rs:
        ex = selection(r, bp)
        cov += r["played"][0]["uci"] in ex
        top = min(r["candidates"], key=lambda c: (-c["eval_user_cp"], c["e0_rank"] or 99))
        best += top["uci"] in ex
    n = len(rs) or 1
    return SelScore(A, L_max, round(cov / n, 3), round(best / n, 3), len(rs))


def grid_selection(cfg: Config, recs: list[dict], band: str, As: list[float], Ls: list[int]) -> list[SelScore]:
    return [evaluate_selection(cfg, recs, band, a, lm) for a in As for lm in Ls]
