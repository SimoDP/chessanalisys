"""User settings with precedence (§2-bis.1, D-56): command line > profile.yaml >
config/local.yaml > config/default.yaml; refusal of options not yet available (D-30)."""

from __future__ import annotations

from typing import Any

from chessanalyst.config import Config
from chessanalyst.errors import UsageError
from chessanalyst.profile import load_profile

COLOR_WORDS = {"bianco": "w", "b": "w", "w": "w", "white": "w", "nero": "b", "n": "b", "black": "b"}
DETAILS = (1, 2, 3, 4, 5)


def parse_color(value: str) -> str | None:
    """``bianco/b/w/white`` → ``w``; ``nero/n/black`` → ``b`` (case-insensitive)."""
    return COLOR_WORDS.get(value.strip().lower())


def check_available(cfg: Config, values: dict[str, Any]) -> None:
    """From M4 «entrambi», ``--elo-white``/``--elo-black`` and detail 1–5 are available (D-30); the chess.com
    scale stays refused while its table is empty."""
    if values.get("detail") is not None and values["detail"] not in DETAILS:
        raise UsageError(f"Dettaglio non valido: {values['detail']} (ammesso da 1 a 5)")
    if (values.get("elo_white") is not None or values.get("elo_black") is not None) and values.get("color") not in (None, "both"):
        raise UsageError("--elo-white e --elo-black valgono solo con --color both")
    if values.get("elo_scale") == "chesscom" and not cfg.elo_conversion.chesscom_to_lichess:
        raise UsageError("Scala chess.com non ancora configurata")


def effective(cfg: Config, cli: dict[str, Any] | None = None, use_profile: bool = True) -> dict[str, Any]:
    u = cfg.default.user
    values: dict[str, Any] = {
        "color": u.color, "elo": u.elo, "elo_scale": u.elo_scale, "opp_elo": u.opp_elo,
        "elo_white": u.elo_white, "elo_black": u.elo_black, "detail": u.detail_level,
        "budget": cfg.default.exploration.profile,
    }
    if use_profile:
        values.update({k: v for k, v in load_profile().items() if v is not None})
    values.update({k: v for k, v in (cli or {}).items() if v is not None})
    if values["color"] in ("white", "black"):
        values["color"] = "w" if values["color"] == "white" else "b"
    return values


def check_elo(cfg: Config, elo: int) -> bool:
    r = cfg.thresholds.elo_input
    return r.min <= elo <= r.max
