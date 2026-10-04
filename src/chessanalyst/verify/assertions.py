"""Typed assertions (§9-bis.5, V06)."""

from __future__ import annotations

from chessanalyst.verify.resolve import ResolveError, Resolver


def eval_band_of(cp: int, mate: int | None, bands: dict) -> str:
    """Band ID of an evaluation (§6.4): modulus in centipawns, lower bound included."""
    if mate is not None:
        return "mate_plus" if mate > 0 else "mate_minus"
    a = abs(cp)
    for key, b in bands.items():
        if key == "mate":
            continue
        lo = round(b["abs_lo"] * 100)
        hi = None if b["abs_hi"] is None else round(b["abs_hi"] * 100)
        if a >= lo and (hi is None or a < hi):
            return key if key == "equal" else f"{key}_{'plus' if cp > 0 else 'minus'}"
    raise ValueError(cp)


def maia_band_of(p: float, bands: dict) -> str:
    for key, b in bands.items():
        if p >= b["lo"] and (b["hi"] is None or p < b["hi"]):
            return key
    raise ValueError(p)


def check_assertion(a: dict, pack: dict, resolver: Resolver, wording: dict) -> str | None:
    """None if consistent with the pack, else the reason."""
    kind = a["kind"]
    if kind == "feature":
        want = set(a.get("squares") or [])
        for f in pack["features"]:
            if f["key"] == a["key"] and f["side"] == a["side"] and want <= set(f["squares"]):
                return None
        return f"feature {a['key']} {a['side']} {sorted(want)} assente nel pacchetto"
    if kind == "classification":
        c = next((c for c in pack["engine"]["candidates"] if c["id"] == a["ref"]), None)
        if c is None:
            return f"candidata inesistente: {a['ref']}"
        return None if c["category"] == a["category"] else f"{a['ref']} ha categoria {c['category']}"
    try:
        if kind == "eval_band":
            r = resolver.resolve("{{ev:" + a["ref"] + "}}")
            actual = eval_band_of(r.value[0], r.value[1], wording["eval_bands"])
        else:
            if a["ref"].startswith("root."):
                return "maia_band non ammette root.*"
            r = resolver.resolve("{{pct:" + a["ref"] + "}}")
            actual = maia_band_of(r.value, wording["maia_bands"])
    except ResolveError as e:
        return f"riferimento non valido: {e.message}"
    return None if actual == a["band"] else f"{a['ref']} è nella banda {actual}, non {a['band']}"
