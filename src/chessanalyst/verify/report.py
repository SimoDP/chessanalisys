"""``verification.json`` (§10.3) and the per-check outcome shown in the report."""

from __future__ import annotations

from chessanalyst.verify.checker import CODES, Result
from chessanalyst.verify.degrade import Degraded


def check_outcomes(last: Result, degraded: Degraded | None) -> dict[str, str]:
    """``superato`` | ``avviso`` (only V07 c/d or the theory share) | ``non superato (…)``."""
    out = {c: "superato" for c in CODES}
    for e in last.errors:
        soft = (e.code == "V07" and e.sub in ("c", "d")) or (e.code == "V08" and e.section is None)
        if soft and out[e.code] == "superato":
            out[e.code] = "avviso"
        elif not soft:
            out[e.code] = "non superato (corretto in modalità degradata)" if degraded else "non superato"
    out["V11"] = "superato"
    return out


def verification_json(attempts: list[Result], degraded: Degraded | None, hints: dict) -> dict:
    last = attempts[-1]
    outcomes = check_outcomes(last, degraded)
    return {
        "attempts": [{"n": k, "errors": [e.to_dict(hints) for e in r.errors]} for k, r in enumerate(attempts, 1)],
        "final": {
            "passed": [c for c, v in outcomes.items() if v == "superato"],
            "warnings": degraded.warnings if degraded else [],
            "removed": degraded.removed if degraded else [],
            "marked": degraded.marked if degraded else [],
        },
        "theory_blocks": [{"section": t["section"], "text": t["text"], "words": t["words"]} for t in last.theory_blocks],
        "theory_share": last.theory_share,
        "words_by_section": last.words_by_section,
    }
