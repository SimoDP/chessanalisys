"""Utility bench on the book cards marked ``verifica``.

    python scripts/books_bench.py /mnt/project-files/libri --freeze   # engines: frozen packs (once)
    python scripts/books_bench.py /mnt/project-files/libri            # model: one analysis per position

Specs and packs go to ``<dir>/banco/``; the report to ``<dir>/banco/rapporto_<date>.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from chessanalyst import bench, books, books_bench  # noqa: E402
from chessanalyst.config import load_config  # noqa: E402
from chessanalyst.errors import ModelError  # noqa: E402


def freeze(cfg, cards, s, out_dir: Path) -> None:
    from chessanalyst.engines.cache import Cache
    from chessanalyst.inputs.fen import parse_fen
    from chessanalyst.inputs.position import Position
    from chessanalyst.pipeline import analyse_position, resolve_settings
    from chessanalyst.run import load_openings, open_engines

    fz = s["bench"]["freeze"]
    engines = open_engines(cfg, Cache(":memory:"))
    openings = load_openings(cfg)
    try:
        for i, card in enumerate(cards, 1):
            spec = books_bench.make_spec(card, s)
            (out_dir / f"{card['id']}.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False),
                                                       encoding="utf-8")
            pack_f = out_dir / f"{card['id']}.pack.json"
            if pack_f.is_file():
                continue
            print(f"{i}/{len(cards)} {card['id']}", flush=True)
            u = spec["user"]
            us = resolve_settings(cfg, u["color"], u["elo"], u["elo_scale"], None, fz["profile"], fz["detail"])
            pos = Position(board=parse_fen(spec["fen"], cfg.wording["errors"]), source="fen")
            pack = analyse_position(cfg, pos, us, engines.analyzer, engines.maia, openings,
                                    tablebase=engines.tablebase)
            pack_f.write_text(pack.model_dump_json() + "\n", encoding="utf-8")
    finally:
        engines.close()


def run(cfg, out_dir: Path) -> None:
    from chessanalyst.llm.client import make_client
    from chessanalyst.llm.cycle import run_model

    client = make_client(cfg)
    results = []
    for spec_f in sorted(out_dir.glob("*.yaml")):
        spec = yaml.safe_load(spec_f.read_text(encoding="utf-8"))
        pack_f = out_dir / f"{spec['id']}.pack.json"
        if not pack_f.is_file():
            continue
        pack = json.loads(pack_f.read_text(encoding="utf-8"))
        t0 = time.monotonic()
        try:
            res = run_model(cfg, pack, client)
            r = bench.score_run(cfg, spec, pack, res.verification, res.output, time.monotonic() - t0)
        except ModelError as e:
            r = bench.score_run(cfg, spec, pack, None, None, time.monotonic() - t0, str(e))
        results.append(bench.aggregate(spec["id"], spec, [r]))
        print(f"{len(results)} {spec['id']} verdetto={r.get('verdict')} {r.get('cost_usd')}", flush=True)
    summary = books_bench.summarize(results)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    (out_dir / f"rapporto_{stamp}.json").write_text(json.dumps({"summary": summary, "positions": results},
                                                             ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / f"rapporto_{stamp}.md").write_text(books_bench.report(summary, results), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Banco di utilità sulle schede dei libri")
    ap.add_argument("books_dir", type=Path)
    ap.add_argument("--freeze", action="store_true", help="congela i pacchetti con i motori")
    args = ap.parse_args(argv)
    cfg = load_config(ROOT)
    s = books.load_settings(ROOT)
    out_dir = args.books_dir / "banco"
    out_dir.mkdir(exist_ok=True)
    if args.freeze:
        freeze(cfg, books_bench.verification_cards(args.books_dir), s, out_dir)
    else:
        run(cfg, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
