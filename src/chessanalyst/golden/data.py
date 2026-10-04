"""``chessanalyst golden --data`` (§8-bis.4, M0).

1. Analyses the Najdorf root, the null move, the nodes after 6.Be3/Be2/Bg5/f4
   and the move-order nodes quoted by the raws with the ``deep`` profile
   parameters → ``fixtures/golden_nodes.json``. Moves quoted by the raws but
   absent from a node's MultiPV are evaluated with one restricted search
   (``root_moves``, as E2c does) stored as ``extra``.
2. Queries Maia-2 at the root and in those nodes (null move excluded, §3.2)
   for 1500, 1900 and 2400 FIDE → ``fixtures/golden_maia.json``.
3. Writes ``docs/golden_diff.md``: raw value vs new value for every number of
   the raws, flags > 0,25 and the AC-09 check.
4. Adds the prose word count of the raws per section (first estimate).
5. Copies ``calibration_levels.md`` into ``docs/CALIBRATION_GUIDE.md``.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chess

from chessanalyst import __version__, elo
from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import entropy_bits
from chessanalyst.engines.types import NodeResult
from chessanalyst.golden import raw_claims as rc
from chessanalyst.golden.wordcount import raw_word_counts

log = logging.getLogger(__name__)

ANCHORS = ("1500", "1900", "2400")
RAW_DIR = Path("examples/golden/raw")
NODES_FILE = Path("fixtures/golden_nodes.json")
MAIA_FILE = Path("fixtures/golden_maia.json")
DIFF_FILE = Path("docs/golden_diff.md")
KEEP_MARK = "<!-- keep: M1b -->"   # golden --data rewrites the file but keeps everything from this mark on
GUIDE_FILE = Path("docs/CALIBRATION_GUIDE.md")
GUIDE_INTRO = "Guida qualitativa per chi scrive prompt ed esempi; non normativa oltre §7."


def path_label(path: tuple[str, ...]) -> str:
    """``("Be3", "e5", "Nb3")`` → ``6.Be3 e5 7.Nb3`` (``--`` = null move)."""
    if not path:
        return "radice"
    if path == ("--",):
        return "mossa nulla (tratto al Nero)"
    board = chess.Board(rc.NAJDORF_FEN)
    parts = []
    for san in path:
        if board.turn == chess.WHITE:
            parts.append(f"{board.fullmove_number}.{san}")
        else:
            parts.append(san if parts else f"{board.fullmove_number}...{san}")
        board.push_san(san)
    return " ".join(parts)


def board_at(path: tuple[str, ...]) -> chess.Board:
    board = chess.Board(rc.NAJDORF_FEN)
    for san in path:
        if san == "--":
            board.push(chess.Move.null())
        else:
            board.push_san(san)
    # Fresh board from the FEN: the golden nodes have no relevant history.
    return chess.Board(board.fen(en_passant="legal"))


def node_params(cfg: Config, phase: str, n_phase_nodes: int, time_scale: float) -> dict[str, Any]:
    """``deep`` profile: t_target = share × B / nodes in phase (§3-ter.2)."""
    p = cfg.exploration.profiles["deep"]
    shares = cfg.exploration.phase_shares
    share = getattr(shares, phase)
    t_target = share * p.B_s / n_phase_nodes * time_scale
    if phase in ("E0", "E1"):
        d_min = p.dmin.root
        multipv = p.multipv.root if phase == "E0" else p.multipv.nodes
    else:
        d_min = p.dmin.nodes
        multipv = p.multipv.nodes
    return {"multipv": multipv, "d_min": d_min, "t_target": t_target, "t_cap": t_target * p.node_cap_factor}


def run_engine_nodes(
    cfg: Config, analyzer: CachedAnalyzer, time_scale: float = 1.0,
    progress: Callable[[str], None] = lambda s: None,
) -> dict[str, Any]:
    p = cfg.exploration.profiles["deep"]
    counts: dict[str, int] = {}
    for _, phase in rc.GOLDEN_NODES:
        counts[phase] = counts.get(phase, 0) + 1
    claimed: dict[tuple[str, ...], set[str]] = {}
    for c in rc.CLAIMS:
        if c.move is not None:
            claimed.setdefault(c.path, set()).add(c.move)
    nodes = []
    for i, (path, phase) in enumerate(rc.GOLDEN_NODES, 1):
        board = board_at(path)
        prm = node_params(cfg, phase, counts[phase], time_scale)
        progress(f"[{i}/{len(rc.GOLDEN_NODES)}] {phase} {path_label(path)} · MultiPV {prm['multipv']}"
                 f" · profondità minima {prm['d_min']} · {prm['t_target']:.0f} s")
        res = analyzer.analyse(board, prm["multipv"], prm["t_target"], prm["d_min"], prm["t_cap"])
        entry: dict[str, Any] = {"path": list(path), "label": path_label(path), "phase": phase,
                                 "fen": board.fen(en_passant="legal"), "params": prm,
                                 "result": res.to_dict(), "extra": None}
        missing = sorted(claimed.get(path, set()) - {ln.san for ln in res.lines})
        if missing:
            moves = [board.parse_san(s) for s in missing]
            t = cfg.exploration.e2c_time_factor * node_params(cfg, "E3", counts["E3"], time_scale)["t_target"]
            progress(f"      E2c {', '.join(missing)} · {t:.0f} s")
            extra = analyzer.analyse(board, len(moves), t, p.dmin.pvwalk, t * p.node_cap_factor, root_moves=moves)
            entry["extra"] = extra.to_dict()
        nodes.append(entry)
    return {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "app_version": __version__,
        "profile": "deep",
        "time_scale": time_scale,
        "root_fen": rc.NAJDORF_FEN,
        "nodes": nodes,
    }


def run_maia(cfg: Config, maia: Any, nodes_data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "maia": maia.info(), "anchors": {}}
    for anchor in ANCHORS:
        e = elo.resolve(int(anchor), "fide", cfg)
        rows = []
        for node in nodes_data["nodes"]:
            if node["phase"] == "E1":
                continue  # Maia-2 is not queried on the null-move node (§3.2)
            board = chess.Board(node["fen"])
            t0 = time.monotonic()
            pol = maia.policy(node["fen"], e.maia, e.maia)
            score = maia.expected_score(node["fen"], e.maia, e.maia)
            dt = time.monotonic() - t0
            ranked = sorted(pol.items(), key=lambda kv: (-kv[1], kv[0]))
            rows.append({
                "path": node["path"], "label": node["label"], "fen": node["fen"],
                "elo_self": e.maia, "elo_oppo": e.maia,
                "policy": [{"san": board.san(chess.Move.from_uci(u)), "uci": u, "p": round(p, 4)}
                           for u, p in ranked if p >= 0.001],
                "expected_score_side_to_move": round(score, 4),
                "entropy_bits": round(entropy_bits(pol), 3),
                "time_s": round(dt, 3),
            })
        out["anchors"][anchor] = {"elo_fide": int(anchor), "elo_maia": e.maia,
                                  "bucket": maia.bucket(e.maia), "saturated": maia.saturated(e.maia),
                                  "nodes": rows}
    return out


# --- diff -------------------------------------------------------------------


def _fmt(cp: int | None) -> str:
    if cp is None:
        return "—"
    s = f"{abs(cp) / 100:.2f}".replace(".", ",")
    return "0,00" if cp == 0 else ("+" if cp > 0 else "-") + s


def _node_index(nodes_data: dict[str, Any]) -> dict[tuple[str, ...], dict[str, Any]]:
    out = {}
    for n in nodes_data["nodes"]:
        out[tuple(n["path"])] = {
            "result": NodeResult.from_dict(n["result"]),
            "extra": NodeResult.from_dict(n["extra"]) if n.get("extra") else None,
            "raw": n,
        }
    return out


def claim_value(idx: dict, claim: rc.Claim) -> tuple[int | None, str]:
    """New value (White cp) for a claim and where it comes from."""
    node = idx.get(claim.path)
    if node is None:
        return None, "nodo assente"
    res: NodeResult = node["result"]
    if claim.move is None:
        best = res.best()
        return (best.eval_white_cp, "riga 1") if best else (None, "nessuna riga")
    ln = res.line_for(claim.move)
    if ln is not None:
        return ln.eval_white_cp, f"MultiPV {ln.rank}"
    extra: NodeResult | None = node["extra"]
    if extra is not None:
        ln = extra.line_for(claim.move)
        if ln is not None:
            return ln.eval_white_cp, "ricerca ristretta (E2c)"
    return None, "non valutata"


def ac09(idx: dict) -> dict[str, Any]:
    root: NodeResult = idx[()]["result"]
    ranking = [ln.san for ln in root.lines]
    rows = []
    ok = True
    for san in rc.AC09_TOP3:
        claim = next(c for c in rc.CLAIMS if c.path == () and c.move == san)
        new, _ = claim_value(idx, claim)
        rank = ranking.index(san) + 1 if san in ranking else None
        diff = None if new is None else new - claim.raw_cp
        passed = diff is not None and abs(diff) <= rc.AC09_MAX_DIFF_CP and rank is not None and rank <= rc.AC09_TOP_N
        ok = ok and passed
        rows.append({"move": san, "raw": claim.raw_cp, "new": new, "diff": diff, "rank": rank, "passed": passed})
    return {"passed": ok, "rows": rows}


def write_diff(cfg: Config, nodes_data: dict[str, Any], maia_data: dict[str, Any] | None,
               maia_error: str | None) -> str:
    idx = _node_index(nodes_data)
    word_re = cfg.verify["word"]
    L: list[str] = []
    L.append("# Golden: confronto tra i raw e la nuova esecuzione (M0)")
    L.append("")
    L.append(f"Generato da `chessanalyst golden --data` il {nodes_data['created_utc']} "
             f"(app {nodes_data['app_version']}, profilo `deep`, fattore di tempo {nodes_data['time_scale']}).")
    root = idx[()]["result"]
    L.append(f"Motore: {root.engine_version}. Valori in pedoni dal punto di vista del Bianco (= utente nei raw).")
    L.append("Soglia di segnalazione: scostamento > 0,25 pedoni (⚠).")
    L.append("")

    # AC-09
    a = ac09(idx)
    L.append("## AC-09")
    L.append("")
    L.append(f"Esito: **{'superato' if a['passed'] else 'NON superato'}** "
             f"(le prime 3 candidate dei raw devono differire ≤ 0,25 e restare tra le prime {rc.AC09_TOP_N}).")
    L.append("")
    L.append("| Mossa | Raw | Nuovo | Differenza | Rango nuovo | Esito |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for r in a["rows"]:
        L.append(f"| 6.{r['move']} | {_fmt(r['raw'])} | {_fmt(r['new'])} | {_fmt(r['diff'])} | "
                 f"{r['rank'] or '—'} | {'OK' if r['passed'] else 'NO'} |")
    L.append("")

    # Nodes summary
    L.append("## Nodi analizzati")
    L.append("")
    L.append("| Nodo | Fase | Profondità | MultiPV | Tempo (s) | Instabile | Migliore |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for n in nodes_data["nodes"]:
        res = NodeResult.from_dict(n["result"])
        best = res.best()
        L.append(f"| {n['label']} | {n['phase']} | {res.depth} | {res.multipv} | {res.time_s:.0f} | "
                 f"{'sì' if res.unstable_depth else 'no'} | {best.san if best else '—'} {_fmt(best.eval_white_cp if best else None)} |")
    L.append("")
    root_best = root.best()
    if root_best and root_best.wdl_white:
        L.append(f"WDL alla radice (riga 1): {root_best.wdl_white} per mille; patta {root_best.wdl_white[1] / 10:.0f}% "
                 f"(raw: circa {rc.ROOT_DRAW_PERMILLE / 10:.0f}%).")
        L.append("")

    # Values
    L.append("## Valori numerici dei raw")
    L.append("")
    L.append("| Nodo | Mossa | Raw | Nuovo | Differenza | Fonte del nuovo valore | Raw citati | Nota |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    flagged = 0
    for c in rc.CLAIMS:
        new, src = claim_value(idx, c)
        diff = None if new is None else new - c.raw_cp
        flag = diff is not None and abs(diff) > rc.AC09_MAX_DIFF_CP
        flagged += flag
        L.append(f"| {path_label(c.path)} | {c.move or '(nodo)'} | {_fmt(c.raw_cp)} | {_fmt(new)} | "
                 f"{_fmt(diff)}{' ⚠' if flag else ''} | {src} | {', '.join(c.sources)} | {c.note} |")
    L.append("")
    L.append(f"Valori oltre la soglia: **{flagged}** su {len(rc.CLAIMS)}.")
    L.append("")

    # Best moves
    L.append("## Mossa migliore per nodo")
    L.append("")
    L.append("| Nodo | Migliore nei raw | Migliore ora | Coincide |")
    L.append("| --- | --- | --- | --- |")
    for path, raw_best in rc.BEST_CLAIMS:
        res = idx[path]["result"]
        best = res.best()
        same = best is not None and best.san in raw_best
        L.append(f"| {path_label(path)} | {' / '.join(raw_best)} | {best.san if best else '—'} | {'sì' if same else 'no'} |")
    L.append("")

    # Maia
    L.append("## Maia-2")
    L.append("")
    if maia_data is None:
        L.append(f"**Non eseguito**: {maia_error}. `fixtures/golden_maia.json` non è stato prodotto; "
                 "va rigenerato con `chessanalyst golden --data` su una macchina con i pesi di Maia-2.")
    else:
        info = maia_data["maia"]
        L.append(f"maia2 {info['package_version']}, modello {info['model_type']}, dispositivo {info['device']}.")
        L.append("")
        L.append("| Ancora | Elo Maia | Fascia | Satura | Prime 3 alla radice | Risultato atteso (radice) |")
        L.append("| --- | --- | --- | --- | --- | --- |")
        for anchor, a_data in maia_data["anchors"].items():
            rootrow = next(r for r in a_data["nodes"] if r["path"] == [])
            top = ", ".join(f"{p['san']} {round(p['p'] * 100)}%" for p in rootrow["policy"][:3])
            L.append(f"| {anchor} | {a_data['elo_maia']} | {a_data['bucket']} | {'sì' if a_data['saturated'] else 'no'} | "
                     f"{top} | {rootrow['expected_score_side_to_move']:.2f} |")
    L.append("")

    # Word counts
    L.append("## Parole di prosa dei raw (prima stima, §9-bis.8)")
    L.append("")
    L.append("Escluse tabelle numeriche, righe `[MAIA]`, titoli, commenti e nota di stato; le tabelle di solo testo "
             "contano cella per cella. Budget = `prose_words` della fascia dell'Elo dell'ancora (dettaglio 4).")
    L.append("")
    L.append("| Raw | Sezioni (parole) | Totale | `prose_words` della fascia |")
    L.append("| --- | --- | --- | --- |")
    for anchor in ANCHORS:
        path = cfg.project_root / RAW_DIR / f"najdorf_w_{anchor}.md"
        counts = raw_word_counts(path, word_re)
        band = elo.band_of(int(anchor), cfg)
        budget = cfg.thresholds.band_params[band].prose_words
        per = ", ".join(f"{k} {v}" for k, v in counts.items())
        L.append(f"| najdorf_w_{anchor} | {per} | {sum(counts.values())} | {budget} ({band}) |")
    L.append("")
    text = "\n".join(L)
    path = cfg.project_root / DIFF_FILE
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    if KEEP_MARK in old:
        text += "\n" + old[old.index(KEEP_MARK):]
    path.write_text(text, encoding="utf-8")
    return text


def write_calibration_guide(cfg: Config) -> Path:
    src = (cfg.project_root / RAW_DIR / "calibration_levels.md").read_text(encoding="utf-8")
    if src.startswith("---"):
        end = src.find("\n---", 3)
        src = src[end + 4:].lstrip("\n")
    body = src.replace("# Cosa cambia tra i livelli (guida alla calibrazione)", "").lstrip("\n")
    out = (
        "# Guida alla calibrazione: cosa cambia tra i livelli\n\n"
        f"> {GUIDE_INTRO}\n>\n"
        "> Fonte: `examples/golden/raw/calibration_levels.md` (raw v0, D-49). "
        "I parametri normativi sono in §7 della documentazione e in `config/thresholds.yaml`.\n\n"
        + body
    )
    path = cfg.project_root / GUIDE_FILE
    path.write_text(out, encoding="utf-8")
    return path


def golden_data(
    cfg: Config,
    analyzer: CachedAnalyzer,
    maia_factory: Callable[[], Any] | None,
    time_scale: float = 1.0,
    progress: Callable[[str], None] = lambda s: None,
    reuse_nodes: bool = False,
) -> dict[str, Any]:
    root = cfg.project_root
    nodes_path = root / NODES_FILE
    if reuse_nodes and nodes_path.is_file():
        nodes_data = json.loads(nodes_path.read_text(encoding="utf-8"))
        progress(f"Riuso {NODES_FILE}")
    else:
        nodes_data = run_engine_nodes(cfg, analyzer, time_scale, progress)
        nodes_path.write_text(json.dumps(nodes_data, indent=1, ensure_ascii=False), encoding="utf-8")
    maia_data = None
    maia_error = None
    if maia_factory is not None:
        try:
            maia = maia_factory()
            progress("Maia-2 sui nodi per le ancore 1500, 1900, 2400")
            maia_data = run_maia(cfg, maia, nodes_data)
            (root / MAIA_FILE).write_text(json.dumps(maia_data, indent=1, ensure_ascii=False), encoding="utf-8")
        except Exception as e:  # noqa: BLE001 - reported in the diff and to the user
            maia_error = str(e)
    else:
        maia_error = "Maia-2 non richiesto"
    write_diff(cfg, nodes_data, maia_data, maia_error)
    write_calibration_guide(cfg)
    a = ac09(_node_index(nodes_data))
    return {"ac09": a, "maia_error": maia_error}


def open_analyzer(cfg: Config, cache_path: Path | None = None) -> tuple[Any, CachedAnalyzer]:
    from chessanalyst.engines.factory import make_stockfish

    sf = make_stockfish(cfg).open()
    return sf, CachedAnalyzer(sf, Cache(cache_path))
