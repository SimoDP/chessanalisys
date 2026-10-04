"""FakeUCI: a tiny UCI engine that replays scripted ``info`` lines (AC-29).

Usage: ``python -m chessanalyst.engines.fake_uci <script.json>``

Script format::

    {"id_name": "Stockfish 19",
     "options": ["Threads", "Hash", "UCI_ShowWDL"],
     "events": [{"delay": 0.01, "line": "info depth 1 multipv 1 score cp 20 pv e2e4"}, ...],
     "bestmove": "e2e4"}

On ``go`` the events are emitted in order (each after its ``delay``); then
the engine waits for ``stop`` and answers ``bestmove``. Events after
``stop`` are discarded.
"""

from __future__ import annotations

import json
import sys
import threading
import time


def _out(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    script = json.loads(open(argv[0], encoding="utf-8").read())
    stop_evt = threading.Event()
    worker: threading.Thread | None = None
    lock = threading.Lock()

    def run_search() -> None:
        for ev in script.get("events", []):
            if stop_evt.wait(ev.get("delay", 0.0)):
                break
            with lock:
                if stop_evt.is_set():
                    break
                _out(ev["line"])
        stop_evt.wait()
        with lock:
            _out(f"bestmove {script.get('bestmove', '0000')}")

    for raw in sys.stdin:
        cmd = raw.strip()
        if cmd == "uci":
            _out(f"id name {script.get('id_name', 'FakeUCI')}")
            _out("id author chessanalyst tests")
            for opt in script.get("options", []):
                if opt in ("Threads", "Hash", "MultiPV"):
                    _out(f"option name {opt} type spin default 1 min 1 max 1024")
                else:
                    _out(f"option name {opt} type check default false")
            _out("uciok")
        elif cmd == "isready":
            _out("readyok")
        elif cmd.startswith("go"):
            stop_evt.clear()
            worker = threading.Thread(target=run_search, daemon=True)
            worker.start()
        elif cmd == "stop":
            stop_evt.set()
            if worker is not None:
                worker.join(timeout=5)
                worker = None
        elif cmd == "quit":
            stop_evt.set()
            break
        # setoption, position, ucinewgame: ignored
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
