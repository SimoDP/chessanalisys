"""Choice of the few-shot example (§9.2): one example per call, by anchor; in opponent mode
``_s07_alt.json`` is added. Examples are read from ``examples/golden/fewshot`` and their tokens
are resolved against the frozen packs (legend)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from chessanalyst.config import Config
from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.golden.render import S07_ALT_PACK, fewshot_path, golden_dir, load_meta, terms_path
from chessanalyst.llm.legend import legend_lines
from chessanalyst.verify.contamination import load_terms


@dataclass
class Example:
    anchor: str
    output_json: str                 # compact JSON of the fewshot
    epd: str                         # EPD of the example's position (V09, D-52)
    validated: bool
    legend: list[str] = field(default_factory=list)
    alt_json: str | None = None
    terms: list[list[str]] = field(default_factory=list)


def _compact(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def load_example(cfg: Config, anchor: str, opponent_mode: bool) -> Example:
    out = json.loads(fewshot_path(cfg, anchor).read_text(encoding="utf-8"))
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    seen: set[str] = set()
    ex = Example(anchor=anchor, output_json=_compact(out), epd=pack["position"]["epd"],
                 validated=bool(load_meta(cfg, anchor).get("validated")),
                 legend=legend_lines(out, pack, cfg.wording, seen), terms=load_terms(terms_path(cfg)))
    if opponent_mode:
        alt = json.loads((golden_dir(cfg) / "fewshot" / "_s07_alt.json").read_text(encoding="utf-8"))
        ex.alt_json = _compact(alt)
        ex.legend += legend_lines(alt, load_frozen_pack(cfg, S07_ALT_PACK), cfg.wording, seen)
    return ex


def example_for(cfg: Config, pack: dict) -> Example:
    return load_example(cfg, pack["user"]["anchor"], not pack["position"]["user_to_move"])
