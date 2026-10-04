"""Prompt (Appendix E), tool schema (Appendix F), legend (§9.2) and privacy (§11.5)."""

from __future__ import annotations

import json
import re

import jsonschema
import pytest

from chessanalyst.golden.packs import load_frozen_pack
from chessanalyst.llm.fewshot import example_for
from chessanalyst.llm.prompt import SYSTEM_PROMPT, build_user_message, number_words, retry_message
from chessanalyst.llm.schema import TOOL_NAME, tool_definition
from tests.fault_fixtures import EXPECTED
from tests.llm_helpers import recorded

DOC = "docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md"


def _block_after(root, heading: str, fence: str = "```") -> str:
    doc = (root / DOC).read_text(encoding="utf-8")
    a = doc.index(heading)
    start = doc.index(fence, a)
    start = doc.index("\n", start) + 1
    return doc[start:doc.index("\n```", start)]


def test_system_prompt_is_appendix_e1(root):
    assert SYSTEM_PROMPT == _block_after(root, "### E.1 System prompt")


def test_tool_schema_equivalent_to_appendix_f(root):
    appendix = json.loads(_block_after(root, "## Appendice F."))
    ours = tool_definition()
    assert ours["name"] == appendix["name"] == TOOL_NAME and ours["description"] == appendix["description"]
    a = jsonschema.Draft202012Validator(appendix["input_schema"])
    b = jsonschema.Draft202012Validator(ours["input_schema"])
    samples = [recorded(n)["content"][0]["input"] for n in EXPECTED if recorded(n)["content"][0]["type"] == "tool_use"]
    good = samples[0]
    samples += [
        {**good, "schema_version": "2"}, {**good, "extra": 1}, {"schema_version": "1", "sections": [], "notes": []},
        {**good, "sections": [{"id": "S14", "blocks": [{"type": "p", "text": "x", "source": "engine"}]}]},
        {**good, "sections": [{"id": "S01", "blocks": [{"type": "p", "text": "x", "source": "engine", "assertions": None}]}]},
        {**good, "sections": [{"id": "S01", "blocks": [{"type": "line", "pv": "PV1", "plies": 0}]}]},
        {**good, "sections": [{"id": "S01", "blocks": [{"type": "table", "ref": "T5"}]}]},
        {**good, "sections": [{"id": "S01", "blocks": [{"type": "text_table", "columns": ["a"], "rows": [[]]}]}]},
        {**good, "sections": [{"id": "S01", "blocks": [{"type": "p", "text": "x", "source": "mixed", "assertions": [
            {"kind": "feature", "key": "k", "side": None, "squares": ["e4"]}]}]}]},
    ]
    for s in samples:
        assert a.is_valid(s) == b.is_valid(s), s


def test_user_message_structure(cfg):
    pack = load_frozen_pack(cfg, "najdorf_w_1500")
    msg = build_user_message(cfg, pack, example_for(cfg, pack))
    assert msg.startswith('<esempio ancora="1500">\nQuesto esempio riguarda')
    for tag in ("<legenda>", "</legenda>", "<analisi>", "</esempio>", "<pacchetto>", "</pacchetto>", "<istruzioni>"):
        assert tag in msg
    assert "<analisi_s07_alternativa>" not in msg
    assert "Modalità: tocca a te. Fascia: 1200_1600. Ancora: 1500. Giochi con il Bianco." in msg
    assert "- S07 «Mosse candidate»: circa" in msg and "deve citare C1, C2, C11" in msg
    assert "con colonne di testo per_chi" in msg
    assert "Quota massima di contenuto theory: settanta per cento delle parole." in msg
    assert "{{ev:N1}} → +0,34" in msg.split("</legenda>")[0]
    view = json.loads(msg.split("<pacchetto>\n")[1].split("\n</pacchetto>")[0])
    assert "tables" not in view


def test_opponent_mode_adds_s07_alt(cfg):
    pack = load_frozen_pack(cfg, "najdorf_after_be3_w_1900")
    msg = build_user_message(cfg, pack, example_for(cfg, pack))
    assert "<analisi_s07_alternativa>" in msg and "Modalità: tocca all'avversario" in msg
    assert "{{mv:R1.u1}} → 7.Nb3" in msg


@pytest.mark.parametrize("anchor", ["1500", "1900", "2400"])
def test_example_choice(cfg, anchor):
    ex = example_for(cfg, load_frozen_pack(cfg, f"najdorf_w_{anchor}"))
    assert ex.anchor == anchor and ex.validated is False and ex.terms


def test_legend_order_of_first_appearance(cfg):
    ex = example_for(cfg, load_frozen_pack(cfg, "najdorf_w_1900"))
    toks = [ln.split(" → ")[0] for ln in ex.legend]
    assert len(toks) == len(set(toks)) and toks[:3] == ["{{ev:N1}}", "{{pct:root.draw}}", "{{mv:C1}}"]


def test_number_words():
    assert [number_words(n) for n in (35, 50, 70, 21, 28, 100, 0)] == [
        "trentacinque", "cinquanta", "settanta", "ventuno", "ventotto", "cento", "zero"]


def test_retry_message():
    assert retry_message(["V03 · S06 · blocco 2 · «g4-g5» · suggerimento"]) == (
        "La consegna contiene errori. Correggi solo questi punti e richiama submit_analysis con l'analisi completa.\n"
        "V03 · S06 · blocco 2 · «g4-g5» · suggerimento")


def test_privacy_no_pgn_names_or_paths(cfg, root):
    """§11.5: a PGN with names and tags → nothing of them reaches the user message."""
    from chessanalyst.inputs.load import load_position
    from tests.recorded import openings, recorded_engines
    from chessanalyst.pipeline import analyse_position, resolve_settings
    from tests.synthetic import FakeClock

    path = root / "fixtures" / "pgn" / "single.pgn"
    pos = load_position(cfg, "pgn", path.read_text(encoding="utf-8"))
    _, an, maia = recorded_engines(root, cfg)
    pack = analyse_position(cfg, pos, resolve_settings(cfg, "w", 1900, "fide", None, "deep"), an, maia,
                            openings(cfg), clock=FakeClock())
    msg = build_user_message(cfg, json.loads(pack.model_dump_json()), example_for(cfg, json.loads(pack.model_dump_json())))
    for secret in ("Rossi", "Bianchi", "Torneo", "Milano", "2026.09.12", "600+5", str(path), "single.pgn"):
        assert secret not in msg
    assert not re.search(r"\[(White|Black|Event)\s", msg)
