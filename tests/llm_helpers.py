"""Frozen packs, fewshots and recorded model responses (fixtures/recorded/llm)."""

from __future__ import annotations

import json
from pathlib import Path

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.verify.checker import verify_response
from chessanalyst.verify.contamination import load_terms
from tests.fault_fixtures import EXPECTED, OUT

ROOT = Path(__file__).resolve().parents[1]
FEWSHOT_DIR = ROOT / "examples" / "golden" / "fewshot"


def recorded(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def pack_for(cfg, name: str) -> dict:
    packname = EXPECTED[name][0]
    if packname == "rook_endgame":
        return json.loads((OUT / "rook_endgame.pack.json").read_text(encoding="utf-8"))
    return load_frozen_pack(cfg, packname)


def fewshot(anchor: str) -> dict:
    return json.loads((FEWSHOT_DIR / f"najdorf_w_{anchor}.json").read_text(encoding="utf-8"))


def check_recorded(cfg, name: str):
    """Verification as the app does it: V09 against the few-shot example of the anchor."""
    pack = pack_for(cfg, name)
    example = load_frozen_pack(cfg, "najdorf_w_1900")
    return verify_response(cfg, pack, recorded(name), fewshot_epd=example["position"]["epd"],
                           terms=load_terms(FEWSHOT_DIR / "_terms.txt"))


def codes(res) -> set[str]:
    return {e.code + (e.sub or "") for e in res.errors}
