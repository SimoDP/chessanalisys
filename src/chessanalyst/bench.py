"""Bench (OQ-BENCH): frozen packs of real positions with the points the analysis must make.

``fixtures/bench/<id>.yaml`` holds the position (FEN, colour, Elo), the expected verdict (bands of N1), the key
points (``must_say``: terms that must appear in one section, as cited IDs, moves or words; ``any`` = one of) and the forbidden
verdict words (``must_not``). ``<id>.pack.json`` next to it (or ``pack:``) is the frozen pack: the bench runs only
the model, verification and render, never the engines.

``chessanalyst bench --freeze`` builds the missing packs with the engines (``calibration.yaml: bench.freeze``).
``chessanalyst bench [--model X] [--runs N]`` writes ``docs/bench/<date>.json`` and ``….md`` with, per position
and run: verdict correct, key points present, final V12 errors, analysis complete, words, cost; and the
comparison with the previous bench.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from chessanalyst.config import Config
from chessanalyst.errors import ModelError, UsageError
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.position import Position
from chessanalyst.verify.tokens import TOKEN_RE, clean_san, TokenSyntaxError, parse_token


def bench_cfg(cfg: Config) -> dict[str, Any]:
    return cfg.calibration["bench"]


def spec_path(cfg: Config, name: str) -> Path:
    return cfg.project_root / bench_cfg(cfg)["dir"] / f"{name}.yaml"


def load_spec(cfg: Config, name: str) -> dict[str, Any]:
    spec = yaml.safe_load(spec_path(cfg, name).read_text(encoding="utf-8"))
    spec.setdefault("id", name)
    return spec


def pack_file(cfg: Config, spec: dict[str, Any]) -> Path:
    return cfg.resolve_path(spec.get("pack") or f"{bench_cfg(cfg)['dir']}/{spec['id']}.pack.json")


def load_pack(cfg: Config, spec: dict[str, Any]) -> dict:
    return json.loads(pack_file(cfg, spec).read_text(encoding="utf-8"))


# --- freezing the packs (engines) --------------------------------------------


def freeze_packs(cfg: Config, analyzer, maia, openings, *, tablebase=None, force: bool = False,
                 progress: Callable[[str], None] = print) -> list[Path]:
    """Packs of the bench positions that have a FEN and no frozen pack yet (all of them with ``force``)."""
    from chessanalyst.pipeline import analyse_position, resolve_settings

    fz = bench_cfg(cfg)["freeze"]
    written = []
    for name in bench_cfg(cfg)["positions"]:
        spec = load_spec(cfg, name)
        out = pack_file(cfg, spec)
        if "fen" not in spec or (out.is_file() and not force):
            continue
        progress(f"== {name} · profilo {fz['profile']} · dettaglio {fz['detail']}")
        pos = Position(board=parse_fen(spec["fen"], cfg.wording["errors"]), source="fen")
        u = spec["user"]
        us = resolve_settings(cfg, u["color"], u["elo"], u.get("elo_scale", "fide"), u.get("opp_elo"),
                              fz["profile"], fz["detail"])
        pack = analyse_position(cfg, pos, us, analyzer, maia, openings, tablebase=tablebase,
                                progress=lambda m: progress(f"   {m}"))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(pack.model_dump_json(indent=2) + "\n", encoding="utf-8")
        written.append(out)
    return written


def rescore_packs(cfg: Config, policy, progress: Callable[[str], None] = print) -> list[Path]:
    """Category Scoring Engine again on every bench pack (``rescore_pack``, Maia-2 only, no Stockfish), written
    to ``bench.dir``: a pack taken from elsewhere (``pack:``) is copied there and the spec must drop ``pack:``."""
    from chessanalyst.pack.builder import rescore_pack

    written = []
    for name in bench_cfg(cfg)["positions"]:
        spec = load_spec(cfg, name)
        old = load_pack(cfg, spec)
        new = rescore_pack(cfg, old, policy)
        out = cfg.project_root / bench_cfg(cfg)["dir"] / f"{name}.pack.json"
        if new != old or out != pack_file(cfg, spec):
            progress(f"{name}: categorie ricalcolate")
            out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            written.append(out)
    return written


# --- what the document says --------------------------------------------------


def move_index(pack: dict) -> dict[str, tuple[str, str]]:
    """Citable ID → (SAN, node where the move is played)."""
    parent = {n["id"]: n["parent"] for n in pack["nodes"]}
    idx: dict[str, tuple[str, str]] = {}
    eng = pack["engine"]
    for c in eng.get("candidates", []):
        idx[c["id"]] = (clean_san(c["san"]), parent.get(c.get("node")) or pack["nodes"][0]["id"])
    for r in eng.get("replies", []):
        idx[r["id"]] = (clean_san(r["san"]), parent.get(r.get("node")) or pack["nodes"][0]["id"])
        for u in r.get("user_best", []):
            idx[u["id"]] = (clean_san(u["san"]), r.get("node"))
    return idx


def _token_moves(raw: str, idx: dict[str, tuple[str, str]]) -> tuple[set[str], set[tuple[str, str]]]:
    """(IDs, (SAN, node) moves) cited by one token."""
    try:
        t = parse_token(raw)
    except TokenSyntaxError:
        return set(), set()
    ids, moves = set(), set()
    if t.ref:
        ids.add(t.ref)
        if t.ref in idx:
            moves.add(idx[t.ref])
    if t.san and t.node:
        moves.add((t.san, t.node))
    if t.kind == "plan" and t.moves:
        moves.add((clean_san(t.moves[0]), t.node))
    if t.squares:
        ids.add(f"diag:{t.squares[0]}-{t.squares[1]}")
    return ids, moves


def _paragraphs(block: dict) -> list[dict]:
    """Paragraph, list items and line caption of one block (each with text, source, assertions)."""
    if block.get("text"):
        return [block]
    return list(block.get("items") or []) + ([block["caption"]] if block.get("caption") else [])


def section_texts(output: dict) -> dict[str, str]:
    """Text of every section of the final output (paragraphs and list items, tokens included)."""
    out = {}
    for s in output.get("sections", []):
        parts = []
        for b in s.get("blocks", []):
            parts += [p["text"] for p in _paragraphs(b)]
        out[s["id"]] = "\n".join(parts)
    return out


def _term_ok(term: dict, text: str, ids: set[str], moves: set[tuple[str, str]]) -> bool:
    if "any" in term:
        return any(_term_ok(t, text, ids, moves) for t in term["any"])
    if "ref" in term:
        return term["ref"] in ids
    if "move" in term:
        return any(san == clean_san(term["move"]) and term.get("node") in (None, node) for san, node in moves)
    if "text" in term:
        return re.search(term["text"], TOKEN_RE.sub(" ", text), re.IGNORECASE) is not None
    raise UsageError(f"Termine del banco di prova non riconosciuto: {term}")


def key_points(spec: dict, pack: dict, output: dict) -> dict[str, bool]:
    """A key point is present when one section contains all its terms."""
    idx = move_index(pack)
    per_section = []
    for text in section_texts(output).values():
        ids, moves = set(), set()
        for raw in (m.group(0) for m in TOKEN_RE.finditer(text)):
            i, mv = _token_moves(raw, idx)
            ids |= i
            moves |= mv
        per_section.append((text, ids, moves))
    return {k["id"]: any(all(_term_ok(t, *sec) for t in k["all"]) for sec in per_section)
            for k in spec.get("must_say", [])}


def verdict_ok(cfg: Config, spec: dict, output: dict) -> tuple[bool, list[str]]:
    """The verdict section states one of the expected bands of N1 and none of the forbidden words."""
    sec_id = cfg.verify["v12"]["verdict"]["section"]
    sec = next((s for s in output.get("sections", []) if s["id"] == sec_id), None)
    if sec is None:
        return False, []
    root = spec.get("verdict", {}).get("node", "N1")
    bands = {a.get("band") for b in sec.get("blocks", []) for p in _paragraphs(b)
             for a in p.get("assertions") or [] if a.get("kind") == "eval_band" and a.get("ref") == root}
    text = TOKEN_RE.sub(" ", section_texts(output).get(sec_id, ""))
    said = [w for w in spec.get("must_not", []) if re.search(w, text, re.IGNORECASE)]
    return bool(bands & set(spec["verdict"]["bands"])) and not said, said


def score_run(cfg: Config, spec: dict, pack: dict, verification: dict | None, output: dict | None,
              seconds: float, error: str | None = None) -> dict[str, Any]:
    if verification is None or output is None:
        return {"failed": error, "passed": False, "seconds": round(seconds, 1)}
    last = verification["attempts"][-1]["errors"]
    v12 = sum(1 for e in last if e["code"] == "V12")
    ok, said = verdict_ok(cfg, spec, output)
    kp = key_points(spec, pack, output)
    words = sum(w["actual"] for w in verification["words_by_section"].values())
    complete = not last
    run = {"verdict": ok, "forbidden_said": said, "key_points": kp, "v12_final": v12, "complete": complete,
           "words": words, "attempts": len(verification["attempts"]),
           "final_errors": sorted({e["code"] for e in last}),
           "cost_usd": (verification.get("usage") or {}).get("cost_usd"),
           "input_tokens": (verification.get("usage") or {}).get("input_tokens"),
           "seconds": round(seconds, 1)}
    run["passed"] = ok and all(kp.values()) and v12 == 0 and complete
    return run


# --- running -------------------------------------------------------------------


def run_bench(cfg: Config, client: Any, *, runs: int | None = None, positions: list[str] | None = None,
              progress: Callable[[str], None] = print, clock: Callable[[], float] = time.monotonic) -> dict:
    from chessanalyst.llm.cycle import run_model

    bc = bench_cfg(cfg)
    runs = runs or bc["runs"]
    out = []
    for name in positions or bc["positions"]:
        spec, per = load_spec(cfg, name), []
        pack = load_pack(cfg, spec)
        for k in range(runs):
            progress(f"{name} · giro {k + 1}/{runs} …")
            t0 = clock()
            try:
                res = run_model(cfg, pack, client)
                per.append(score_run(cfg, spec, pack, res.verification, res.output, clock() - t0))
            except ModelError as e:
                per.append(score_run(cfg, spec, pack, None, None, clock() - t0, str(e)))
        out.append(aggregate(name, spec, per))
    return {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": client.model,
            "config_hash": cfg.config_hash, "runs": runs, "document": cfg.default.llm.document,
            "positions": out}


def _mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 5) if xs else None


def aggregate(name: str, spec: dict, runs: list[dict]) -> dict:
    ok = [r for r in runs if not r.get("failed")]
    keys = [k["id"] for k in spec.get("must_say", [])]
    return {
        "position": name, "n": len(runs), "runs": runs,
        "passed": sum(1 for r in runs if r["passed"]),
        "verdict": sum(1 for r in ok if r["verdict"]),
        "key_points": {k: sum(1 for r in ok if r["key_points"].get(k)) for k in keys},
        "all_key_points": sum(1 for r in ok if all(r["key_points"].values())),
        "v12_zero": sum(1 for r in ok if r["v12_final"] == 0),
        "complete": sum(1 for r in ok if r["complete"]),
        "failed": len(runs) - len(ok),
        "words": _mean([r["words"] for r in ok]),
        "cost_usd": _mean([r["cost_usd"] for r in ok]),
        "input_tokens": _mean([r["input_tokens"] for r in ok]),
        "seconds": _mean([r["seconds"] for r in runs]),
    }


def goal_reached(cfg: Config, summary: dict) -> tuple[bool, float | None]:
    goal = bench_cfg(cfg)["goal"]
    need = goal["min_passing_runs"] * summary["runs"] / bench_cfg(cfg)["runs"]
    cost = _mean([r.get("cost_usd") for p in summary["positions"] for r in p["runs"]])
    ok = all(p["passed"] >= need for p in summary["positions"])
    return ok and cost is not None and cost <= goal["max_mean_cost_usd"], cost


# --- report --------------------------------------------------------------------


def _cell(p: dict) -> str:
    n = p["n"]
    kp = " ".join(f"{k} {v}/{n}" for k, v in p["key_points"].items())
    return (f"superati {p['passed']}/{n} · verdetto {p['verdict']}/{n} · punti chiave {p['all_key_points']}/{n} "
            f"({kp}) · V12 zero {p['v12_zero']}/{n} · complete {p['complete']}/{n}"
            + (f" · falliti {p['failed']}" if p["failed"] else "")
            + (f" · parole {p['words']:.0f}" if p["words"] is not None else "")
            + (f" · costo {p['cost_usd']:.4f} $" if p["cost_usd"] is not None else "")
            + (f" · {p['seconds']:.0f} s" if p["seconds"] is not None else ""))


def _totals(cfg: Config, s: dict) -> str:
    ok, cost = goal_reached(cfg, s)
    n = sum(p["n"] for p in s["positions"])
    passed = sum(p["passed"] for p in s["positions"])
    words = _mean([p["words"] for p in s["positions"]])
    tokens = _mean([p["input_tokens"] for p in s["positions"]])
    return (f"{passed} giri superati su {n}"
            + (f", parole medie {words:.0f}" if words is not None else "")
            + (f", token in ingresso medi {tokens:.0f}" if tokens is not None else "")
            + (f", costo medio {cost:.4f} $" if cost is not None else "")
            + f" · traguardo {'raggiunto' if ok else 'non raggiunto'}")


def compare(cfg: Config, new: dict, old: dict | None) -> str:
    goal = bench_cfg(cfg)["goal"]
    head = [f"# Banco di prova — {new['created_utc']}", "",
            f"Modello: `{new['model']}` · documento {new.get('document', 'sections')}"
            + (f" · chiamate {new['calls']}" if "calls" in new else "")
            + f" · config_hash `{new['config_hash']}` · {new['runs']} giri per posizione"
            + (f" · confronto con il {old['created_utc']}" if old else " · primo riferimento"), "",
            f"Traguardo (OQ-BENCH): su ogni posizione almeno {goal['min_passing_runs']} giri su "
            f"{bench_cfg(cfg)['runs']} con verdetto corretto, tutti i punti chiave, zero errori V12 finali e "
            f"analisi completa; costo medio fino a {goal['max_mean_cost_usd']} $.", "",
            "| Posizione | Prima | Adesso |", "| --- | --- | --- |"]
    if old:                                   # a partial bench (--position) is compared on its positions only
        names = {p["position"] for p in new["positions"]}
        old = dict(old, positions=[p for p in old["positions"] if p["position"] in names])
    prev = {p["position"]: p for p in (old or {}).get("positions", [])}
    rows = [f"| {p['position']} | {_cell(prev[p['position']]) if p['position'] in prev else '—'} | {_cell(p)} |"
            for p in new["positions"]]
    tot = [""] + ([f"- Prima: {_totals(cfg, old)}"] if old else []) + [f"- Adesso: {_totals(cfg, new)}"]
    return "\n".join(head + rows + tot) + "\n"


def write_bench(cfg: Config, summary: dict) -> tuple[Path, Path]:
    d = cfg.project_root / bench_cfg(cfg)["out_dir"]
    d.mkdir(parents=True, exist_ok=True)
    olds = sorted(d.glob("*.json"))
    old = json.loads(olds[-1].read_text(encoding="utf-8")) if olds else None
    stamp = summary["created_utc"].replace(":", "").replace("-", "")[:15]
    j, m = d / f"{stamp}.json", d / f"{stamp}.md"
    j.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    m.write_text(compare(cfg, summary, old), encoding="utf-8")
    return j, m
