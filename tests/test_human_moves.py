"""Usefulness test, phase 3 (D-76): every move played at least 15% of the times, by the user or by the opponent,
is in the document, however bad; the table says how often the other moves are played together; a move that
loses nothing gets no «perde 0,00». In the test (02, 05) Nxf7 at 29% and Be3 at 19% were missing."""

from __future__ import annotations

from chessanalyst import bench
from chessanalyst.explore.select import BandSel, ReplyRow, RootRow, select_candidates, select_replies
from chessanalyst.llm.prompt_kp import _tokens_of
from chessanalyst.pack.tables import _footnote
from chessanalyst.plan.keypoints import key_points
from chessanalyst.verify.resolve import Resolver


def _on(cfg, p=0.15):
    sel = cfg.thresholds.selection.model_copy(update={"human_min_p": p})
    return cfg.model_copy(update={"thresholds": cfg.thresholds.model_copy(update={"selection": sel})})


def test_probable_root_moves_are_explained_and_listed():
    e0 = [RootRow(u, u, e, "e0", i + 1) for i, (u, e) in enumerate([("m1", 50), ("m2", 45), ("m3", 40)])]
    e4 = [RootRow("trap", "trap", -800, "e4", None)]
    pol = {"m1": 0.2, "m2": 0.05, "m3": 0.01, "trap": 0.3}
    bp = BandSel(K=2, explained_min=2, listed_max=2, L_max=40, A=0.5)
    off = select_candidates(e0, e4, pol, bp)
    assert "trap" in off.explained and "trap" not in off.listed          # Maia top only, out of the table
    on = select_candidates(e0, e4, dict(pol, m3=0.16, trap=0.29), bp, 0.15)
    assert {"trap", "m3"} <= set(on.explained) and {"trap", "m3"} <= set(on.listed)


def test_probable_replies_beyond_k():
    rows = [ReplyRow(u, u, e, i + 1, p) for i, (u, e, p) in
            enumerate([("a", 30, 0.05), ("b", 20, 0.25), ("c", 10, 0.2), ("d", -500, 0.18)])]
    assert "d" not in select_replies(rows, 2, 0.05, 2)
    assert set(select_replies(rows, 2, 0.05, 2, 0.15)) == {"a", "b", "c", "d"}


def test_also_played_in_the_recommendation(cfg):
    pack = bench.load_pack(cfg, bench.load_spec(cfg, "bogo_c5_w_1700"))
    rec = next(k for k in key_points(_on(cfg), pack) if k["type"] == "recommendation")
    told = {rec["facts"]["ref"], rec["facts"].get("second", {}).get("ref"), rec["facts"].get("trap", {}).get("ref")}
    also = {x["ref"] for x in rec["facts"].get("also_played", [])}
    assert {"C1", "C3", "C6"} <= told | also and also <= set(rec["ids"])
    rec_off = next(k for k in key_points(_on(cfg, None), pack) if k["type"] == "recommendation")
    assert "also_played" not in rec_off["facts"]


def test_footnote_with_the_other_moves(cfg):
    on = _on(cfg)
    assert _footnote(on, False, [0.4, 0.3]) == "Tutte le altre mosse insieme: 30% (ognuna sotto il 15%)."
    assert _footnote(on, False, [0.6, 0.4]) is None
    assert _footnote(cfg, False, [0.4]) is None                            # v0.9.1: no note
    assert _footnote(on, True, [0.5]).startswith("* Probabilità")


def test_no_loss_token_for_a_move_that_loses_nothing(cfg):
    pack = bench.load_pack(cfg, bench.load_spec(cfg, "bogo_c5_w_1700"))
    best = next(c for c in pack["engine"]["candidates"] if c["loss_cp"] == 0)
    worse = next(c for c in pack["engine"]["candidates"] if c["loss_cp"] > 0)
    r, section = Resolver(pack, cfg.wording), {"max_pv_plies": 4}
    assert "perdita" not in _tokens_of(best["id"], section, r)
    assert "perdita" in _tokens_of(worse["id"], section, r)


def test_v12_on_a_zero_loss(cfg):
    from chessanalyst.plan.outline import outline_pack
    from chessanalyst.verify.checker import Checker
    pack = outline_pack(cfg, bench.load_pack(cfg, bench.load_spec(cfg, "bogo_c5_w_1700")))
    sec = next(s for s in pack["section_plan"] if "C1" in (s.get("cites_allowed") or []) and s["id"] != "S01")
    assert next(c for c in pack["engine"]["candidates"] if c["id"] == "C1")["loss_cp"] == 0

    def errs(text):
        resp = {"content": [{"type": "tool_use", "name": "submit_analysis", "input": {
            "schema_version": "1", "notes": [], "sections": [{"id": sec["id"], "blocks": [
                {"type": "p", "source": "mixed", "text": text, "assertions": []}]}]}}]}
        return [e for e in Checker(cfg, pack, words_floor=False).check(resp).errors if e.code == "V12"]
    assert errs("Gioca {{mv:C1}}, che perde {{loss:C1}}.")
    assert not errs("Gioca {{mv:C1}} ({{ev:C1}}).")
