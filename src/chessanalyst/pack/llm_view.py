"""Reduced view of the pack sent to the model (§6.1, AC-35).

Excluded: ``tables``, nodes with ``citable: false``, ``omitted_nodes``,
``config_hash``. In the nodes only the first lines of ``multipv`` (PV
truncated) and the first moves of the Maia-2 policy are sent. The pack
contains no PGN, player names, tags or paths (§11.5).
"""

from __future__ import annotations

import copy
import json

# §6.1 fixes these sizes in the text; Appendix D has no key for them (OQ-M1a-13).
VIEW_MULTIPV_LINES = 5
VIEW_PV_PLIES = 6
VIEW_POLICY_MOVES = 5
EXCLUDED = ("tables", "omitted_nodes", "config_hash")


def llm_view(pack: dict) -> dict:
    view = {k: copy.deepcopy(v) for k, v in pack.items() if k not in EXCLUDED}
    nodes = []
    for n in view["nodes"]:
        if not n["citable"]:
            continue
        n["multipv"] = [dict(ln, pv=ln["pv"][:VIEW_PV_PLIES]) for ln in n["multipv"][:VIEW_MULTIPV_LINES]]
        if n["maia"] is not None:
            n["maia"]["policy"] = n["maia"]["policy"][:VIEW_POLICY_MOVES]
        nodes.append(n)
    view["nodes"] = nodes
    return view


def llm_view_json(pack: dict) -> str:
    """Compact JSON (E.2)."""
    return json.dumps(llm_view(pack), ensure_ascii=False, separators=(",", ":"))
