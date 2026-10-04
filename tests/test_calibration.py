"""M5: sampling, offline recomputation of T and selection, AUC (no engines, no network)."""

from __future__ import annotations

import io
import json
import random

import chess.pgn
import pytest

from chessanalyst.calibration import fit as F
from chessanalyst.calibration.sample import pick_position, sample_positions


def test_auc():
    assert F.auc([3, 2, 1], [True, False, False]) == 1.0
    assert F.auc([1, 2, 3], [True, False, False]) == 0.0
    assert F.auc([1, 1], [True, False]) == 0.5
    assert F.auc([1, 2], [False, False]) is None


GAME = """[Event "Rated Rapid game"]
[Site "https://lichess.org/abcdEFGH"]
[White "someone"]
[Black "other"]
[Result "1-0"]
[WhiteElo "1650"]
[BlackElo "1700"]
[TimeControl "600+0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7
11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7 14. Bg5 b4 1-0
"""


def test_pick_position_without_names(cfg):
    game = chess.pgn.read_game(io.StringIO(GAME))
    p = pick_position(cfg, game, random.Random(1))
    sp = cfg.calibration["sample"]
    assert p is not None and sp["ply_min"] <= p["ply"] <= len(p["moves"]) - sp["tail_plies"]
    assert p["id"] == "abcdEFGH" and "someone" not in json.dumps(p)
    assert p["elo_self"] == (1650 if p["side"] == "w" else 1700)


def test_sample_respects_event_and_quota(cfg):
    games = [chess.pgn.read_game(io.StringIO(GAME.replace("Rapid", r))) for r in ("Blitz", "Rapid", "Rapid")]
    pos = sample_positions(cfg, iter(games))
    assert len(pos) == 2 and all(p["month"] == cfg.calibration["source"]["month"] for p in pos)


def _record_from_pack(pack):
    """The annotation record of a frozen pack, using only its filtered lines."""
    me = pack["user"]["color"]
    lines = [{"defender": ln["defender"], "risk": ln["risk"], "p_att": ln["p_att"], "impact_cp": ln["impact_cp"],
              "mate": ln["reason"] == "mate" or (ln["mate_user"] is not None and (ln["mate_user"] > 0) == (ln["attacker"] == me)),
              "tags": ln["tags"], "primary": ln["primary"]} for ln in pack["filtered_lines"]]
    return {"side": me, "band": pack["user"]["band"], "lines": lines,
            "t_stat": {c["id"]: c["components"]["T_stat"] for c in pack["categories"]}, "played": []}


@pytest.mark.parametrize("name", ["fixtures/packs/fried_liver_w_1500", "examples/golden/packs/najdorf_w_1900"])
def test_offline_t_equals_the_engine(cfg, root, name):
    pack = json.loads((root / f"{name}.pack.json").read_text(encoding="utf-8"))
    rec = _record_from_pack(pack)
    for c in pack["categories"]:
        if c["id"] == "practical_complexity":
            continue
        assert round(F.user_t(cfg, rec, c["id"], 1.0, 1.0, 0.0)) == c["T"][pack["user"]["color"]], c["id"]


def test_selection_offline_matches_the_pack(cfg, root):
    pack = json.loads((root / "examples/golden/packs/najdorf_w_1900.pack.json").read_text(encoding="utf-8"))
    rec = {"candidates": [{k: c[k] for k in ("uci", "san", "eval_user_cp", "loss_cp", "p_user", "e0_rank",
                                                "source", "explained", "complexity")} for c in pack["engine"]["candidates"]],
           "maia_top": pack["nodes"][0]["maia"]["policy"][0]["uci"]}
    bp0 = cfg.thresholds.band_params["1600_2000"]
    ex = F.selection(rec, F.BandSel(bp0.K, bp0.explained_min, bp0.listed_max, bp0.L_max, bp0.A))
    assert sorted(ex) == sorted(c["uci"] for c in pack["engine"]["candidates"] if c["explained"])


def test_report_reproducible(cfg, root):
    """The committed relation comes from the committed annotations."""
    from chessanalyst.calibration.report import FIT_FILE, compute

    if not (root / F.ANNOTATIONS_FILE).is_file() or not (root / FIT_FILE).is_file():
        pytest.skip("annotazioni assenti: chessanalyst calibrate --annotate")
    if not any((root / F.PACKS_DIR).glob("*.pack.json")):
        pytest.skip("pacchetti delle annotazioni assenti (data/ non è versionata)")
    saved = json.loads((root / FIT_FILE).read_text(encoding="utf-8"))
    d = json.loads(json.dumps(compute(cfg)))
    assert d["t_baseline"]["mean_auc"] == saved["t_baseline"]["mean_auc"] or saved.get("thresholds_updated")
