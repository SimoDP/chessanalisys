"""Saved user profile ``<config_dir>/chessanalyst/profile.yaml`` (§2-bis.1).

Written only by the interactive flow after confirmation; read by both flows.
Contains color, Elo, Elo scale, budget (detail from M4); never the position."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import platformdirs
import yaml

KEYS = ("color", "elo", "elo_scale", "budget", "detail")   # detail from M4


def profile_path() -> Path:
    base = os.environ.get("CHESSANALYST_CONFIG_DIR")
    return (Path(base) if base else Path(platformdirs.user_config_dir("chessanalyst"))) / "profile.yaml"


def load_profile() -> dict[str, Any]:
    p = profile_path()
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {k: v for k, v in data.items() if k in KEYS}


def save_profile(values: dict[str, Any]) -> Path:
    p = profile_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump({k: values[k] for k in KEYS if k in values}, sort_keys=False), encoding="utf-8")
    return p
