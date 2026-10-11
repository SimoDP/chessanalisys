"""D-79: pawn structures of the books' catalogue (config/structures.yaml) and the sentence the render writes."""

from __future__ import annotations

import json
import re

import chess
import pytest

from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.features.structures import SQUARE_RE, find_structure, place
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from chessanalyst.plan.outline import outline_pack
from tests.synthetic import FakeClock, SyntheticEngine, SyntheticMaiaBackend

IQP_W = "r1bq1rk1/pp2bppp/2n1pn2/8/3P4/2NB1N2/PP3PPP/R1BQ1RK1 w - - 0 10"
IQP_B = "r1bq1rk1/pp3ppp/2n2n2/2bp4/8/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 10"
HEDGEHOG = "r1bq1rk1/3nbppp/pp1ppn2/8/2P1P3/2N2N2/PP2BPPP/R1BQ1RK1 w - - 0 10"
SAN_RE = re.compile(r"\b[KQRBN][a-h]?[1-8]?x?[a-h][1-8]\b|O-O|\b[a-h][1-8]-[a-h][1-8]\b")


@pytest.fixture(scope="module")
def catalogue(cfg):
    return cfg.structures["catalogue"]


def test_found_for_either_colour(catalogue):
    assert find_structure(chess.Board(IQP_W), catalogue) == ("pedone_isolato", chess.WHITE)
    assert find_structure(chess.Board(IQP_B), catalogue) == ("pedone_isolato", chess.BLACK)
    assert find_structure(chess.Board(), catalogue) is None


def test_the_first_structure_of_the_catalogue_wins(catalogue):
    assert find_structure(chess.Board(HEDGEHOG), catalogue) == ("riccio", chess.WHITE)    # also a Maroczy bind


def test_squares_are_mirrored_for_a_black_owner():
    assert place("la casa {d5} e la colonna {c}", chess.WHITE) == "la casa d5 e la colonna c"
    assert place("la casa {d5} e la colonna {c}", chess.BLACK) == "la casa d4 e la colonna c"


def test_catalogue_texts(cfg, catalogue):
    """Plain words for the render: no move notation, squares only in braces, every detail level covered."""
    assert set(cfg.structures["display"]["sentences"]) == {"1", "2", "3", "4", "5"}
    for sid, e in catalogue.items():
        assert e["name"] and e["summary"] and e["owner"] and e["other"], sid
        for text in [e["summary"], *e["owner"], *e["other"], *e["mistakes"], *e["advanced"]]:
            bare = SQUARE_RE.sub("", text)
            assert not SAN_RE.search(text), (sid, text)
            assert not re.search(r"\d", bare), (sid, text)


def _pack(cfg, fen: str, color: str, elo: int) -> dict:
    us = resolve_settings(cfg, color, elo, "fide", None, "fast", 5)
    pack = analyse_position(cfg, Position(board=chess.Board(fen), source="fen"), us,
                            CachedAnalyzer(SyntheticEngine(), Cache(":memory:")),
                            MaiaEngine(SyntheticMaiaBackend(), cfg.maia2_limits), None, clock=FakeClock())
    return outline_pack(cfg, json.loads(pack.model_dump_json()))


@pytest.mark.parametrize("fen,color,mine", [(IQP_W, "w", True), (IQP_B, "w", False)])
def test_the_plan_opens_with_the_structure(cfg, catalogue, fen, color, mine):
    out = _pack(cfg, fen, color, 1500)
    s05 = next(s for s in out["section_plan"] if s["id"] == "S05")
    e = catalogue["pedone_isolato"]
    lead = s05["lead_text"]
    assert s05["lead_kind"] == "structure" and lead.startswith(f"Struttura dei pedoni: {e['name']}.")
    owner = chess.WHITE if mine else chess.BLACK
    first_mine = place(e["owner" if mine else "other"][0], owner)
    assert f"Il tuo piano: {first_mine}" in lead
    assert ("{" not in lead) and (("d4" in lead) if mine else ("d5" in lead))
    item = next(i for k in out["key_points"] if k["type"] == "plan" for i in k["facts"]["items"]
                if i["key"] == "structure")
    assert item["of"] == ("user" if mine else "opp")
    assert not any(a for a in e["advanced"] if place(a, owner) in lead)     # 1500: no advanced sentence
