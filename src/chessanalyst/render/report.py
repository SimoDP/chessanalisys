"""Header and technical report of ``analysis.md`` (§8.6). Warning texts come
from ``config/wording.yaml: header``; the line templates are those of §8.6."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessanalyst.config import Config
from chessanalyst.render.format_it import numbered

if TYPE_CHECKING:
    from chessanalyst.render.markdown import RenderInfo

import chess

REPORT_TITLE = "Rapporto tecnico"
UNNAMED = "posizione senza nome"
SCALES = {"fide": "FIDE", "lichess": "Lichess", "chesscom": "chess.com"}
HEADER_WARNINGS = ("references_not_validated", "profile_unsupported", "move_order_limited",
                   "maia_low_confidence_header", "unstable_nodes")
CONFIDENCE = {"normal": "normale", "low": "bassa"}
CHECK_CODES = tuple(f"V{k:02d}" for k in range(1, 12))


def _colors(cfg: Config, code: str) -> str:
    return cfg.wording["colors"][code]


def header_lines(cfg: Config, pack: dict, info: "RenderInfo") -> list[str]:
    u, pos = pack["user"], pack["position"]
    name = pack["opening"]["name"] if pack["opening"] else UNNAMED
    sf = pack["engine"]["stockfish"]
    lines = [
        f"# Analisi della posizione: {name}",
        "",
        f"FEN: `{pos['fen']}` · Tratto: {_colors(cfg, pos['side_to_move'])} · Giochi con: {_colors(cfg, u['color'])}",
        f"Elo dichiarato {u['elo_declared']} {SCALES[u['elo_scale']]} → {u['elo_maia']} in scala Lichess usata da "
        f"Maia-2 · Avversario: {u['opp_elo_declared']} {SCALES[u['elo_scale']]} → {u['opp_elo_maia']}",
        f"Fascia {u['band']} · Ancora {u['anchor']} · Profilo {u['budget_profile']} · {sf['version']} · "
        f"profondità radice {pack['engine']['root']['depth']}",
        "",
        f"> {cfg.wording['header']['convention']}",
    ]
    active = set(pack["warnings"]) | ({"references_not_validated"} if not info.references_validated else set())
    for w in HEADER_WARNINGS:
        if w in active:
            lines.append(f"> {cfg.wording['header'][w]}")
    return lines + [""]


def _path(pack: dict, path: list[str]) -> str:
    if not path:
        return "radice"
    if "--" in path:
        return "mossa nulla" + (" " + " ".join(path[1:]) if len(path) > 1 else "")
    return numbered(chess.Board(pack["position"]["fen"]), path)


def _fmt_s(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def report_lines(cfg: Config, pack: dict, output: dict, info: "RenderInfo") -> list[str]:
    u, m, sf = pack["user"], pack["maia"], pack["engine"]["stockfish"]
    nodes = pack["nodes"]
    depths = [n["depth"] for n in nodes]
    unstable = [f"{n['id']} ({_path(pack, n['path'])})" for n in nodes if n["unstable_depth"]]
    omitted = [f"{o['id']} ({o['reason']})" for o in pack["omitted_sections"]]
    absorbed = [f"{s['id']} in {s['absorbed_into']}" for s in pack["section_plan"] if s["absorbed_into"]]
    phases = [f"{p['phase']} ({p['reason']})" for p in pack["omitted_phases"]]
    onodes = [f"{n['phase']} {n['ref']} ({n['reason']})" for n in pack["omitted_nodes"]]
    other_w = [w for w in pack["warnings"] if w not in HEADER_WARNINGS] + info.warnings
    checks = " · ".join(f"{c} {info.checks.get(c, 'superato')}" for c in CHECK_CODES)
    none = "nessuno"
    lines = [
        f"## {REPORT_TITLE}",
        "",
        f"- Versioni: {sf['version']} · Maia-2 {m['package_version']} (modello {m['model_type']}, {m['device']}) · "
        f"modello di linguaggio: {info.llm_model or 'nessuno (esempio di riferimento)'}",
        f"- Profilo {u['budget_profile']} · tempo dei motori {_fmt_s(sum(n['time_s'] for n in nodes))} s · "
        f"nodi analizzati {len(nodes)} · profondità minima {min(depths)} e massima {max(depths)}",
        f"- Nodi sotto la profondità minima: {', '.join(unstable) if unstable else none}",
        f"- Elo dichiarato {u['elo_declared']} {SCALES[u['elo_scale']]} · Elo Maia-2 {u['elo_maia']} · fascia {u['band']} "
        f"· ancora {u['anchor']} · confidenza di Maia-2 {CONFIDENCE[m['confidence']]}",
        f"- Sezioni omesse: {', '.join(omitted) if omitted else 'nessuna'} · assorbite: "
        f"{', '.join(absorbed) if absorbed else 'nessuna'}",
        f"- Fasi omesse: {', '.join(phases) if phases else 'nessuna'} · nodi omessi: {', '.join(onodes) if onodes else none}",
        f"- Contenuto teorico: {info.theory_blocks} blocchi, {round(info.theory_share * 100)}% delle parole",
        f"- Controlli: {checks}",
        f"- Retry: {info.retries}",
        f"- Rimossi in modalità degradata: {'; '.join(info.removed) if info.removed else none}",
        f"- Marcati come non verificati: {'; '.join(info.marked) if info.marked else none}",
        f"- Avvisi: {', '.join(other_w) if other_w else none}",
        f"- Note del modello: {'; '.join(output.get('notes') or []) or 'nessuna'}",
        "- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e "
        "asserzione non è controllata.",
        "",
    ]
    return lines
