"""Word count of §9-bis.8 and the M0 measurement of the raw golden files."""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

from chessanalyst.verify.wordcount import count_words  # noqa: F401 - re-exported

SECTION_MARK = re.compile(r"<!--\s*(S\d\d)\b")
COMMENT_RE = re.compile(r"<!--.*?-->")
NUMERIC_CELL = re.compile(r"[+\-−]?\d+,\d+")


def _strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def raw_section_texts(path: Path) -> "OrderedDict[str, list[str]]":
    """Prose of a raw file grouped by destination section (``<!-- Sxx -->``).

    Excluded (§8-bis.4 step 4): front matter, headings, HTML comments, the
    status blockquote, code lines, ``[MAIA]`` lines and numeric tables (a table
    with at least one ``±d,dd`` value). Text tables are counted cell by cell."""
    lines = _strip_front_matter(path.read_text(encoding="utf-8")).splitlines()
    out: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            m = SECTION_MARK.search(line)
            if m:
                current = m.group(1)
            elif line.startswith("# "):
                current = None
            i += 1
            continue
        if line.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            if current is None:
                continue
            body = [r for r in block[2:]]
            if any(NUMERIC_CELL.search(r) for r in body):
                continue
            for r in block:
                if re.match(r"^\s*\|[\s\-|:]+\|\s*$", r):
                    continue
                out.setdefault(current, []).extend(c.strip() for c in r.strip().strip("|").split("|"))
            continue
        i += 1
        if current is None:
            continue
        stripped = COMMENT_RE.sub("", line).strip()
        if not stripped or stripped.startswith(">") or stripped.startswith("`") or "[MAIA]" in stripped:
            continue
        out.setdefault(current, []).append(stripped)
    return out


def raw_word_counts(path: Path, word_re: str) -> "OrderedDict[str, int]":
    return OrderedDict((sid, sum(count_words(t, word_re) for t in texts))
                       for sid, texts in raw_section_texts(path).items())
