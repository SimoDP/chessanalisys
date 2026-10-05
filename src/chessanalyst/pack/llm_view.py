"""Reduced view of the pack sent to the model (§6.1, AC-35).

Excluded: ``tables``, nodes with ``citable: false``, ``omitted_nodes``,
``config_hash``. In the nodes only the first lines of ``multipv`` (PV
truncated) and the first moves of the Maia-2 policy are sent. The pack
contains no PGN, player names, tags or paths (§11.5).

D-70: ``bands``, the band of every evaluation and Maia-2 probability an assertion can cite, already computed.
D-71: ``facts``, the pieces square by square and what each move and line does (features/motifs.py); the node
of the null move carries ``hypothetical``.

M3: of each category only the user's T (the opponent's T is for detail 5, O-5), R, balance, advice and
confidence; of each filtered line the data the text can cite (PV truncated as in the nodes).
"""

from __future__ import annotations

import copy
import json

from chessanalyst.config import LlmViewCfg

EXCLUDED = ("tables", "omitted_nodes", "config_hash")
LINE_FIELDS = ("id", "kind", "start_node", "entry", "against_user", "plies", "eval_end_user_cp", "mate_user",
               "impact_cp", "p_att", "risk", "tags", "primary", "visible_at_level")


def llm_view(pack: dict, view: LlmViewCfg, wording: dict | None = None) -> dict:
    """``view`` = ``config/default.yaml: llm.view`` (§6.1, D-65); with ``wording`` the view carries ``bands``
    (D-70)."""
    out = {k: copy.deepcopy(v) for k, v in pack.items() if k not in EXCLUDED}
    nodes = []
    for n in out["nodes"]:
        if not n["citable"]:
            continue
        n["multipv"] = [dict(ln, pv=ln["pv"][:view.pv_plies]) for ln in n["multipv"][:view.multipv_lines]]
        if n["maia"] is not None:
            n["maia"]["policy"] = n["maia"]["policy"][:view.policy_moves]
        nodes.append(n)
    null = (pack["engine"].get("null_move") or {}).get("node")
    for n in nodes:
        if n["id"] == null:                       # D-71: the side to move passes, the position is not real
            n["hypothetical"] = "mossa nulla: chi deve muovere passa il turno; non è la valutazione della posizione"
    out["nodes"] = nodes
    me = pack["user"]["color"]
    opp = "b" if me == "w" else "w"
    five = pack["user"]["detail_level"] == 5            # the opponent's T only at detail 5 (§5-bis.2, O-5)
    out["categories"] = [{"id": c["id"], "T": c["T"][me], "R": c["R"], "balance": c["balance"],
                          "advice": c["advice"], "confidence": c["confidence"],
                          **({"T_opp": c["T"][opp]} if five else {})} for c in pack.get("categories", [])]
    out["filtered_lines"] = [{k: (v[:view.pv_plies] if k == "plies" else v) for k, v in ln.items()
                              if k in LINE_FIELDS} for ln in pack.get("filtered_lines", [])]
    if wording is not None:
        from chessanalyst.verify.assertions import band_table

        from chessanalyst.features.motifs import pack_facts

        out["bands"] = band_table(pack, wording)
        out["facts"] = pack_facts(pack, wording["pieces"], view.pv_plies)
    return out


def llm_view_json(pack: dict, view: LlmViewCfg, wording: dict | None = None) -> str:
    """Compact JSON (E.2)."""
    return json.dumps(llm_view(pack, view, wording), ensure_ascii=False, separators=(",", ":"))
