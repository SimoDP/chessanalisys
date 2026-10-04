"""Feature fact with witness (§5.1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Feature:
    key: str
    side: str | None
    squares: list[str] = field(default_factory=list)
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
