from __future__ import annotations

import pytest

from chessanalyst.golden.wordcount import count_words, raw_word_counts


@pytest.mark.parametrize("text,n", [
    ("Il cavallo va in d5.", 5),
    ("l'alfiere {{m:Nb3@N4}} è **forte**", 5),
    ("{{pv:PV1:6}}", 1),
    ("Tre sistemi: Inglese, Classico.", 4),
])
def test_appendix_g5(cfg, text, n):
    assert count_words(text, cfg.verify["word"]) == n


def test_raw_sections_are_mapped(cfg, root):
    c15 = raw_word_counts(root / "examples/golden/raw/najdorf_w_1500.md", cfg.verify["word"])
    assert list(c15) == ["S01", "S03", "S05", "S06", "S08", "S10", "S02"]
    c19 = raw_word_counts(root / "examples/golden/raw/najdorf_w_1900.md", cfg.verify["word"])
    assert {"S01", "S03", "S04", "S05", "S06", "S07", "S10"} <= set(c19)
    assert all(v > 0 for v in c19.values())
