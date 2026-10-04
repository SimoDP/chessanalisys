"""AC-19: doctor reports missing engine, version different from the pin,
missing API key, device, and prints the elo_maia/saturated table."""

from __future__ import annotations

import chess

from chessanalyst.doctor import ERR, OK, WARN, run_doctor
from chessanalyst.engines.fake import FakeMaiaBackend
from chessanalyst.engines.maia2 import MaiaEngine
from chessanalyst.engines.stockfish import StockfishEngine
from chessanalyst.errors import EnvironmentProblem
from tests.conftest import uci_iterations

NAJDORF = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"


def fake_maia(cfg):
    epd = chess.Board(NAJDORF).epd(en_passant="legal")
    backend = FakeMaiaBackend({(epd, 1500, 1500): ({"c1e3": 0.3, "f1e2": 0.2}, 0.55)})
    return MaiaEngine(backend, cfg.maia2_limits)


def by_name(checks):
    return {c.name: c for c in checks}


def test_missing_engine_is_an_error(cfg):
    def missing(_cfg):
        raise EnvironmentProblem("Stockfish non trovato")

    checks, code = run_doctor(cfg, env={}, stockfish_factory=missing, maia_factory=fake_maia, benchmark=False)
    c = by_name(checks)
    assert c["Stockfish"].status == ERR and "setup_engines" in c["Stockfish"].fix
    assert code == 4


def test_version_pin_mismatch_api_key_device_and_elo_table(cfg, fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 3), [("cp 30", "c1e3")]), id_name="Stockfish 15")
    checks, _ = run_doctor(cfg, env={}, stockfish_factory=lambda _c: StockfishEngine(cmd, 16, 0.01, threads=1),
                           maia_factory=fake_maia, benchmark=False)
    c = by_name(checks)
    assert c["Stockfish"].status == OK and "Stockfish 15" in c["Stockfish"].detail
    assert c["Versione Stockfish"].status == WARN and "Stockfish 16" in c["Versione Stockfish"].detail
    assert c["OPENROUTER_API_KEY"].status == WARN
    assert "dispositivo" in c["PyTorch"].detail
    assert c["Maia-2"].status == OK
    table = c["Elo Maia-2"].detail
    assert "1500 FIDE → 1700 → fascia 7" in table
    assert "1900 FIDE → 2025 → fascia 10 (satura)" in table
    assert "2400 FIDE → 2400 → fascia 10 (satura)" in table


def test_api_key_present_is_never_printed(cfg, fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 3), [("cp 30", "c1e3")]))
    checks, _ = run_doctor(cfg, env={"OPENROUTER_API_KEY": "sk-secret-123"},
                           stockfish_factory=lambda _c: StockfishEngine(cmd, 16, 0.01, threads=1),
                           maia_factory=fake_maia, benchmark=False)
    c = by_name(checks)
    assert c["OPENROUTER_API_KEY"].status == OK
    assert c["Versione Stockfish"].status == OK
    assert all("sk-secret" not in x.detail for x in checks)


def test_maia_failure_is_an_error(cfg, fake_uci):
    cmd = fake_uci(uci_iterations(range(1, 3), [("cp 30", "c1e3")]))

    def no_weights(_cfg):
        raise EnvironmentProblem("Pesi di Maia-2 assenti")

    checks, code = run_doctor(cfg, env={}, stockfish_factory=lambda _c: StockfishEngine(cmd, 16, 0.01, threads=1),
                              maia_factory=no_weights, benchmark=False)
    assert by_name(checks)["Maia-2"].status == ERR
    assert code == 4
