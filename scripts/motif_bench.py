"""Bench of the tactical motif detectors on Lichess puzzles (data plan, phase 1).

    python scripts/motif_bench.py                     # runs on the recorded sample, writes the report
    python scripts/motif_bench.py --sample FILE.csv   # rebuilds the sample from the Lichess database (CSV)

The database is ``lichess_db_puzzle.csv.zst`` from database.lichess.org (CC0); decompress it first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chessanalyst import motif_bench as mb  # noqa: E402
from chessanalyst.config import load_config  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Banco dei motivi tattici sui problemi di Lichess")
    ap.add_argument("--sample", type=Path, help="CSV dei problemi di Lichess da cui ricavare il campione")
    args = ap.parse_args(argv)
    settings = mb.load_settings(ROOT)
    sample = ROOT / settings["sample_file"]
    if args.sample:
        with args.sample.open(encoding="utf-8") as f:
            chosen = mb.select(mb.read_puzzles(f), settings["themes"], settings["per_theme"], settings["control"])
        mb.write_sample(chosen, sample)
        print(f"Campione: {len(chosen)} problemi in {sample}")
    with sample.open(encoding="utf-8") as f:
        puzzles = list(mb.read_puzzles(f))
    words = load_config(ROOT).wording["pieces"]
    result = mb.run(puzzles, settings, words)
    out = ROOT / settings["report_file"]
    out.write_text(mb.report(result, settings), encoding="utf-8")
    print(f"Rapporto: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
