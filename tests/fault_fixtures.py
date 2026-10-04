"""Builds the recorded model responses of Appendix G.6 (``fixtures/recorded/llm/``).

Every defective response is ``good_najdorf_1900.json`` (= the 1900 fewshot,
valid against its frozen pack) with exactly one defect, so that the expected
errors are the only ones. ``bad_contamination.json`` is written against
``rook_endgame.pack.json`` (synthetic engines, frozen next to it).

Regenerate with ``python -m tests.fault_fixtures`` after changing the fewshot;
``tests/acceptance/test_ac16_fault_injection.py`` checks they are up to date.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "recorded" / "llm"
FEWSHOT = ROOT / "examples" / "golden" / "fewshot" / "najdorf_w_1900.json"

# file → (pack, expected error codes; "V07a" = V07 with sub-check a)
EXPECTED: dict[str, tuple[str, set[str]]] = {
    "good_najdorf_1900.json": ("najdorf_w_1900", set()),
    "bad_illegal_san.json": ("najdorf_w_1900", {"V04"}),
    "bad_unknown_id.json": ("najdorf_w_1900", {"V02"}),
    "bad_null_value.json": ("najdorf_w_1900", {"V02"}),
    "bad_free_digit.json": ("najdorf_w_1900", {"V03"}),
    "bad_chain.json": ("najdorf_w_1900", {"V03"}),
    "bad_plan.json": ("najdorf_w_1900", {"V04"}),
    "bad_plan_engine.json": ("najdorf_w_1900", {"V10"}),
    "bad_theory_tokens.json": ("najdorf_w_1900", {"V08", "V10"}),
    "bad_extra_section.json": ("najdorf_w_1900", {"V07a"}),
    "bad_missing_table.json": ("najdorf_w_1900", {"V07b"}),
    "bad_must_cover.json": ("najdorf_w_1900", {"V07c"}),
    "bad_contamination.json": ("rook_endgame", {"V09", "V07d"}),   # short on purpose: budgets of the synthetic pack
    "bad_markup.json": ("najdorf_w_1900", {"V01"}),
    "bad_assertion.json": ("najdorf_w_1900", {"V06"}),
    "bad_long_line.json": ("najdorf_w_1900", {"V05"}),
    "max_tokens.json": ("najdorf_w_1900", {"V01"}),
}


def envelope(output: dict, stop_reason: str = "tool_use") -> dict:
    """The fields of an API response that the verification reads (§9.3)."""
    return {"stop_reason": stop_reason,
            "content": [{"type": "tool_use", "id": "toolu_recorded", "name": "submit_analysis", "input": output}]}


def _section(out: dict, sid: str) -> dict:
    return next(s for s in out["sections"] if s["id"] == sid)


def _replace(out: dict, sid: str, old: str, new: str) -> dict:
    """Replace ``old`` in exactly one text of section ``sid``."""
    o = copy.deepcopy(out)
    hits = 0

    def walk(x):
        nonlocal hits
        if isinstance(x, dict):
            if isinstance(x.get("text"), str) and old in x["text"] and hits == 0:
                x["text"] = x["text"].replace(old, new, 1)
                hits += 1
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(_section(o, sid))
    if hits != 1:
        raise ValueError(f"{old!r} non trovato in {sid}")
    return o


def rook_endgame_response(pack: dict) -> dict:
    """A structurally complete answer on the rook endgame that names the Najdorf (V09)."""
    plan = [s for s in pack["section_plan"] if s["required"]]
    sections = []
    for s in plan:
        blocks = [{"type": "p", "source": "engine",
                   "text": "Il finale è vicino all'equilibrio: {{ev:N1}}. Non è una struttura da Najdorf."}]
        blocks += [{"type": "table", "ref": t} for t in s["tables"]]
        if s["must_cover"]:
            blocks.append({"type": "p", "source": "engine",
                           "text": " ".join("{{mv:%s}} ({{ev:%s}})." % (c, c) for c in s["must_cover"])})
        sections.append({"id": s["id"], "blocks": blocks})
    return {"schema_version": "1", "sections": sections, "notes": []}


def build(rook_pack: dict) -> dict[str, dict]:
    good = json.loads(FEWSHOT.read_text(encoding="utf-8"))
    r = _replace
    out = {
        "good_najdorf_1900.json": envelope(good),
        "bad_illegal_san.json": envelope(r(good, "S01", "{{m:e5@N2}}", "{{m:Nf6@N1}}")),
        "bad_unknown_id.json": envelope(r(good, "S01", "{{ev:C1}}", "{{ev:C99}}")),
        "bad_null_value.json": envelope(r(good, "S07", "{{pct:C10.p_user}}", "{{pct:C1.p_up}}")),
        "bad_free_digit.json": envelope(r(good, "S01", "Le cinque mosse", "Le 5 mosse")),
        "bad_chain.json": envelope(r(good, "S04", "{{plan:w:g4,g5,h4@N3}}", "g4-g5 e h4")),
        "bad_plan.json": envelope(r(r(good, "S04", "{{plan:w:g4,g5,h4@N3}}", "{{plan:w:Be3,Qd2,Qxd8@N1}}"),
                                    "S03", "{{plan:w:Be2,Be3,O-O,f4@N1}}", "{{plan:w:Bb5,O-O@N1}}")),
        "bad_plan_engine.json": envelope(r(good, "S01", "quindi non sprecare tempi",
                                           "quindi non sprecare tempi con {{plan:w:Be3,Qd2@N3}}")),
        "bad_theory_tokens.json": envelope(r(good, "S04", "si arrocca corto.", "si arrocca corto ({{ev:C5}}).")),
        "bad_markup.json": envelope(r(good, "S01", "Posizione teorica", "## Posizione teorica")),
        "bad_long_line.json": envelope(r(good, "S07", "{{pv:PV1:8}}", "{{pv:PV1:10}}")),
        "max_tokens.json": {"stop_reason": "max_tokens",
                            "content": [{"type": "text", "text": "Analisi interrotta per limite di token."}]},
    }
    extra = copy.deepcopy(good)
    extra["sections"].append({"id": "S11", "blocks": [{"type": "p", "source": "engine",
                                                       "text": "Una sezione non prevista: {{ev:C2}}."}]})
    out["bad_extra_section.json"] = envelope(extra)

    missing = copy.deepcopy(good)
    s07 = _section(missing, "S07")
    t1 = next(b for b in s07["blocks"] if b["type"] == "table")
    texts = [c["idea"]["text"] for c in t1["text_cells"].values()]
    s07["blocks"][s07["blocks"].index(t1)] = {"type": "p", "source": "mixed", "text": ". ".join(texts) + "."}
    out["bad_missing_table.json"] = envelope(missing)

    must = r(r(good, "S07", "{{mv:C3}} e {{mv:C4}}", "{{mv:C3}} e {{mv:C5}}"), "S07", "{{ev:C4}}", "{{ev:C5}}")
    out["bad_must_cover.json"] = envelope(must)

    feat = copy.deepcopy(good)
    para = next(b for b in _section(feat, "S04")["blocks"] if b["type"] == "p")
    para["assertions"].append({"kind": "feature", "key": "backward_pawn", "side": "w", "squares": ["d4"]})
    out["bad_assertion.json"] = envelope(feat)

    out["bad_contamination.json"] = envelope(rook_endgame_response(rook_pack))
    return out


def rook_endgame_pack() -> dict:
    """Pack of ``rook_endgame.fen`` with the deterministic synthetic engines (no opening)."""
    from chessanalyst.config import load_config
    from chessanalyst.engines.cache import Cache, CachedAnalyzer
    from chessanalyst.engines.maia2 import MaiaEngine
    from chessanalyst.inputs.fen import parse_fen
    from chessanalyst.inputs.position import Position
    from chessanalyst.pipeline import analyse_position, resolve_settings
    from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

    cfg = load_config()
    board = parse_fen((ROOT / "fixtures" / "positions" / "rook_endgame.fen").read_text(), cfg.wording["errors"])
    cache = Cache(":memory:")
    pack = analyse_position(cfg, Position(board=board, source="fen"),
                            resolve_settings(cfg, "w", 1900, "fide", None, "standard"),
                            CachedAnalyzer(SyntheticEngine(), cache),
                            MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits, cache), None, clock=FakeClock())
    d = json.loads(pack.model_dump_json())
    d["created_utc"] = "2026-01-01T00:00:00+00:00"
    return d


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rook = rook_endgame_pack()
    (OUT / "rook_endgame.pack.json").write_text(json.dumps(rook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, data in build(rook).items():
        (OUT / name).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("scritto", OUT / name)


if __name__ == "__main__":
    main()
