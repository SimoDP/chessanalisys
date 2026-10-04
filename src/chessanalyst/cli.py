"""Command line interface (§2-bis.1, argparse, D-56).

M0 provides ``doctor`` and ``golden --data``. The other commands exist so
that they are refused explicitly (exit code 2) instead of failing obscurely.
"""

from __future__ import annotations

import argparse
import logging
import sys

from chessanalyst import exit_codes
from chessanalyst.errors import AnalystError

NOT_YET = {
    "interactive": "M1a",
    "analyze": "M1a",
    "rerun": "M1c",
    "golden --packs": "M1b",
    "golden --render": "M1b",
}


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
    sub.add_parser("analyze", help="analisi non interattiva (da M1a)")
    sub.add_parser("rerun", help="rifà LLM, verifica e render (da M1c)")
    return p


def _not_yet(what: str) -> int:
    sys.stderr.write(f"Funzione «{what}» disponibile da {NOT_YET[what]}.\n")
    return exit_codes.USAGE


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
    if out["maia_error"]:
        console.print(f"AVVISO Maia-2: {out['maia_error']}", markup=False)
        return exit_codes.ENVIRONMENT
    return exit_codes.OK


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("analyze", "rerun"):
        return _not_yet(argv[0])  # options of later milestones are not parsed yet
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        if args.command is None:
            return _not_yet("interactive")
        if args.command == "doctor":
            return _cmd_doctor(args)
        if args.command == "golden":
            if args.packs:
                return _not_yet("golden --packs")
            if args.render:
                return _not_yet("golden --render")
            return _cmd_golden_data(args)
    except AnalystError as e:
        sys.stderr.write(f"Errore: {e}\n")
        return e.exit_code
    return exit_codes.USAGE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
