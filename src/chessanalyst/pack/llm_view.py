"""Reduced view of the pack sent to the model (§6.1, AC-35).

Excluded: ``tables``, nodes with ``citable: false``, ``omitted_nodes``,
``config_hash``. In the nodes only the first lines of ``multipv`` (PV
truncated) and the first moves of the Maia-2 policy are sent. The pack
contains no PGN, player names, tags or paths (§11.5).
"""

from __future__ import annotations

import copy
import json

from chessanalyst.config import LlmViewCfg

EXCLUDED = ("tables", "omitted_nodes", "config_hash")


def llm_view(pack: dict, view: LlmViewCfg) -> dict:
    """``view`` = ``config/default.yaml: llm.view`` (§6.1, D-65)."""
    out = {k: copy.deepcopy(v) for k, v in pack.items() if k not in EXCLUDED}
    nodes = []
    for n in out["nodes"]:
        if not n["citable"]:
            continue
        n["multipv"] = [dict(ln, pv=ln["pv"][:view.pv_plies]) for ln in n["multipv"][:view.multipv_lines]]
        if n["maia"] is not None:
            n["maia"]["policy"] = n["maia"]["policy"][:view.policy_moves]
        nodes.append(n)
    out["nodes"] = nodes
    return out


def llm_view_json(pack: dict, view: LlmViewCfg) -> str:
    """Compact JSON (E.2)."""
    return json.dumps(llm_view(pack, view), ensure_ascii=False, separators=(",", ":"))
