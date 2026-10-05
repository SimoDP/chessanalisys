"""``chessanalyst ui`` (M6): the local server with synthetic engines and a recorded response — no network
beyond 127.0.0.1."""

from __future__ import annotations

import http.client
import json
import threading
import time

import pytest
import yaml

from chessanalyst.ui.server import App, make_server
from tests.m6_helpers import synthetic_stack

PGN2 = '[Event "a"]\n[White "X"]\n[Black "Y"]\n[WhiteElo "1700"]\n[BlackElo "1650"]\n\n1. e4 c5 2. Nf3 d6 *\n\n' \
       '[Event "b"]\n[White "Z"]\n[Black "W"]\n\n1. d4 d5 *\n'


@pytest.fixture
def server(cfg, tmp_path, monkeypatch):
    synthetic_stack(cfg, monkeypatch, tmp_path)
    app = App(cfg, tmp_path / "out")
    srv = make_server(app, 0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield app, srv.server_address[1]
    srv.shutdown()
    srv.server_close()


def call(port, method, path, body=None, token=None, host=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    h = {"Host": host or f"127.0.0.1:{port}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if token:
        h["X-Token"] = token
    h.update(headers or {})
    c.request(method, path, body=data, headers=h)
    r = c.getresponse()
    raw = r.read()
    c.close()
    ctype = r.getheader("Content-Type", "")
    return r.status, (json.loads(raw) if ctype.startswith("application/json") else raw.decode("utf-8")), r


def wait(port, job):
    for _ in range(600):
        st, j, _ = call(port, "GET", f"/api/job/{job}")
        if j["state"] != "running":
            return j
        time.sleep(0.05)
    raise AssertionError("analysis did not finish")


def test_page_and_guards(server):
    app, port = server
    st, page, r = call(port, "GET", "/")
    assert st == 200 and app.token in page and "/*DATA*/" not in page and 'id="white-king"' in page
    assert "default-src 'none'" in r.getheader("Content-Security-Policy")
    assert call(port, "GET", "/", host="evil.example:80")[0] == 403                  # DNS rebinding
    assert call(port, "POST", "/api/preview", {"method": "example"})[0] == 403        # no token
    assert call(port, "POST", "/api/preview", {"method": "example"}, token="x")[0] == 403
    assert call(port, "POST", "/api/preview", {"method": "example"}, token=app.token,
                headers={"Origin": "http://evil.example"})[0] == 403
    big = {"method": "pgn", "text": "x" * (app.cfg.default.ui.max_request_kb * 1024 + 1)}
    assert call(port, "POST", "/api/preview", big, token=app.token)[0] == 413
    assert call(port, "GET", "/a/../conf/analysis.md")[0] == 404
    assert call(port, "GET", "/a/%2e%2e/analysis.md")[0] == 404


def test_preview(server):
    app, port = server
    st, j, _ = call(port, "POST", "/api/preview", {"method": "example"}, token=app.token)
    assert st == 200 and j["fen"].startswith("rnbqkb1r/1p2pppp") and j["tag_elos"] is None
    assert dict(j["rows"])["Apertura"].startswith("B90")
    st, j, _ = call(port, "POST", "/api/preview", {"method": "pgn", "text": PGN2}, token=app.token)
    assert st == 200 and [g["index"] for g in j["games"]] == [1, 2]                   # choose the game
    st, j, _ = call(port, "POST", "/api/preview", {"method": "pgn", "text": PGN2, "game": 1, "at": "2w"},
                    token=app.token)
    assert st == 200 and j["tag_elos"] == {"w": 1700, "b": 1650} and j["last"] == "g1f3"
    st, j, _ = call(port, "POST", "/api/preview", {"method": "fen", "text": "8/8/8 w - - 0 1"}, token=app.token)
    assert st == 400 and j["error"]
    st, j, _ = call(port, "POST", "/api/preview", {"method": "example", "elo": "99999"}, token=app.token)
    assert st == 400 and "Elo non valido" in j["error"]
    st, j, _ = call(port, "POST", "/api/preview", {"method": "example", "detail": "9"}, token=app.token)
    assert st == 400


def test_analysis_list_files_and_profile(server, tmp_path):
    app, port = server
    st, j, _ = call(port, "POST", "/api/analyze", {"method": "example", "color": "white", "elo": "1900",
                                                   "budget": "fast", "detail": "4"}, token=app.token)
    assert st == 202
    done = wait(port, j["job"])
    assert done["state"] == "done" and done["messages"], done
    name = done["folder"]
    st, xs, _ = call(port, "GET", "/api/analyses")
    assert [a["name"] for a in xs] == [name] and xs[0]["html"] and xs[0]["title"].startswith("Analisi della posizione")
    st, page, _ = call(port, "GET", f"/a/{name}/analysis.html")
    assert st == 200 and 'class="mv"' in page
    st, pgn, r = call(port, "GET", f"/a/{name}/export.pgn")
    assert st == 200 and '[SetUp "1"]' in pgn and name in r.getheader("Content-Disposition")
    assert call(port, "GET", f"/a/{name}/pack.json")[0] == 404                       # only the listed files
    assert call(port, "GET", f"/a/{name}/run.log")[0] == 404
    prof = yaml.safe_load((tmp_path / "conf" / "profile.yaml").read_text(encoding="utf-8"))
    assert prof == {"color": "w", "elo": 1900, "elo_scale": "fide", "budget": "fast", "detail": 4}


def test_both_colors(server):
    app, port = server
    st, j, _ = call(port, "POST", "/api/analyze", {"method": "example", "color": "both", "elo_white": "1900",
                                                   "elo_black": "1500", "budget": "fast"}, token=app.token)
    done = wait(port, j["job"])
    assert done["state"] == "done", done
    st, page, _ = call(port, "GET", f"/a/{done['folder']}/analysis.html")
    assert page.count('<section class="part">') == 2


def test_one_analysis_at_a_time_and_errors(cfg, tmp_path, monkeypatch):
    synthetic_stack(cfg, monkeypatch, tmp_path)
    gate = threading.Event()

    def runner(pos, us, progress):
        progress("E0")
        gate.wait(10)
        from chessanalyst.errors import ModelError

        raise ModelError("Nessuna risposta valida del modello dopo i retry")

    app = App(cfg, tmp_path / "out", runner=runner)
    srv = make_server(app, 0)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        body = {"method": "example", "budget": "fast"}
        st, j, _ = call(port, "POST", "/api/analyze", body, token=app.token)
        assert st == 202
        assert call(port, "POST", "/api/analyze", body, token=app.token)[0] == 409
        gate.set()
        done = wait(port, j["job"])
        assert done["state"] == "error" and "Nessuna risposta valida" in done["error"]
        assert done["messages"] == ["Motori in esecuzione … (E0)"]
    finally:
        srv.shutdown()
        srv.server_close()
