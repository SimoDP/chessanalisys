"""Command line interface (§2-bis.1, argparse, D-56).

M1c: interactive flow, ``analyze`` and ``rerun`` (pack, model, verification,
render), ``doctor``, ``golden --data/--packs/--render``. Options of later
milestones are refused explicitly with exit code 2 (D-30, ``settings.py``).
"""

from __future__ import annotations

import argparse
import logging
import sys

from chessanalyst import exit_codes
from chessanalyst.errors import AnalystError

class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # usage errors → exit code 2
        self.print_usage(sys.stderr)
        sys.stderr.write(f"Errore: {message}\n")
        raise SystemExit(exit_codes.USAGE)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="chessanalyst", description="Chess Position Analyst")
    p.add_argument("--verbose", action="store_true", help="log DEBUG anche su console")
    sub = p.add_subparsers(dest="command")
    d = sub.add_parser("doctor", help="controlla l'ambiente")
    d.add_argument("--no-benchmark", action="store_true", help="salta il benchmark di Stockfish")
    g = sub.add_parser("golden", help="dati e pacchetti degli esempi golden")
    mode = g.add_mutually_exclusive_group(required=True)
    mode.add_argument("--data", action="store_true", help="M0: rigenera i dati dei golden (§8-bis.4)")
    mode.add_argument("--packs", action="store_true", help="M1b: rigenera e congela i pacchetti golden")
    mode.add_argument("--render", action="store_true", help="M1b: verifica i fewshot e genera rendered")
    g.add_argument("--time-scale", type=float, default=1.0,
                   help="fattore sui tempi del profilo deep (1.0 = tempi normativi)")
    g.add_argument("--reuse-nodes", action="store_true",
                   help="riusa fixtures/golden_nodes.json e ripete solo Maia-2 e il confronto")
    g.add_argument("--no-maia", action="store_true", help="salta Maia-2")
    g.add_argument("--force", action="store_true", help="--packs: sovrascrive i pacchetti congelati")
    g.add_argument("--recorded", action="store_true",
                   help="--packs: usa le registrazioni di fixtures/recorded invece dei motori")
    a = sub.add_parser("analyze", help="analisi non interattiva")
    a.add_argument("--input", choices=["example", "fen", "pgn"], default=None)
    src = a.add_mutually_exclusive_group()
    src.add_argument("--text")
    src.add_argument("--file")
    src.add_argument("--stdin", action="store_true")
    a.add_argument("--game", type=int)
    at = a.add_mutually_exclusive_group()
    at.add_argument("--at")
    at.add_argument("--ply", type=int)
    a.add_argument("--color", choices=["white", "black", "both"])
    a.add_argument("--elo", type=int)
    a.add_argument("--opp-elo", type=int)
    a.add_argument("--elo-white", type=int)
    a.add_argument("--elo-black", type=int)
    a.add_argument("--elo-scale", choices=["fide", "lichess", "chesscom"])
    a.add_argument("--budget", choices=["fast", "standard", "deep"])
    a.add_argument("--detail", type=int)
    a.add_argument("--out")
    a.add_argument("--yes", action="store_true")
    a.add_argument("--verbose", action="store_true", dest="verbose_a")
    r = sub.add_parser("rerun", help="rifà modello, verifica e render da pack.json")
    r.add_argument("folder", help="cartella di output con pack.json")
    r.add_argument("--verbose", action="store_true", dest="verbose_a")
    return p


def _cmd_doctor(args: argparse.Namespace) -> int:
    from chessanalyst.config import load_config
    from chessanalyst.doctor import print_checks, run_doctor

    cfg = load_config()
    checks, code = run_doctor(cfg, benchmark=not args.no_benchmark)
    print_checks(checks)
    return code


def _cmd_golden_data(args: argparse.Namespace) -> int:
    from rich.console import Console

    from chessanalyst.config import load_config
    from chessanalyst.engines.cache import Cache, CachedAnalyzer
    from chessanalyst.engines.factory import make_maia
    from chessanalyst.golden.data import golden_data, open_analyzer

    console = Console()
    cfg = load_config()
    if args.reuse_nodes:
        sf, analyzer = None, CachedAnalyzer(None, Cache())
    else:
        sf, analyzer = open_analyzer(cfg)
    try:
        maia_factory = None if args.no_maia else (lambda: make_maia(cfg, Cache()))
        out = golden_data(cfg, analyzer, maia_factory, time_scale=args.time_scale,
                          progress=lambda s: console.print(s, highlight=False, markup=False),
                          reuse_nodes=args.reuse_nodes)
    finally:
        if sf is not None:
            sf.close()
    a = out["ac09"]
    console.print(f"AC-09: {'superato' if a['passed'] else 'NON superato'} · vedi docs/golden_diff.md", markup=False)
    if out["maia_error"] and not args.no_maia:
        console.print(f"AVVISO Maia-2: {out['maia_error']}", markup=False)
        return exit_codes.ENVIRONMENT
    return exit_codes.OK


def _cmd_golden_packs(args: argparse.Namespace) -> int:
    from rich.console import Console

    from chessanalyst.config import load_config
    from chessanalyst.engines.cache import Cache, CachedAnalyzer
    from chessanalyst.golden.packs import check_overwrite, golden_packs
    from chessanalyst.run import load_openings, open_engines

    console = Console()
    cfg = load_config()
    check_overwrite(cfg, args.force)   # before starting the engines
    if args.recorded:
        from chessanalyst.engines.fake import FakeEngine, FakeMaiaBackend
        from chessanalyst.engines.maia2 import MaiaEngine

        rec = cfg.project_root / "fixtures" / "recorded"
        cache = Cache(":memory:")
        analyzer = CachedAnalyzer(FakeEngine.from_dir(rec / "engine"), cache)
        maia = MaiaEngine(FakeMaiaBackend.from_dir(rec / "maia"), cfg.maia2_limits, cache)
        close = lambda: None  # noqa: E731
    else:
        engines = open_engines(cfg, Cache(":memory:"))   # fresh cache: the packs come from this run only
        analyzer, maia, close = engines.analyzer, engines.maia, engines.close
    try:
        written = golden_packs(cfg, analyzer, maia, load_openings(cfg), force=args.force,
                               time_scale=args.time_scale,
                               progress=lambda s: console.print(s, highlight=False, markup=False))
    finally:
        close()
    for w in written:
        console.print(f"Scritto {w.relative_to(cfg.project_root)}", markup=False)
    return exit_codes.OK


def _cmd_golden_render(args: argparse.Namespace) -> int:
    from chessanalyst.config import load_config
    from chessanalyst.golden.render import golden_render

    cfg = load_config()
    outcomes = golden_render(cfg)
    failed = False
    for o in outcomes:
        for line in o.errors:
            print(f"  {o.name} · {line}")
        if o.rendered is not None:
            print(f"Scritto {o.rendered.relative_to(cfg.project_root)}")
        failed = failed or bool(o.errors)
    return exit_codes.INVALID_INPUT if failed else exit_codes.OK


def _console():
    from rich.console import Console

    return Console(stderr=False, highlight=False)


def _finish(outdir) -> None:
    print(f"Analisi salvata in {outdir / 'analysis.md'}")


def _settings_from(cfg, values):
    from chessanalyst.pipeline import resolve_settings

    return resolve_settings(cfg, values["color"], values["elo"], values["elo_scale"], values.get("opp_elo"),
                            values["budget"], values.get("detail", 4))


def _progress(console):
    def show(s: str) -> None:
        if s.startswith("modello di linguaggio"):
            console.print("Modello di linguaggio in esecuzione ...", markup=False)
        else:
            console.print(f"Motori in esecuzione ...  ({s})", markup=False)
    return show


def _cmd_rerun(args: argparse.Namespace) -> int:
    from pathlib import Path

    from chessanalyst.config import load_config
    from chessanalyst.run import rerun

    cfg = load_config()
    path = rerun(cfg, Path(args.folder).expanduser(), verbose=args.verbose or args.verbose_a)
    print(f"Analisi salvata in {path}")
    return exit_codes.OK


def _cmd_analyze(args: argparse.Namespace) -> int:
    from pathlib import Path

    from chessanalyst.config import load_config
    from chessanalyst.errors import UsageError
    from chessanalyst.inputs.confirm import confirmation_text
    from chessanalyst.inputs.load import load_position
    from chessanalyst.inputs.read_source import read_source, read_stdin
    from chessanalyst.run import load_openings, run_analysis
    from chessanalyst.settings import check_available, check_elo, effective

    cfg = load_config()
    cli = {"color": args.color, "elo": args.elo, "opp_elo": args.opp_elo, "elo_white": args.elo_white,
           "elo_black": args.elo_black, "elo_scale": args.elo_scale, "budget": args.budget, "detail": args.detail}
    check_available(cfg, cli)
    values = effective(cfg, cli)
    check_available(cfg, values)
    for key in ("elo", "opp_elo"):
        if values.get(key) is not None and not check_elo(cfg, values[key]):
            r = cfg.thresholds.elo_input
            raise UsageError(f"Elo non valido: {values[key]} (ammesso tra {r.min} e {r.max})")
    method = args.input or cfg.default.input.method or "example"
    has_src = args.text is not None or args.file is not None or args.stdin
    if method == "example" and has_src:
        raise UsageError("--input example non accetta --text, --file o --stdin")
    if method != "example" and not has_src:
        raise UsageError(f"--input {method} richiede uno tra --text, --file e --stdin")
    if method != "pgn" and (args.game is not None or args.at is not None or args.ply is not None):
        raise UsageError("--game, --at e --ply valgono solo con --input pgn")
    text = None
    if args.stdin:
        text = read_stdin()
    elif args.file is not None:
        p = Path(args.file).expanduser()
        if not p.is_file():
            from chessanalyst.errors import InputError

            raise InputError(cfg.wording["errors"]["file_not_found"].format(detail=args.file))
        text = p.read_text(encoding="utf-8-sig")
    elif args.text is not None:
        text = read_source(args.text)
    pos = load_position(cfg, method, text, game_no=args.game, at=args.at, ply=args.ply)
    us = _settings_from(cfg, values)
    console = _console()
    if not args.yes:
        openings = load_openings(cfg)
        console.print(confirmation_text(pos, openings.lookup_epd(pos.board) if openings else None), markup=False)
        if input("Confermi? [s/n]: ").strip().lower() not in ("s", "si", "sì"):
            return exit_codes.OK
    out_base = Path(args.out) if args.out else cfg.resolve_path(cfg.default.output.dir)
    outdir = run_analysis(cfg, pos, us, out_base, verbose=args.verbose or args.verbose_a,
                          progress=_progress(console))
    _finish(outdir)
    return exit_codes.OK


def _cmd_interactive(args: argparse.Namespace) -> int:
    from chessanalyst.config import load_config
    from chessanalyst.interactive import IO, interactive
    from chessanalyst.run import run_analysis

    cfg = load_config()
    console = _console()

    def run(pos, values) -> int:
        us = _settings_from(cfg, values)
        outdir = run_analysis(cfg, pos, us, cfg.resolve_path(cfg.default.output.dir), verbose=args.verbose,
                              progress=_progress(console))
        _finish(outdir)
        return exit_codes.OK

    return interactive(cfg, IO(ask=input, say=lambda s: console.print(s, markup=False)), run)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)
    verbose = args.verbose or getattr(args, "verbose_a", False)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)  # run.log gets DEBUG
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.handlers = [h for h in root_logger.handlers if not getattr(h, "_chessanalyst_console", False)]
    console_handler._chessanalyst_console = True
    root_logger.addHandler(console_handler)
    try:
        if args.command is None:
            return _cmd_interactive(args)
        if args.command == "analyze":
            return _cmd_analyze(args)
        if args.command == "rerun":
            return _cmd_rerun(args)
        if args.command == "doctor":
            return _cmd_doctor(args)
        if args.command == "golden":
            if args.packs:
                return _cmd_golden_packs(args)
            if args.render:
                return _cmd_golden_render(args)
            return _cmd_golden_data(args)
    except AnalystError as e:
        sys.stderr.write(f"Errore: {e}\n")
        return e.exit_code
    except Exception:  # noqa: BLE001 - unexpected bug: exit code 1 with the trace in run.log
        logging.getLogger(__name__).exception("Errore inatteso")
        sys.stderr.write("Errore inatteso: vedi run.log\n")
        return exit_codes.BUG
    return exit_codes.USAGE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
