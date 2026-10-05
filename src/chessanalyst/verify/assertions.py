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
    if kind == "category_advice":          # M3: the band of the user's T (§5-bis.2)
        c = next((c for c in pack.get("categories", []) if c["id"] == a["id"]), None)
        if c is None:
            return f"categoria inesistente: {a['id']}"
        return None if c["advice"] == a["advice"] else f"{a['id']}: T {c['T'][pack['user']['color']]} è «{c['advice']}»"
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


def band_table(pack: dict, wording: dict) -> dict[str, dict[str, str]]:
    """D-70: the band of every value an assertion can cite, computed as V06 computes it, so that the model copies
    the band instead of deriving it (sign, side and thresholds were its most frequent V06 errors)."""
    r = Resolver(pack, wording)
    eng = pack["engine"]
    ev_refs = ([n["id"] for n in pack["nodes"] if n["citable"]] + [c["id"] for c in eng["candidates"]]
               + [x["id"] for x in eng["replies"]] + [u["id"] for x in eng["replies"] for u in x["user_best"]]
               + [p["id"] for p in eng["pvs"]] + [ln["id"] for ln in pack.get("filtered_lines", [])])
    pct_refs = [f"{c['id']}.p_user" for c in eng["candidates"]] + [f"{x['id']}.p_opp" for x in eng["replies"]]
    out: dict[str, dict[str, str]] = {"eval_band": {}, "maia_band": {}}
    for ref in ev_refs:
        try:
            v = r.resolve("{{ev:" + ref + "}}").value
            out["eval_band"][ref] = eval_band_of(v[0], v[1], wording["eval_bands"])
        except (ResolveError, ValueError, TypeError):
            continue
    for ref in pct_refs:
        try:
            v = r.resolve("{{pct:" + ref + "}}").value
            if v is not None:
                out["maia_band"][ref] = maia_band_of(v, wording["maia_bands"])
        except (ResolveError, ValueError, TypeError):
            continue
    return out
