"""D-71: computed facts for the model (features/motifs.py) and V12 (verify/board_claims.py), on a real case of
the user: Black to move wins with 18...e4; DeepSeek wrote about a white knight on c4 (the queen) and a bishop on
f1 (a rook). ``fixtures/user_cases/e4_wins_w_1700.*``."""

from __future__ import annotations

import json

import chess
import pytest

from chessanalyst.features.motifs import line_facts, move_facts, pack_facts
from chessanalyst.verify.board_claims import BoardClaims
from chessanalyst.verify.checker import verify_response

CASE = "fixtures/user_cases/e4_wins_w_1700"


@pytest.fixture
def case(root):
    pack = json.loads((root / f"{CASE}.pack.json").read_text(encoding="utf-8"))
    out = json.loads((root / f"{CASE}.deepseek.json").read_text(encoding="utf-8"))
    return pack, out


def test_move_facts_explain_the_tactics(cfg, case):
    pack, _ = case
    words = cfg.wording["pieces"]
    f = pack_facts(pack, words, cfg.default.llm.view.pv_plies)
    assert f["board"]["c4"] == "donna bianca" and f["board"]["f1"] == "torre bianca" and "c3" in f["board"]
    e4 = f["moves"]["R5"]                       # 18...e4: discovered attack of Bf6 on Nc3, pawn attacks f3
    assert {(a["square"], a["discovered"]) for a in e4["attacks"]} == {("c3", True), ("f3", False)}
    assert f["moves"]["R1"]["check"] is True and f["moves"]["R1"]["attacks"][0]["piece"] == "donna bianca"
    assert f["moves"]["R1.u3"]["captures"] == "donna nera"
    assert f["moves"]["R1.u3"]["leaves_hanging"] == ["donna bianca in d4"]        # cxd4
    assert f["moves"]["R4.u1"]["captures"] == "pedone nero"
    assert f["hypothetical_nodes"] == ["N2"]
    assert f["lines"]["PV5"]["material_change_for_user"] < 0


def test_line_facts_and_pins(cfg):
    words = cfg.wording["pieces"]
    b = chess.Board("4k3/8/8/8/8/8/3q4/R3K3 w Q - 0 1")
    lf = line_facts(b, ["Kxd2", "Kd7"], 2, chess.WHITE, words)
    assert lf == {"material_change_for_user": 9, "captures": ["Kxd2: donna nera"]}
    pin = chess.Board("4k3/4r3/8/8/8/8/8/R2K4 w - - 0 1")
    assert move_facts(pin, "Ra8+", words)["check"] is True
    p2 = chess.Board("4k3/4n3/8/8/8/8/8/3K3R w - - 0 1")
    assert move_facts(p2, "Re1", words)["pins"] == ["cavallo nero in e7"]


def test_v12_finds_the_invented_pieces(cfg, case):
    pack, out = case
    res = verify_response(cfg, pack, out)
    v12 = [(e.section, e.text, e.detail) for e in res.errors if e.code == "V12"]
    texts = [t for _, t, _ in v12]
    assert sum("cavallo" in t.lower() and "c4" in t for t in texts) >= 3
    assert any(t.startswith("Alfiere f1") for t in texts)
    assert any("non difende d2" in d for _, _, d in v12)
    verdict = sorted(t for s, t, d in v12 if "banda di N1" in d)
    assert verdict == ["equilibrat", "stai bene"]           # «La posizione è equilibrata» at -4,77
    assert len(v12) == 6 + 2


@pytest.mark.parametrize("text,ok", [
    ("La donna in c4 attacca il pedone in c5.", True),
    ("Il cavallo nero in f4 attacca g2.", True),
    ("Hai un cavallo forte in c4.", False),
    ("**Alfiere f1:** protegge il re.", False),
    ("Il cavallo c3 protegge il pedone in d2.", False),
    ("Dopo lo scacco porta il re in h1.", True),                  # a move: Kh1 is legal later in the lines
    ("Se il Nero gioca bene, la donna nera in d4 domina.", True),  # Qd4+ is a reply
    ("La torre nera in c8 difende c5.", False),                    # no move word: the square is empty now
    ("I pedoni b2 e b3 sono doppiati.", True),
    ("I pedoni b2 e c4 sono doppiati.", False),
])
def test_v12_sentences(cfg, case, text, ok):
    pack, _ = case
    bc = BoardClaims(pack, cfg.wording["pieces"], cfg.verify["v12"])
    assert (bc.check(text) == []) == ok, [c.detail for c in bc.check(text)]


def test_v12_theory_and_move_cells(cfg, case):
    pack, _ = case
    bc = BoardClaims(pack, cfg.wording["pieces"], cfg.verify["v12"])
    assert bc.check("**Torre in c8**", theory=True) == []          # a plan: the rook gets to c8 in a line
    assert bc.check("Torre in c8: entra in a7", about_moves=True) == []
    assert bc.check("**Alfiere f1**", theory=True)                  # the square right after the piece: now
    assert bc.check("Il cavallo in e8 è forte.", theory=True)       # nowhere in the lines either


def test_pins(cfg, case):
    from chessanalyst.verify.board_claims import pinned

    pack, _ = case
    bc = BoardClaims(pack, cfg.wording["pieces"], cfg.verify["v12"])
    assert bc.check("Il cavallo in c3 è inchiodato.")                       # invented by the model
    assert bc.check("L'alfiere in f6 inchioda il cavallo in c3.")
    assert bc.check("L'alfiere in f6 lo inchioda.") == []                   # no square: not checked
    assert pinned(chess.Board("4k3/8/8/1b6/8/3N4/4Q3/K7 w - - 0 1")) == {(True, chess.KNIGHT, chess.D3)}
    assert pinned(chess.Board("4k3/8/8/1b6/8/3N4/4P3/K3Q3 w - - 0 1")) == set()
