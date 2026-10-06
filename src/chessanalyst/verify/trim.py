"""D-74: the word budget is enforced by the code. A section over the budget loses its last sentences,
never one that cites an ID of must_cover; the caller re-checks the result and keeps it only if no new
error appears."""

from __future__ import annotations

import copy
import re

from chessanalyst.verify.tokens import TOKEN_RE
from chessanalyst.verify.wordcount import count_words

_SENTENCE = re.compile(r"(?<=[.!?;])\s+")


def _units(section: dict) -> list[tuple[dict, list | None, dict]]:
    """(block, list of items or None, paragraph) for every prose paragraph, in reading order."""
    out = []
    for blk in section.get("blocks") or []:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") == "p" and isinstance(blk.get("text"), str):
            out.append((blk, None, blk))
        elif blk.get("type") in ("ul", "ol") and isinstance(blk.get("items"), list):
            out += [(blk, blk["items"], it) for it in blk["items"]
                    if isinstance(it, dict) and isinstance(it.get("text"), str)]
    return out


def _refs(text: str) -> set[str]:
    """IDs cited by the tokens of ``text``, with their roots (R1.u1 → R1.u1, R1)."""
    refs: set[str] = set()
    for tok in TOKEN_RE.findall(text):
        parts = tok.strip("{}").split(":")
        if len(parts) > 1:
            ref = parts[1]
            while ref:
                refs.add(ref)
                ref = ref.rpartition(".")[0]
    return refs


def _section_words(section: dict, word_re: str) -> int:
    return sum(count_words(p["text"], word_re) for _, _, p in _units(section))


def _drop_last_sentence(section: dict, keep: set[str]) -> bool:
    """Removes the last sentence that cites nothing of ``keep``; an emptied paragraph goes with its
    assertions, an emptied list with it. False when no sentence can go."""
    for blk, items, para in reversed(_units(section)):
        sentences = _SENTENCE.split(para["text"].strip())
        for i in range(len(sentences) - 1, -1, -1):
            if _refs(sentences[i]) & keep:
                continue
            rest = sentences[:i] + sentences[i + 1:]
            if rest:
                para["text"] = " ".join(rest)
                left = _refs(para["text"])
                para["assertions"] = [a for a in para.get("assertions") or []
                                      if not isinstance(a, dict) or "ref" not in a or a["ref"] in left]
            elif items is not None:
                items.remove(para)
                if not items:
                    section["blocks"].remove(blk)
            else:
                section["blocks"].remove(blk)
            return True
    return False


def trim_response(response: dict, plan: dict[str, dict], over: set[str], word_re: str,
                  tolerance) -> dict | None:
    """A copy of ``response`` with every section of ``over`` cut to budget + tolerance, or None when a
    section cannot get there without losing an ID of must_cover."""
    new = copy.deepcopy(response)
    out = new if "schema_version" in new else next(       # a bare output, as the checker accepts it
        (b["input"] for b in new.get("content", []) if b.get("type") == "tool_use"
         and isinstance(b.get("input"), dict)), None)
    if out is None:
        return None
    sections = {s.get("id"): s for s in out.get("sections") or [] if isinstance(s, dict)}
    for sid in over:
        sec, s = sections.get(sid), plan.get(sid)
        if sec is None or s is None or s.get("word_budget") is None:
            return None
        hi = s["word_budget"] + tolerance(s["word_budget"])
        keep = set(s.get("must_cover") or [])
        while _section_words(sec, word_re) > hi:
            if not _drop_last_sentence(sec, keep):
                return None
    return new
