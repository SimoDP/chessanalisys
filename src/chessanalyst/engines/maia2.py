"""Maia-2 adapter: the only module that imports ``maia2`` (CLAUDE.md, §3.2).

Verified in M0 on ``maia2`` 0.11.0 (details in docs/MAIA2_NOTES.md):

* ``maia2.model.from_pretrained(type, device="auto", save_root=...)`` downloads
  the weights from Google Drive (``gdown``) into ``save_root`` and loads them;
* ``maia2.inference.prepare()`` and
  ``inference_each(model, prepared, fen, elo_self, elo_oppo)`` return
  ``(move_probs, win_prob)``: ``move_probs`` maps UCI → probability over the
  legal moves (rounded to 4 decimals by the package); ``win_prob`` is from
  **White's** point of view (the package computes it for the side to move on
  the mirrored board and returns ``1 - v`` when Black is to move);
* Elo buckets (``utils.map_to_category``): 0 below 1100, then one per 100
  points, 10 for ≥ 2000.
"""

from __future__ import annotations

import contextlib
import io
import logging
import math
from pathlib import Path
from typing import Any, Protocol

import chess

from chessanalyst.config import Maia2LimitsCfg
from chessanalyst.engines.cache import Cache, maia_key

log = logging.getLogger(__name__)


def bucket(elo: int, limits: Maia2LimitsCfg) -> int:
    """Maia-2 Elo bucket, from config/maia2_limits.yaml."""
    top_index = 1 + (limits.top_bucket_lower - limits.first_bucket_upper) // limits.bucket_width
    if elo < limits.first_bucket_upper:
        return 0
    if elo >= limits.top_bucket_lower:
        return top_index
    return 1 + (elo - limits.first_bucket_upper) // limits.bucket_width


def top_bucket(limits: Maia2LimitsCfg) -> int:
    return bucket(limits.top_bucket_lower, limits)


def saturated(elo_maia: int, limits: Maia2LimitsCfg) -> bool:
    """D-24: single rule, no branches elsewhere."""
    return elo_maia >= limits.top_bucket_lower


def normalize_policy(board: chess.Board, raw: dict[str, float]) -> dict[str, float]:
    """All legal moves (missing ones at 0), illegal keys dropped (logged), sum 1."""
    legal = {m.uci() for m in board.legal_moves}
    out = {u: 0.0 for u in legal}
    for uci, p in raw.items():
        if uci in legal:
            out[uci] = float(p)
        else:
            log.warning("Maia-2: mossa non legale scartata %s in %s", uci, board.fen())
    total = sum(out.values())
    if total <= 0:
        n = len(out)
        return {u: 1.0 / n for u in out} if n else {}
    return {u: p / total for u, p in out.items()}


def entropy_bits(policy: dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in policy.values() if p > 0)


class MaiaBackend(Protocol):
    """What the adapter needs from the underlying package (real or fake)."""

    package_version: str
    model_type: str
    device: str

    def infer(self, fen: str, elo_self: int, elo_oppo: int) -> tuple[dict[str, float], float]:
        """Raw ``(move_probs, win_prob_white)``."""


class Maia2Backend:
    """Real ``maia2`` package. Loading triggers the weights download if missing."""

    def __init__(self, model_type: str, device: str, models_dir: Path) -> None:
        try:
            import maia2  # noqa: F401
            from maia2 import inference, model
        except ImportError as e:  # pragma: no cover - environment dependent
            from chessanalyst.errors import EnvironmentProblem

            raise EnvironmentProblem(f"Pacchetto maia2 non installato: {e}") from e
        import torch

        self._inference = inference
        self.package_version = getattr(maia2, "__version__", "unknown")
        self.model_type = model_type
        models_dir.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):   # the package prints download/loading messages
            self._model = model.from_pretrained(type=model_type, device=device, save_root=str(models_dir))
        log.info("maia2: %s", buf.getvalue().strip())
        self.device = str(next(self._model.parameters()).device)
        self._prepared = inference.prepare()
        self._torch = torch

    def infer(self, fen: str, elo_self: int, elo_oppo: int) -> tuple[dict[str, float], float]:
        return self._inference.inference_each(self._model, self._prepared, fen, elo_self, elo_oppo)


def weights_file(models_dir: Path, model_type: str) -> Path:
    """Where ``from_pretrained`` stores the weights (``<type>_model.pt``)."""
    return models_dir / f"{model_type}_model.pt"


class MaiaEngine:
    """Adapter of §3.2: ``policy``, ``expected_score``, ``bucket``, ``saturated``, ``info``."""

    def __init__(self, backend: MaiaBackend, limits: Maia2LimitsCfg, cache: Cache | None = None) -> None:
        self.backend = backend
        self.limits = limits
        self.cache = cache
        self.calls = 0

    def _query(self, fen: str, elo_self: int, elo_oppo: int) -> dict[str, Any]:
        board = chess.Board(fen)
        epd = board.epd(en_passant="legal")
        key = maia_key(epd, elo_self, elo_oppo, self.backend.model_type, self.backend.package_version)
        if self.cache is not None:
            hit = self.cache.get_maia(key)
            if hit is not None:
                return hit
        self.calls += 1
        # The model ignores clocks: query on the EPD with neutral counters.
        probs, win_white = self.backend.infer(epd + " 0 1", elo_self, elo_oppo)
        policy = normalize_policy(board, probs)
        win_white = float(win_white)
        score = win_white if board.turn == chess.WHITE else 1.0 - win_white
        result = {"policy": policy, "expected_score": score}
        if self.cache is not None:
            self.cache.put_maia(key, result)
        return result

    def policy(self, fen: str, elo_self: int, elo_oppo: int) -> dict[str, float]:
        return dict(self._query(fen, elo_self, elo_oppo)["policy"])

    def expected_score(self, fen: str, elo_self: int, elo_oppo: int) -> float:
        """Expected result for the side to move, in [0, 1]."""
        return float(self._query(fen, elo_self, elo_oppo)["expected_score"])

    def bucket(self, elo: int) -> int:
        return bucket(elo, self.limits)

    def saturated(self, elo: int) -> bool:
        return saturated(elo, self.limits)

    def info(self) -> dict[str, str]:
        return {
            "package_version": self.backend.package_version,
            "model_type": self.backend.model_type,
            "device": self.backend.device,
        }
