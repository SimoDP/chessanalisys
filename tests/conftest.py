from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from chessanalyst.config import Config, load_config

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption("--record", action="store_true", default=False,
                     help="rigenera fixtures/recorded/{engine,maia} con i motori veri (con -m engines)")


@pytest.fixture(autouse=True)
def _no_real_api(request, monkeypatch):
    """The default suite never reaches the API: the key is hidden unless a test is marked ``llm``."""
    if "llm" not in request.keywords:
        for var in ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
            monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def cfg() -> Config:
    return load_config(ROOT)


def uci_iterations(
    depths: range | list[int],
    lines: list[tuple[str, str]],
    delay: float = 0.01,
) -> list[dict]:
    """Complete MultiPV iterations: ``lines`` = [(score, pv), ...] per rank."""
    events = []
    for d in depths:
        for rank, (score, pv) in enumerate(lines, 1):
            events.append({
                "delay": delay if rank == 1 else 0.0,
                "line": f"info depth {d} seldepth {d + 2} multipv {rank} score {score} "
                        f"wdl 100 850 50 nodes {1000 * d} nps 100000 time {10 * d} pv {pv}",
            })
    return events


@pytest.fixture
def fake_uci(tmp_path):
    """Return a factory: events → command list starting FakeUCI on a script."""

    def make(events: list[dict], id_name: str = "Stockfish 16", bestmove: str = "e2e4") -> list[str]:
        script = {"id_name": id_name, "options": ["Threads", "Hash", "MultiPV", "UCI_ShowWDL"],
                  "events": events, "bestmove": bestmove}
        path = tmp_path / f"script_{len(list(tmp_path.glob('script_*.json')))}.json"
        path.write_text(json.dumps(script), encoding="utf-8")
        return [sys.executable, "-m", "chessanalyst.engines.fake_uci", str(path)]

    return make
