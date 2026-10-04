"""Helpers for acceptance tests."""

from __future__ import annotations

from typing import Any

from chessanalyst.config import Config


def with_profile(cfg: Config, name: str, **changes: Any) -> Config:
    """Copy of ``cfg`` with fields of exploration profile ``name`` replaced."""
    prof = cfg.exploration.profiles[name].model_copy(update=changes)
    profiles = dict(cfg.exploration.profiles)
    profiles[name] = prof
    exploration = cfg.exploration.model_copy(update={"profiles": profiles})
    return cfg.model_copy(update={"exploration": exploration})
