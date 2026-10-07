"""D-75: the numbers follow Stockfish (positive = better for White); the words stay from the user's side."""

from __future__ import annotations

import json

import yaml

from chessanalyst.render.format_it import eval_sign, fmt_eval
from chessanalyst.verify.resolve import Resolver


def test_default_is_stockfish_sign(root):
    raw = yaml.safe_load((root / "config" / "wording.yaml").read_text(encoding="utf-8"))
    assert raw["numbers"]["eval_sign"] == "white"
    assert eval_sign(raw, "b") == -1 and eval_sign(raw, "w") == 1
    assert eval_sign({"numbers": {"eval_sign": "user"}}, "b") == 1
    assert eval_sign({}, "b") == 1                      # v0.9.1 when the key is missing


def test_fmt_eval_with_sign():
    assert fmt_eval(639, sign=-1) == "-6,39"
    assert fmt_eval(-32, sign=-1) == "+0,32"
    assert fmt_eval(0, sign=-1) == "0,00"
    assert fmt_eval(0, 2, table=True, sign=-1) == "-#2"
    assert fmt_eval(0, -3, table=True, sign=-1) == "#3"
    assert fmt_eval(0, 2, opp_name="il Bianco", sign=-1) == "matto in 2 per te"   # words: user's side


def test_resolver_black_user(cfg, root):
    pack = json.loads((root / "fixtures" / "bench" / "knight_d6_b_1700.pack.json").read_text(encoding="utf-8"))
    assert pack["user"]["color"] == "b"
    cp, cid = pack["engine"]["root"]["eval_user_cp"], "N1"
    assert cp != 0
    user = Resolver(pack, dict(cfg.wording, numbers={"eval_sign": "user"})).resolve("{{ev:%s}}" % cid)
    white = Resolver(pack, dict(cfg.wording, numbers={"eval_sign": "white"})).resolve("{{ev:%s}}" % cid)
    assert user.value == white.value == (cp, None)          # verification still sees the user's side
    assert user.text == fmt_eval(cp) and white.text == fmt_eval(-cp)


def test_header_convention(cfg):
    from chessanalyst.render.report import CONVENTION
    assert "Bianco" in cfg.wording["header"][CONVENTION["white"]]
    assert cfg.wording["header"][CONVENTION["user"]] == cfg.wording["header"]["convention"]
