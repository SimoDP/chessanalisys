"""Free-text scans: forbidden markup (V01) and moves/digits in clear (V03).

Regular expressions come from ``config/verify.yaml`` (Appendix D.10)."""

from __future__ import annotations

import re


class Scanner:
    def __init__(self, verify_cfg: dict, allowed_literals: list[str]) -> None:
        v = verify_cfg["v03"]
        self.token = re.compile(v["token"])
        self.pass1 = {k: re.compile(p) for k, p in v["pass1"].items()}
        self.square = re.compile(v["square"])
        self.digit = re.compile(v["digit"])
        self.markup = [re.compile(p, re.M) for p in verify_cfg["v01_markup"]]
        self.literals = sorted(allowed_literals, key=len, reverse=True)

    def markup_hits(self, text: str) -> list[str]:
        """V01: lines starting with ``#``, links, backticks, HTML."""
        stripped = self.token.sub("§", text)
        return [m.group(0) for p in self.markup for m in p.finditer(stripped)]

    def v03_hits(self, text: str) -> list[str]:
        """V03 on the free text: tokens become ``§``, allowed literals are removed."""
        t = self.token.sub("§", text)
        for lit in self.literals:
            t = t.replace(lit, " ")
        hits = [f"{name}: {m.group(0)}" for name, p in self.pass1.items() for m in p.finditer(t)]
        rest = self.square.sub(" ", t)
        hits += [f"digit: {m.group(0)}" for m in self.digit.finditer(rest)]
        return hits
