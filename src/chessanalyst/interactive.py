"""Interactive flow ``chessanalyst`` (§2-bis.1). M1–M3: no «entrambi», no detail."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from chessanalyst import exit_codes
from chessanalyst.config import Config
from chessanalyst.errors import InputError
from chessanalyst.inputs.confirm import confirmation_text
from chessanalyst.inputs.example import example_position
from chessanalyst.inputs.fen import parse_fen
from chessanalyst.inputs.pgn import game_infos, position_from_game, read_games
from chessanalyst.inputs.position import Position
from chessanalyst.inputs.load import detect_or_assume
from chessanalyst.inputs.read_source import read_interactive, read_source
from chessanalyst.settings import check_available, check_elo, effective, parse_color

BUDGETS = ("fast", "standard", "deep")
COLOR_LABEL = {"w": "bianco", "b": "nero"}


class TooManyAttempts(Exception):
    pass


@dataclass
class IO:
    ask: Callable[[str], str]          # raises EOFError at end of input
    say: Callable[[str], None]


def _retry(io: IO, max_attempts: int, prompt: str, parse: Callable[[str], Any], error: str) -> Any:
    for _ in range(max_attempts):
        value = parse(io.ask(prompt))
        if value is not None:
            return value
        io.say(error)
    raise TooManyAttempts()


def ask_settings(cfg: Config, io: IO) -> dict[str, Any]:
    v = effective(cfg)
    check_available(cfg, v)   # values from config/profile of later milestones are refused, never ignored (D-30)
    n = cfg.default.input.max_attempts
    v["color"] = _retry(io, n, f"Colore [bianco/nero, {COLOR_LABEL[v['color']]}]: ",
                        lambda s: v["color"] if not s.strip() else parse_color(s),
                        "Risposta non valida: bianco o nero.")

    def parse_elo(s: str):
        if not s.strip():
            return v["elo"]
        try:
            e = int(s.strip())
        except ValueError:
            return None
        return e if check_elo(cfg, e) else None

    r = cfg.thresholds.elo_input
    v["elo"] = _retry(io, n, f"Elo [{v['elo']}] (scala: {v['elo_scale']}): ", parse_elo,
                      f"Elo non valido: un intero tra {r.min} e {r.max}.")
    v["budget"] = _retry(io, n, f"Budget [fast/standard/deep, {v['budget']}]: ",
                         lambda s: v["budget"] if not s.strip() else (s.strip().lower() if s.strip().lower() in BUDGETS else None),
                         "Risposta non valida: fast, standard o deep.")
    return v


def _yes(s: str) -> bool | None:
    s = s.strip().lower()
    return True if s in ("s", "si", "sì") else False if s == "n" else None


def ask_position(cfg: Config, io: IO) -> Position:
    msgs = cfg.wording["errors"]
    n = cfg.default.input.max_attempts
    method = _retry(io, n, "Posizione da [esempio/fen/pgn] (invio = esempio): ",
                    lambda s: "example" if s.strip().lower() in ("", "esempio") else
                    (s.strip().lower() if s.strip().lower() in ("fen", "pgn") else None),
                    "Risposta non valida: esempio, fen o pgn.")
    if method == "example":
        return example_position(cfg)
    for _ in range(n):
        try:
            if method == "fen":
                io.say("Incolla la FEN oppure scrivi il percorso di un file:")
            else:
                io.say("Incolla il PGN (termina con una riga che contiene solo un punto, oppure Ctrl-D / Ctrl-Z+Invio)\n"
                       "oppure scrivi il percorso di un file (.pgn / .txt):")
            first = io.ask("> ")
            text = read_source(first) if method == "fen" else read_interactive(first, lambda: io.ask(""))
            detected = detect_or_assume(text, method, msgs)
            if detected != method:
                names = {"fen": "FEN", "pgn": "PGN"}
                ans = _retry(io, n, f"Hai scelto {names[method]} ma il testo sembra un {names[detected]}. "
                                    f"Uso {names[detected]}? [s/n] ", _yes, "Rispondi s o n.")
                if not ans:
                    continue
                method = detected
            if method == "fen":
                return Position(board=parse_fen(text, msgs), source="fen")
            games = read_games(text)
            if not games:
                raise InputError(msgs["pgn_no_games"])
            infos = game_infos(games)
            if len(games) == 1:
                g = infos[0]
                io.say(f'  Trovata 1 partita: "{g.label()}", {g.plies} semimosse, risultato {g.result}')
                game = games[0]
            else:
                for g in infos:
                    io.say(f"  {g.index}. {g.white} - {g.black} · {g.event} {g.date} · {g.plies} semimosse · {g.result}")
                k = _retry(io, n, "Numero della partita: ",
                           lambda s: int(s) if s.strip().isdigit() and 1 <= int(s) <= len(games) else None,
                           f"Scegli un numero tra 1 e {len(games)}.")
                game = games[k - 1]
            at = io.ask("  Analizzare la posizione finale (invio) oppure indicare la mossa "
                        "(es. 17b = dopo la 17ª del Nero): ")
            return position_from_game(game, msgs, at=at or None)
        except InputError as e:
            io.say(f"Errore: {e}")
        except EOFError:
            break
    raise TooManyAttempts()


def interactive(cfg: Config, io: IO, run: Callable[[Position, dict[str, Any]], int]) -> int:
    """Return the exit code. ``run`` performs the analysis after confirmation.
    Options not yet available raise UsageError (exit code 2 in ``cli.main``)."""
    from chessanalyst.profile import save_profile
    from chessanalyst.engines.openings import opening_entry
    from chessanalyst.run import load_openings

    try:
        settings = ask_settings(cfg, io)
        openings = load_openings(cfg)
        while True:
            pos = ask_position(cfg, io)
            entry = opening_entry(openings, pos.board)
            io.say(confirmation_text(pos, entry))
            ans = _retry(io, cfg.default.input.max_attempts, "Confermi? [s/n/correggi]: ",
                         lambda s: s.strip().lower() if s.strip().lower() in ("s", "n", "correggi") else None,
                         "Rispondi s, n oppure correggi.")
            if ans == "n":
                return exit_codes.OK
            if ans == "correggi":
                continue
            save_profile({"color": settings["color"], "elo": settings["elo"],
                          "elo_scale": settings["elo_scale"], "budget": settings["budget"]})
            return run(pos, settings)
    except (TooManyAttempts, EOFError):
        io.say("Troppi tentativi non validi.")
        return exit_codes.INVALID_INPUT
