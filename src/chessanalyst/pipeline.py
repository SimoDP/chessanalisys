"""From a position and the user settings to the Evidence Pack (M1a, no LLM)."""

from __future__ import annotations

import time
from collections.abc import Callable

import chess

from chessanalyst import elo
from chessanalyst.config import Config
from chessanalyst.engines.cache import CachedAnalyzer
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.engines.openings import OpeningIndex
from chessanalyst.explore.runner import UserCtx, explore
from chessanalyst.features.profile import compute_profile, extract_features
from chessanalyst.inputs.position import Position
from chessanalyst.pack.builder import UserSettings, build_pack
from chessanalyst.pack.schema import Pack


def resolve_settings(cfg: Config, color: str, elo_declared: int, elo_scale: str, opp_elo: int | None,
                     budget: str, detail: int = 4) -> UserSettings:
    me = elo.resolve(elo_declared, elo_scale, cfg)
    opp = elo.resolve(opp_elo if opp_elo is not None else elo_declared, elo_scale, cfg)
    return UserSettings(
        color=chess.WHITE if color in ("w", "white") else chess.BLACK,
        elo_declared=me.declared, elo_scale=elo_scale, elo_ref_fide=me.ref_fide, elo_maia=me.maia,
        opp_elo_declared=opp.declared, opp_elo_maia=opp.maia,
        band=elo.band_of(me.ref_fide, cfg), anchor=elo.anchor_of(me.ref_fide, cfg),
        budget_profile=budget, detail_level=detail,
    )


def stockfish_info(engine, profile: str) -> dict:
    return {"version": engine.version, "threads": getattr(engine, "threads", None),
            "hash_mb": getattr(engine, "hash_mb", None), "profile": profile}


def analyse_position(cfg: Config, pos: Position, us: UserSettings, analyzer: CachedAnalyzer, maia: MaiaEngine,
                     openings: OpeningIndex | None, clock: Callable[[], float] = time.monotonic,
                     progress: Callable[[str], None] = lambda s: None, time_scale: float = 1.0) -> Pack:
    bp = cfg.thresholds.band_params[us.band]
    ctx = UserCtx(color=us.color, elo_maia=us.elo_maia, opp_elo_maia=us.opp_elo_maia, band=us.band, bp=bp,
                  profile_name=us.budget_profile)
    exp = explore(cfg, pos.board, ctx, analyzer, maia, clock=clock, progress=progress, time_scale=time_scale)
    lines = exp.root.result.lines
    feats = extract_features(pos.board, cfg, lines)
    entry = openings.lookup_epd(pos.board) if openings is not None else None
    opening = {"eco": entry["eco"], "name": entry["name"], "matched_by": "epd"} if entry else None
    profile = compute_profile(pos.board, cfg, lines, bp.K, feats, in_book=entry is not None,
                              quiet=exp.quiet, spread_cp=exp.spread_cp)
    return build_pack(cfg, pos, us, exp, maia.info(), feats, profile, opening,
                      stockfish_info(analyzer.engine, us.budget_profile), maia.bucket)
