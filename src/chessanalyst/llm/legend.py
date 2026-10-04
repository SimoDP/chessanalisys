"""Legend of the example's tokens (§9.2): ``{{ev:C1}} → +0,37``, in order of first appearance,
resolved against the example's frozen pack (the model does not receive that pack)."""

from __future__ import annotations

from chessanalyst.verify.checker import iter_units
from chessanalyst.verify.resolve import Resolver
from chessanalyst.verify.tokens import find_tokens


def legend_lines(output: dict, pack: dict, wording: dict, seen: set[str] | None = None) -> list[str]:
    resolver = Resolver(pack, wording)
    seen = set() if seen is None else seen
    lines = []
    for unit in iter_units(output):
        for tok in find_tokens(unit.text):
            if tok not in seen:
                seen.add(tok)
                lines.append(f"{tok} → {resolver.resolve(tok).text}")
    for sec in output["sections"]:                       # line blocks render a PV as well
        for blk in sec["blocks"]:
            if blk["type"] == "line":
                key = f"line {blk['pv']}:{blk['plies']}"
                if key not in seen:
                    seen.add(key)
                    lines.append(f'{{"type": "line", "pv": "{blk["pv"]}", "plies": {blk["plies"]}}} → '
                                 f"{resolver.pv_text(blk['pv'], blk['plies'])}")
    return lines
