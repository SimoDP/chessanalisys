"""Recording of the engine fixtures (Appendix G): ``pytest -m engines --record``.

Runs the pipeline with the real Stockfish, Maia-2 and Syzygy tables on the
example position (user White, 1500/1900/2400 FIDE, profile ``deep``, E3 at
ℓ1–ℓ3 from M2), on ``najdorf_after_be3`` (opponent to move) and on the M2
positions (Fried Liver from a PGN, rook endgame, Lucena with the tablebase),
each group with a fresh cache, then dumps every search into
``fixtures/recorded/engine/<group>.json``, every Maia-2 answer into
``fixtures/recorded/maia/<group>.json`` and every tablebase probe into
``fixtures/recorded/syzygy/<group>.json``.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path

from chessanalyst.config import Config
from chessanalyst.engines.cache import Cache, CachedAnalyzer, sf_key
from chessanalyst.engines.factory import maia_models_dir, make_stockfish, make_tablebase
from chessanalyst.engines.fake import RecordingMaiaBackend
from chessanalyst.engines.maia2 import Maia2Backend, MaiaEngine
from chessanalyst.engines.types import NodeResult
from chessanalyst.inputs.position import Position
from chessanalyst.pipeline import analyse_position, resolve_settings
from chessanalyst.run import load_openings

GROUPS = {
    # the standard run (same cache, after deep) records the searches a lighter profile adds (AC-14)
    "najdorf": ("fixtures/positions/najdorf.fen", [("w", 1500), ("w", 1900), ("w", 2400), ("w", 1900, "standard")]),
    "najdorf_after_be3": ("fixtures/positions/najdorf_after_be3.fen", [("w", 1900)]),
    "fried_liver": ("fixtures/pgn/fried_liver.pgn", [("w", 1500)]),
    "rook_endgame": ("fixtures/positions/rook_endgame.fen", [("w", 1900)]),
    "lucena": ("fixtures/positions/lucena.fen", [("w", 1900)]),
}
PROFILE = "deep"


def group_position(cfg: Config, path: Path) -> Position:
    """The position of a recording group: a FEN file, or the end of a PGN (history kept)."""
    from chessanalyst.golden.packs import GoldenPack, spec_position

    return spec_position(cfg, GoldenPack(path.stem, str(path.relative_to(cfg.project_root)), "w", 0))


def _stopped_clock() -> float:
    """Exploration clock of the recordings: the global deadline (§3-ter.2) never cuts the tree, so the
    fixtures cover every node that a replay with instant fake engines requests. Each search still
    stops at its own ``t_target``/``t_cap``."""
    return 0.0


class _RecordingEngine:
    """Stockfish for the recordings; keeps every search (not only the cached ones).

    ``patient_cap_s``: in a group with several runs on the same cache, a search below the minimum depth
    would be repeated by a later run and the replays of the first run would request another tree. There
    every search waits for the minimum depth, up to this cap (the global deadline of the profile, so a
    tablebase position that never gets there cannot block the recording)."""

    def __init__(self, engine, patient_cap_s: float | None = None) -> None:
        self.engine = engine
        self.version = engine.version
        self.patient_cap_s = patient_cap_s
        self.results: list[tuple[str, NodeResult]] = []

    def analyse_node(self, board, multipv, t_target, d_min, t_cap, root_moves=None):
        if self.patient_cap_s is not None:
            t_cap = max(t_cap, self.patient_cap_s)
        res = self.engine.analyse_node(board, multipv, t_target, d_min, t_cap, root_moves=root_moves)
        self.results.append((sf_key(self.version, board, [m.uci() for m in root_moves] if root_moves else None), res))
        return res


def record_fixtures(cfg: Config, time_scale: float = 1.0, progress: Callable[[str], None] = print,
                    groups: list[str] | None = None, extend: bool = False) -> list[Path]:
    """``extend``: start from the recorded searches of the group (loaded into the cache), so that only
    the searches missing from the fixtures are run (e.g. after adding a run to a group)."""
    root = cfg.project_root
    m = cfg.default.engines.maia2
    backend = RecordingMaiaBackend(Maia2Backend(m.model_type, m.device, maia_models_dir(cfg)))
    openings = load_openings(cfg)
    written = []
    for group, (pos_file, runs) in GROUPS.items():
        if groups and group not in groups:
            continue
        backend.records.clear()
        tb = make_tablebase(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            cache = Cache(Path(tmp) / "rec.sqlite")
            eng = root / "fixtures" / "recorded" / "engine" / f"{group}.json"
            rows: list[dict] = []
            if extend and eng.is_file():
                rows = json.loads(eng.read_text(encoding="utf-8"))
                for row in rows:
                    cache.put_sf(row["key"], NodeResult.from_dict(row["result"]))
            sf = make_stockfish(cfg).open()
            try:
                prof = cfg.exploration.profiles[PROFILE]
                cap = prof.deadline_factor * prof.B_s * time_scale if len(runs) > 1 else None
                patient = _RecordingEngine(sf, cap)
                analyzer = CachedAnalyzer(patient, cache)
                maia = MaiaEngine(backend, cfg.maia2_limits, None)
                pos = group_position(cfg, root / pos_file)
                for color, elo, *prof in runs:
                    profile = prof[0] if prof else PROFILE
                    progress(f"== {group} · {color} · {elo} FIDE · {profile}")
                    us = resolve_settings(cfg, color, elo, "fide", None, profile)
                    analyse_position(cfg, pos, us, analyzer, maia, openings, progress=lambda s: progress(f"   {s}"),
                                     time_scale=time_scale, tablebase=tb, clock=_stopped_clock)
            finally:
                sf.close()
                if tb is not None:
                    tb.close()
            cache.close()
        rows += [{"key": k, "result": r.to_dict()} for k, r in patient.results]
        rows.sort(key=lambda r: (r["key"], r["result"]["multipv"], r["result"]["depth"]))
        eng.write_text(json.dumps(rows, indent=0), encoding="utf-8")
        mai = root / "fixtures" / "recorded" / "maia" / f"{group}.json"
        mai.write_text(json.dumps(sorted(backend.records.values(), key=lambda r: (r["epd"], r["elo_self"], r["elo_oppo"])),
                                  indent=0), encoding="utf-8")
        written += [eng, mai]
        if tb is not None and tb.records:
            syz = root / "fixtures" / "recorded" / "syzygy" / f"{group}.json"
            syz.parent.mkdir(parents=True, exist_ok=True)
            syz.write_text(json.dumps(tb.records, indent=0, sort_keys=True), encoding="utf-8")
            written.append(syz)
        progress(f"   {len(rows)} ricerche, {len(backend.records)} chiamate a Maia-2")
    return written
