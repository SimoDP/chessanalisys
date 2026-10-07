"""D-72: the document made of the key points (plan/keypoints.py), one section per point, in the code's order.

``outline_pack`` returns the pack with a new ``section_plan`` (only the sections of the key points, in their
order, with budgets proportional to what each point holds), the key points (``key_points``, each with its
section) and ``document: keypoints``. Verification and render read the plan as before; two keys are new in each
section of the plan:

- ``cites_allowed``: the IDs a token of the section may cite (V13): each fact is told in one section only;
- ``auto_tables``: the tables the render puts in the section (the model writes no table block);
- ``lead_text``: a sentence the render writes before the model's text (the material, in the verdict).

The pack itself (engines, nodes, tables) does not change: the outline can be rebuilt from it at any time.
"""

from __future__ import annotations

import copy

from chessanalyst.config import Config
from chessanalyst.pack.section_plan import fill_opp
from chessanalyst.plan.keypoints import key_points
from chessanalyst.verify.tokens import clean_san

DOCUMENT = "keypoints"
SECTION_IDS = [f"S{k:02d}" for k in range(1, 14)]
THEORY_TYPES = ("plan", "reasoning")
MAIA_TYPES = ("main_danger", "likely_reply", "opportunity")


def _norm(ref: str) -> str:
    if "@" in ref:
        san, node = ref.split("@", 1)
        return f"{clean_san(san)}@{node}"
    return ref


def _items(kp: dict) -> int:
    f = kp["facts"]
    for key in ("replies", "moves", "items"):
        if isinstance(f.get(key), list):
            return len(f[key])
    return f["items"] if isinstance(f.get("items"), int) else 1          # reasoning: points of the list


def _must_cover(kp: dict) -> list[str]:
    f, t = kp["facts"], kp["type"]
    if t == "verdict":
        return ["N1"]
    if t == "recommendation":
        return [f["ref"]]
    if t == "systems":
        return list(kp["ids"])
    if t == "main_danger":
        return [f.get("ref") or f["line"]]
    if t in ("likely_reply", "opportunity"):
        out = []
        for r in f["replies"]:
            out += [r["ref"]] + [r[k]["ref"] for k in ("answer", "trap") if k in r]
        return [_norm(x) for x in out]
    return []


def _allowed(kp: dict, pack: dict) -> list[str]:
    eng = pack["engine"]
    pvs = {p["id"] for p in eng["pvs"]}
    cand_pv = {c["id"]: c.get("pv") for c in eng["candidates"]}
    out = [_norm(i) for i in kp["ids"]]
    for i in kp["ids"]:
        if cand_pv.get(i):
            out.append(cand_pv[i])
        if i.startswith("R") and "." not in i and f"PV{i[1:]}" in pvs:
            out.append(f"PV{i[1:]}")
    if kp["type"] == "verdict":
        out.append("N1")
    if kp["type"] == "plan":
        nodes = list((eng.get("context_move") or {}).get("san_by_node", {}))[:1]      # where it is first played
        out += [_norm(f"{i['san']}@{n}") for i in kp["facts"]["items"] if i["key"] == "context_move" for n in nodes]
    return list(dict.fromkeys(out))


def material_lead(cfg: Config, kp: dict) -> str | None:
    """The sentence on the material that opens the verdict, written by the code (usefulness test, phase 2: the
    model turned «a pawn up» against the user)."""
    if kp["type"] != "verdict" or "material_balance_user" not in kp["facts"]:
        return None
    from chessanalyst.llm.prompt import number_words

    bal = kp["facts"]["material_balance_user"]
    lead, w = cfg.wording["material_lead"], cfg.wording["material_words"]
    if bal == 0:
        return lead["even"]
    n = abs(bal)
    count = f"{w['one'] if n == 1 else number_words(n)} {w['pawn'] if n == 1 else w['pawns']}"
    return lead["up" if bal > 0 else "down"].format(n=count)


def outline_pack(cfg: Config, pack: dict) -> dict:
    if pack.get("document") == DOCUMENT:
        return pack
    kpc = cfg.thresholds.keypoints
    points = key_points(cfg, pack)
    opp = cfg.wording["colors"]["b" if pack["user"]["color"] == "w" else "w"]
    base = next((s for s in pack["section_plan"]), None)
    plies = min(base["max_pv_plies"] if base else cfg.thresholds.plies_bounds[1], kpc.pv_plies)
    saturated = bool(pack["maia"]["saturated"])
    user_to_move = pack["position"]["user_to_move"]
    plan, used = [], set()
    for kp in points:
        sid = kpc.sections[kp["type"]]
        kp["section"] = sid
        used.add(sid)
        w = kpc.words[kp["type"]]
        budget = w["base"] + w["per_item"] * _items(kp) + w.get("per_move", 0) * len(kp["ids"])
        budget = max(kpc.words_min, min(kpc.words_max, budget))
        auto = ["T1"] if "T1" in pack["tables"] and kp["type"] == (
            "recommendation" if user_to_move else "likely_reply") else []
        plan.append({
            "id": sid, "title": fill_opp(cfg.wording["keypoint_titles"][kp["type"]], opp), "required": True,
            "absorbed_into": None, "omitted": None, "word_budget": budget, "max_pv_plies": plies,
            "theory_allowed": kp["type"] in THEORY_TYPES, "tables": [], "must_cover": _must_cover(kp),
            "focus_squares": [], "maia_low_confidence": saturated and kp["type"] in MAIA_TYPES,
            "cites_allowed": _allowed(kp, pack), "auto_tables": auto, "key_point": kp["id"],
            "lead_text": material_lead(cfg, kp),
        })
    for sid in SECTION_IDS:
        if sid not in used:
            plan.append({"id": sid, "title": None, "required": False, "absorbed_into": None, "omitted": DOCUMENT,
                         "word_budget": None, "max_pv_plies": plies, "theory_allowed": False, "tables": [],
                         "must_cover": [], "focus_squares": [], "maia_low_confidence": False})
    out = copy.copy(pack)
    out["section_plan"], out["key_points"], out["document"] = plan, points, DOCUMENT
    out["omitted_sections"] = []                     # the old sections are not «omitted»: there are none
    return out


def document_pack(cfg: Config, pack: dict, document: str | None = None) -> dict:
    """The pack as the document of ``document`` (default ``llm.document``) needs it."""
    return outline_pack(cfg, pack) if (document or cfg.default.llm.document) == DOCUMENT else pack
