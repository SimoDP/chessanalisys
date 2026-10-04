"""``chessanalyst golden --render`` (§8-bis.4 M1b, step 3, AC-27).

Each ``fewshot/najdorf_w_<anchor>.json`` must pass V01–V10 against its frozen
pack; ``rendered/najdorf_w_<anchor>.md`` is then produced by the normal render
(it is always derived: never edited by hand). ``_s07_alt.json`` is checked
against the AC-21 pack (S07 only).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from chessanalyst.config import Config
from chessanalyst.golden.packs import ANCHORS, load_frozen_pack
from chessanalyst.render.markdown import RenderInfo, render_markdown
from chessanalyst.verify.checker import Result, error_lines, restrict_plan, verify_response
from chessanalyst.verify.contamination import load_terms
from chessanalyst.verify.report import check_outcomes

S07_ALT_PACK = "najdorf_after_be3_w_1900"


def golden_dir(cfg: Config) -> Path:
    return cfg.project_root / "examples" / "golden"


def fewshot_path(cfg: Config, anchor: str) -> Path:
    return golden_dir(cfg) / "fewshot" / f"najdorf_w_{anchor}.json"


def load_meta(cfg: Config, anchor: str) -> dict:
    p = golden_dir(cfg) / "fewshot" / f"najdorf_w_{anchor}.meta.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else {"validated": False}


def terms_path(cfg: Config) -> Path:
    return golden_dir(cfg) / "fewshot" / "_terms.txt"


@dataclass
class GoldenOutcome:
    name: str
    result: Result
    rendered: Path | None = None
    errors: list[str] = field(default_factory=list)


def render_info(result: Result, validated: bool) -> RenderInfo:
    return RenderInfo(llm_model=None, references_validated=validated, checks=check_outcomes(result, None),
                      theory_blocks=len(result.theory_blocks), theory_share=result.theory_share)


def check_fewshot(cfg: Config, anchor: str) -> tuple[dict, dict, Result]:
    pack = load_frozen_pack(cfg, f"najdorf_w_{anchor}")
    fewshot = json.loads(fewshot_path(cfg, anchor).read_text(encoding="utf-8"))
    terms = load_terms(terms_path(cfg))
    return pack, fewshot, verify_response(cfg, pack, fewshot, fewshot_epd=pack["position"]["epd"], terms=terms)


def check_s07_alt(cfg: Config) -> Result:
    pack = restrict_plan(load_frozen_pack(cfg, S07_ALT_PACK), {"S07"})
    frag = json.loads((golden_dir(cfg) / "fewshot" / "_s07_alt.json").read_text(encoding="utf-8"))
    return verify_response(cfg, pack, frag)


def golden_render(cfg: Config, progress: Callable[[str], None] = print) -> list[GoldenOutcome]:
    hints = cfg.wording["verify_hints"]
    outcomes = []
    out_dir = golden_dir(cfg) / "rendered"
    out_dir.mkdir(parents=True, exist_ok=True)
    for anchor in ANCHORS:
        name = f"najdorf_w_{anchor}"
        pack, fewshot, res = check_fewshot(cfg, anchor)
        o = GoldenOutcome(name, res, errors=error_lines(res.errors, hints))
        if not res.errors:
            doc = render_markdown(cfg, pack, res.output, render_info(res, bool(load_meta(cfg, anchor).get("validated"))))
            o.rendered = out_dir / f"{name}.md"
            o.rendered.write_text(doc, encoding="utf-8")
        outcomes.append(o)
        progress(f"{name}: {'OK' if not res.errors else f'{len(res.errors)} errori'}")
    res = check_s07_alt(cfg)
    outcomes.append(GoldenOutcome("_s07_alt", res, errors=error_lines(res.errors, hints)))
    progress(f"_s07_alt: {'OK' if not res.errors else f'{len(res.errors)} errori'}")
    return outcomes
