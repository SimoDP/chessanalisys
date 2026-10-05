"""``chessanalyst ui`` (M6): a page in the browser for the same flow as the interactive command line —
position (example, FEN, PGN), settings, confirmation with the board (§2-bis.5), analysis with progress, list of
the saved analyses with the page of each one and the exports.

Standard library only (``http.server``). The server listens on 127.0.0.1 only and accepts a request only if
its Host is the server itself (no DNS rebinding); the POST requests also need the token of the page, which other
sites cannot read. Files are served only from the folders of the output directory, by name, never by path.
"""

from __future__ import annotations

import json
import logging
import secrets
import threading
import uuid
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

import chess
import chess.svg

from chessanalyst.config import Config
from chessanalyst.errors import AnalystError, InputError, UsageError

log = logging.getLogger(__name__)

HOST = "127.0.0.1"                      # never another interface: the UI has no authentication
SERVED = {"analysis.html": "text/html; charset=utf-8", "analysis.md": "text/markdown; charset=utf-8"}
EXPORT_TYPES = {"html": "text/html; charset=utf-8", "md": "text/markdown; charset=utf-8",
                "pgn": "application/x-chess-pgn; charset=utf-8"}
CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
       "connect-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'")


@dataclass
class Job:
    id: str
    state: str = "running"              # running | done | error
    messages: list[str] = field(default_factory=list)
    folder: str | None = None
    error: str | None = None


class App:
    """State of the server: the configuration, the output directory, the jobs (one analysis at a time: the
    engines use the whole machine)."""

    def __init__(self, cfg: Config, out_base: Path, runner: Callable | None = None) -> None:
        self.cfg = cfg
        self.out_base = out_base
        self.token = secrets.token_urlsafe(24)
        self.jobs: dict[str, Job] = {}
        self.lock = threading.Lock()
        self.runner = runner            # tests: a function(pos, us, progress) -> Path

    # -- analyses on disk ------------------------------------------------------------------------------------

    def folder(self, name: str) -> Path | None:
        """The analysis folder called ``name``, if it is a direct child of the output directory."""
        if not self.out_base.is_dir():
            return None
        for p in self.out_base.iterdir():
            if p.name == name and p.is_dir():
                return p
        return None

    def analyses(self) -> list[dict[str, Any]]:
        if not self.out_base.is_dir():
            return []
        out = []
        for p in self.out_base.iterdir():
            md = p / "analysis.md"
            if not p.is_dir() or not md.is_file():
                continue
            title = next((ln[2:].strip() for ln in md.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")),
                         p.name)
            out.append({"name": p.name, "title": title, "mtime": md.stat().st_mtime,
                        "html": (p / "analysis.html").is_file(),
                        "both": (p / "pack_white.json").is_file()})
        return sorted(out, key=lambda a: -a["mtime"])

    # -- position and settings ---------------------------------------------------------------------------------

    def preview(self, req: dict[str, Any]) -> dict[str, Any]:
        from chessanalyst.engines.openings import opening_entry
        from chessanalyst.inputs.confirm import castling_text
        from chessanalyst.inputs.pgn import game_infos, read_games
        from chessanalyst.interactive import tag_elos
        from chessanalyst.run import load_openings

        method = req.get("method") or "example"
        games = []
        if method == "pgn" and (req.get("text") or "").strip():
            games = read_games(req["text"])
            if len(games) > 1 and not req.get("game"):
                return {"games": [{"index": g.index, "label": f"{g.white} - {g.black} · {g.event} {g.date} · "
                                                             f"{g.plies} semimosse · {g.result}"}
                                  for g in game_infos(games)]}
        pos = self.position(req)
        b = pos.board
        entry = opening_entry(load_openings(self.cfg), b)
        ep = chess.square_name(b.ep_square) if b.ep_square is not None and b.has_legal_en_passant() else "nessuna"
        rows = [["FEN", pos.fen], ["Tratto", "il Bianco" if b.turn == chess.WHITE else "il Nero"]]
        if pos.source == "pgn":
            rows.append(["Ultima mossa", f"{pos.last_move_san or 'nessuna'} · semimosse giocate: {pos.plies}"])
        rows.append(["Apertura", f"{entry['eco']} {entry['name']}" if entry else "non riconosciuta"])
        rows.append(["Arrocco", f"{castling_text(b)} · en passant: {ep}"])
        last = b.peek().uci() if b.move_stack else None
        return {"fen": pos.fen, "rows": rows, "last": last, "tag_elos": tag_elos(pos)}

    def position(self, req: dict[str, Any]):
        from chessanalyst.inputs.load import load_position

        method = req.get("method") or "example"
        if method not in ("example", "fen", "pgn"):
            raise UsageError(f"Metodo non valido: {method}")
        game = int(req["game"]) if req.get("game") else None
        return load_position(self.cfg, method, req.get("text") if method != "example" else None, game_no=game,
                             at=(req.get("at") or None) if method == "pgn" else None)

    def settings(self, req: dict[str, Any]) -> dict[str, Any]:
        """The values of the form with the same checks as the command line (D-30)."""
        from chessanalyst.settings import check_available, check_elo, effective

        def num(key):
            v = req.get(key)
            if v in (None, ""):
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                raise UsageError(f"Valore non valido per {key}: {v}") from None

        color = {"white": "w", "black": "b", "both": "both"}.get(req.get("color") or "", None)
        cli = {"color": color, "elo": num("elo"), "opp_elo": num("opp_elo"), "elo_white": num("elo_white"),
               "elo_black": num("elo_black"), "elo_scale": req.get("elo_scale") or None,
               "budget": req.get("budget") or None, "detail": num("detail")}
        if cli["elo_scale"] not in (None, "fide", "lichess", "chesscom"):
            raise UsageError(f"Scala non valida: {cli['elo_scale']}")
        if cli["budget"] not in (None, "fast", "standard", "deep"):
            raise UsageError(f"Budget non valido: {cli['budget']}")
        if color != "both":
            cli["elo_white"] = cli["elo_black"] = None
        check_available(self.cfg, cli)
        values = effective(self.cfg, cli)
        check_available(self.cfg, values)
        if values["color"] == "both":
            values["opp_elo"] = None
        for key in ("elo", "opp_elo", "elo_white", "elo_black"):
            if values.get(key) is not None and not check_elo(self.cfg, values[key]):
                r = self.cfg.thresholds.elo_input
                raise UsageError(f"Elo non valido: {values[key]} (ammesso tra {r.min} e {r.max})")
        return values

    def defaults(self) -> dict[str, Any]:
        from chessanalyst.settings import effective

        v = effective(self.cfg)
        r = self.cfg.thresholds.elo_input
        return {"color": {"w": "white", "b": "black"}.get(v["color"], v["color"]), "elo": v["elo"],
                "opp_elo": v.get("opp_elo"), "elo_white": v.get("elo_white"), "elo_black": v.get("elo_black"),
                "elo_scale": v["elo_scale"], "budget": v["budget"], "detail": v["detail"],
                "elo_min": r.min, "elo_max": r.max, "poll_ms": self.cfg.default.ui.poll_ms,
                "chesscom": bool(self.cfg.elo_conversion.chesscom_to_lichess)}

    # -- analysis -----------------------------------------------------------------------------------------------

    def start(self, req: dict[str, Any]) -> Job:
        from chessanalyst.profile import save_profile

        from chessanalyst.cli import _settings_from

        values = self.settings(req)
        pos = self.position(req)
        us = _settings_from(self.cfg, values)
        with self.lock:
            if any(j.state == "running" for j in self.jobs.values()):
                raise Busy()
            job = Job(uuid.uuid4().hex)
            self.jobs[job.id] = job
        # as in the interactive flow: the profile is saved after the confirmation, never the position
        save_profile({"color": values["color"], "elo": values["elo"], "elo_scale": values["elo_scale"],
                      "budget": values["budget"], "detail": values["detail"]})
        threading.Thread(target=self._run, args=(job, pos, us), daemon=True).start()
        return job

    def _run(self, job: Job, pos, us) -> None:
        def progress(s: str) -> None:
            job.messages.append("Modello di linguaggio in esecuzione …" if s.startswith("modello di linguaggio")
                                else f"Motori in esecuzione … ({s})")

        try:
            if self.runner is not None:
                outdir = self.runner(pos, us, progress)
            else:
                from chessanalyst.run import run_analysis

                outdir = run_analysis(self.cfg, pos, us, self.out_base, progress=progress)
            job.folder = Path(outdir).name
            job.state = "done"
        except AnalystError as e:
            job.error, job.state = str(e), "error"
        except Exception:                              # noqa: BLE001 — a bug: the trace goes to the log
            log.exception("Analisi interrotta")
            job.error, job.state = "Errore inatteso: vedi run.log", "error"


class Busy(Exception):
    pass


def _page(app: App) -> str:
    html = resources.files("chessanalyst.ui").joinpath("index.html").read_text(encoding="utf-8")
    data = json.dumps({"token": app.token, "defaults": app.defaults()}).replace("</", "<\\/")
    return (html.replace("/*DATA*/null", data)
            .replace("<!--PIECES-->", "".join(chess.svg.PIECES.values())))


def make_handler(app: App, port_ref: list[int]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "chessanalyst"
        sys_version = ""

        def log_message(self, fmt: str, *args) -> None:       # at DEBUG, never the bodies
            # the page polls the job every ui.poll_ms: those requests would fill run.log of the running analysis
            if self.command == "GET" and urlsplit(self.path).path.startswith("/api/job/"):
                return
            log.debug("ui: " + fmt, *args)

        # -- helpers -------------------------------------------------------------------------------------------
        def _host_ok(self) -> bool:
            host = self.headers.get("Host", "")
            return host in (f"{HOST}:{port_ref[0]}", f"localhost:{port_ref[0]}")

        def _send(self, status: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", CSP)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, data: Any) -> None:
            self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _error(self, status: int, message: str) -> None:
            self._json(status, {"error": message})

        # -- GET -------------------------------------------------------------------------------------------------
        def do_GET(self) -> None:  # noqa: N802
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "Host non ammesso")
            path = urlsplit(self.path).path
            if path == "/":
                return self._send(HTTPStatus.OK, _page(app).encode("utf-8"), "text/html; charset=utf-8")
            if path == "/api/analyses":
                return self._json(HTTPStatus.OK, app.analyses())
            if path.startswith("/api/job/"):
                job = app.jobs.get(path.rsplit("/", 1)[1])
                if job is None:
                    return self._error(HTTPStatus.NOT_FOUND, "Analisi non trovata")
                return self._json(HTTPStatus.OK, job.__dict__)
            parts = [unquote(p) for p in path.split("/")]
            if len(parts) == 4 and parts[1] == "a":
                return self._file(parts[2], parts[3])
            return self._error(HTTPStatus.NOT_FOUND, "Pagina non trovata")

        do_HEAD = do_GET

        def _file(self, name: str, file: str) -> None:
            folder = app.folder(name)
            if folder is None:
                return self._error(HTTPStatus.NOT_FOUND, "Analisi non trovata")
            if file in SERVED:
                p = folder / file
                if not p.is_file():
                    return self._error(HTTPStatus.NOT_FOUND, "File non trovato")
                return self._send(HTTPStatus.OK, p.read_bytes(), SERVED[file])
            fmt = file.removeprefix("export.")
            if file.startswith("export.") and fmt in EXPORT_TYPES:
                from chessanalyst.export import export

                try:
                    dest = export(app.cfg, folder, fmt)
                except AnalystError as e:
                    return self._error(HTTPStatus.CONFLICT, str(e))
                return self._send(HTTPStatus.OK, dest.read_bytes(), EXPORT_TYPES[fmt],
                                  {"Content-Disposition": f'attachment; filename="{dest.name}"'})
            return self._error(HTTPStatus.NOT_FOUND, "File non trovato")

        # -- POST ------------------------------------------------------------------------------------------------
        def do_POST(self) -> None:  # noqa: N802
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "Host non ammesso")
            origin = self.headers.get("Origin")
            if origin is not None and origin not in (f"http://{HOST}:{port_ref[0]}", f"http://localhost:{port_ref[0]}"):
                return self._error(HTTPStatus.FORBIDDEN, "Origine non ammessa")
            if not secrets.compare_digest(self.headers.get("X-Token", ""), app.token):
                return self._error(HTTPStatus.FORBIDDEN, "Token mancante o non valido: ricarica la pagina")
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Serve JSON")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > app.cfg.default.ui.max_request_kb * 1024:
                return self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Richiesta troppo grande")
            try:
                req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if not isinstance(req, dict):
                    raise ValueError
            except (ValueError, UnicodeDecodeError):
                return self._error(HTTPStatus.BAD_REQUEST, "JSON non valido")
            path = urlsplit(self.path).path
            try:
                if path == "/api/preview":
                    app.settings(req)                  # the settings are checked before the confirmation
                    return self._json(HTTPStatus.OK, app.preview(req))
                if path == "/api/analyze":
                    return self._json(HTTPStatus.ACCEPTED, {"job": app.start(req).id})
            except Busy:
                return self._error(HTTPStatus.CONFLICT, "C'è già un'analisi in corso: attendi che finisca")
            except (InputError, UsageError, AnalystError) as e:
                return self._error(HTTPStatus.BAD_REQUEST, str(e))
            except Exception:                          # noqa: BLE001
                log.exception("ui: errore inatteso")
                return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "Errore inatteso: vedi il log")
            return self._error(HTTPStatus.NOT_FOUND, "Pagina non trovata")

    return Handler


def make_server(app: App, port: int) -> ThreadingHTTPServer:
    port_ref = [port]
    server = ThreadingHTTPServer((HOST, port), make_handler(app, port_ref))
    server.daemon_threads = True
    port_ref[0] = server.server_address[1]           # port 0: the one the system chose
    return server


def serve(cfg: Config, out_base: Path, port: int | None = None, open_browser: bool | None = None,
          announce: Callable[[str], None] = print) -> None:
    app = App(cfg, out_base)
    server = make_server(app, cfg.default.ui.port if port is None else port)
    url = f"http://{HOST}:{server.server_address[1]}/"
    announce(f"Interfaccia locale su {url} (Ctrl-C per chiudere)")
    if cfg.default.ui.open_browser if open_browser is None else open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if any(j.state == "running" for j in app.jobs.values()):
            announce("Analisi in corso interrotta: il pacchetto, se già scritto, resta nella cartella (usa rerun)")
