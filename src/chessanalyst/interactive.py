"""Interactive flow ``chessanalyst`` (§2-bis.1). From M4: «entrambi» (Elo per color), detail 1–5, Elo from the
PGN tags proposed with confirmation (§2-bis.4 point 8)."""

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
from chessanalyst.settings import DETAILS, check_available, check_elo, effective, parse_color

BUDGETS = ("fast", "standard", "deep")
COLOR_LABEL = {"w": "bianco", "b": "nero", "both": "entrambi"}
BOTH_WORDS = ("entrambi", "e", "both")
SCALES = ("fide", "lichess")


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
    v["color"] = _retry(io, n, f"Colore [bianco/nero/entrambi, {COLOR_LABEL[v['color']]}]: ",
                        lambda s: v["color"] if not s.strip() else
                        ("both" if s.strip().lower() in BOTH_WORDS else parse_color(s)),
                        "Risposta non valida: bianco, nero o entrambi.")

    def parse_elo(default: int):
        def parse(s: str):
            if not s.strip():
                return default
            try:
                e = int(s.strip())
            except ValueError:
                return None
            return e if check_elo(cfg, e) else None
        return parse

    r = cfg.thresholds.elo_input
    bad = f"Elo non valido: un intero tra {r.min} e {r.max}."
    if v["color"] == "both":          # D-16: one Elo per color, the same by default
        v["elo_white"] = _retry(io, n, f"Elo del Bianco [{v.get('elo_white') or v['elo']}] (scala: {v['elo_scale']}): ",
                                parse_elo(v.get("elo_white") or v["elo"]), bad)
        v["elo_black"] = _retry(io, n, f"Elo del Nero [{v.get('elo_black') or v['elo_white']}] (scala: {v['elo_scale']}): ",
                                parse_elo(v.get("elo_black") or v["elo_white"]), bad)
        v["elo"] = v["elo_white"]
    else:
        v["elo"] = _retry(io, n, f"Elo [{v['elo']}] (scala: {v['elo_scale']}): ", parse_elo(v["elo"]), bad)
    v["budget"] = _retry(io, n, f"Budget [fast/standard/deep, {v['budget']}]: ",
                         lambda s: v["budget"] if not s.strip() else (s.strip().lower() if s.strip().lower() in BUDGETS else None),
                         "Risposta non valida: fast, standard o deep.")
    v["detail"] = _retry(io, n, f"Dettaglio [1-5, {v['detail']}]: ",
                         lambda s: v["detail"] if not s.strip() else
                         (int(s.strip()) if s.strip().isdigit() and int(s.strip()) in DETAILS else None),
                         "Risposta non valida: un numero da 1 a 5.")
    return v


def tag_elos(pos: Position) -> dict[str, int] | None:
    """``WhiteElo`` and ``BlackElo`` of the PGN, when both are positive integers (§2-bis.4 point 8)."""
    if pos.game is None:
        return None
    out = {}
    for color, tag in (("w", "WhiteElo"), ("b", "BlackElo")):
        val = pos.game.headers.get(tag, "").strip()
        if not val.isdigit() or int(val) <= 0:
            return None
        out[color] = int(val)
    return out


def ask_tag_elos(cfg: Config, io: IO, pos: Position, v: dict[str, Any]) -> dict[str, Any]:
    """M4: the Elo of the PGN tags are proposed with confirmation, always asking their scale. In the
    answer the user's Elo is the tag of their color, the opponent's the other one (both with «entrambi»)."""
    elos = tag_elos(pos)
    if elos is None:
        return v
    n = cfg.default.input.max_attempts
    use = _retry(io, n, f"La partita indica Elo Bianco {elos['w']} e Nero {elos['b']}. Usarli? [s/n] ", _yes,
                 "Rispondi s o n.")
    if not use:
        return v
    scale = _retry(io, n, f"Scala di questi Elo [fide/lichess, {v['elo_scale']}]: ",
                   lambda s: v["elo_scale"] if not s.strip() else (s.strip().lower() if s.strip().lower() in SCALES else None),
                   "Risposta non valida: fide o lichess.")
    v = dict(v, elo_scale=scale)
    if not all(check_elo(cfg, e) for e in elos.values()):
        r = cfg.thresholds.elo_input
        io.say(f"Elo della partita fuori dall'intervallo ammesso ({r.min}–{r.max}): restano quelli indicati.")
        return v
    if v["color"] == "both":
        v.update(elo_white=elos["w"], elo_black=elos["b"], elo=elos["w"])
    else:
        other = "b" if v["color"] == "w" else "w"
        v.update(elo=elos[v["color"]], opp_elo=elos[other])
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
            run_settings = ask_tag_elos(cfg, io, pos, settings)
            entry = opening_entry(openings, pos.board)
            io.say(confirmation_text(pos, entry))
            ans = _retry(io, cfg.default.input.max_attempts, "Confermi? [s/n/correggi]: ",
                         lambda s: s.strip().lower() if s.strip().lower() in ("s", "n", "correggi") else None,
                         "Rispondi s, n oppure correggi.")
            if ans == "n":
                return exit_codes.OK
            if ans == "correggi":
                continue
            save_profile({"color": settings["color"], "elo": settings["elo"], "elo_scale": settings["elo_scale"],
                          "budget": settings["budget"], "detail": settings["detail"]})
            return run(pos, run_settings)
    except (TooManyAttempts, EOFError):
        io.say("Troppi tentativi non validi.")
        return exit_codes.INVALID_INPUT
