"""Recording of the engine fixtures (Appendix G): ``pytest -m engines --record``.

Runs the M1a pipeline with the real Stockfish and Maia-2 on the example
position (user White, 1500/1900/2400 FIDE, profile ``deep``, E3 at ℓ1) and on
``najdorf_after_be3`` (opponent to move), each group with a fresh cache, then
dumps every search into ``fixtures/recorded/engine/<group>.json`` and every
Maia-2 answer into ``fixtures/recorded/maia/<group>.json``.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer
from chessanalyst.engines.factory import maia_models_dir, make_stockfish
from chessanalyst.engines.fake import RecordingMaiaBackend
from chessanalyst.engines.maia2 import Maia2Backend, MaiaEngine
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from chessanalyst.run import load_openings

GROUPS = {
    "najdorf": ("fixtures/positions/najdorf.fen", [("w", 1500), ("w", 1900), ("w", 2400)]),
    "najdorf_after_be3": ("fixtures/positions/najdorf_after_be3.fen", [("w", 1900)]),
}
PROFILE = "deep"


def record_fixtures(cfg: Config, time_scale: float = 0.5, progress: Callable[[str], None] = print) -> list[Path]:
    root = cfg.project_root
    m = cfg.default.engines.maia2
    backend = RecordingMaiaBackend(Maia2Backend(m.model_type, m.device, maia_models_dir(cfg)))
    openings = load_openings(cfg)
    written = []
    for group, (fen_file, runs) in GROUPS.items():
        backend.records.clear()
        with tempfile.TemporaryDirectory() as tmp:
            cache = Cache(Path(tmp) / "rec.sqlite")
            sf = make_stockfish(cfg).open()
            try:
                analyzer = CachedAnalyzer(sf, cache)
                maia = MaiaEngine(backend, cfg.maia2_limits, None)
                board = parse_fen((root / fen_file).read_text(encoding="utf-8"), cfg.wording["errors"])
                for color, elo in runs:
                    progress(f"== {group} · {color} · {elo} FIDE · {PROFILE}")
                    us = resolve_settings(cfg, color, elo, "fide", None, PROFILE)
                    analyse_position(cfg, Position(board=board.copy(), source="fen"), us, analyzer, maia, openings,
                                     progress=lambda s: progress(f"   {s}"), time_scale=time_scale)
            finally:
                sf.close()
            rows = cache.db.execute("SELECT key, result_json FROM sf ORDER BY key").fetchall()
            cache.close()
        eng = root / "fixtures" / "recorded" / "engine" / f"{group}.json"
        eng.write_text(json.dumps([{"key": k, "result": json.loads(r)} for k, r in rows], indent=0), encoding="utf-8")
        mai = root / "fixtures" / "recorded" / "maia" / f"{group}.json"
        mai.write_text(json.dumps(sorted(backend.records.values(), key=lambda r: (r["epd"], r["elo_self"], r["elo_oppo"])),
                                  indent=0), encoding="utf-8")
        written += [eng, mai]
        progress(f"   {len(rows)} ricerche, {len(backend.records)} chiamate a Maia-2")
    return written
