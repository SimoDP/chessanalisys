"""AC-05: V03 on the strings of Appendix G.4 (after token replacement)."""

from __future__ import annotations

import pytest

from chessanalyst.verify.scan import Scanner

ALLOWED = [
    "Il cavallo punta alla casa d5.",
    "Le case d4 ed e5 sono il centro.",
    "Maia-2 è poco affidabile qui.",
    "Hai tre sistemi tra cui scegliere.",
    "{{m:Nb3@N4}} prepara {{plan:w:f3,Qd2@N3}}",
]
REJECTED = [
    "Hai 3 sistemi.",
    "Gioca Be3 subito.",
    "Dopo exd5 il centro si apre.",
    "Arrocca con O-O.",
    "La spinta g4-g5 è il piano.",
    "Attento alla diagonale a7–g1.",
    "Il Nero gioca ...b5.",
    "Succede nel 50% dei casi.",
    "Il motore dà +0,37.",
    "Dopo 6.Be3 la posizione è tesa.",
    "Il ♘ va in d5.",
    "Promuove con =Q.",
]


@pytest.fixture(scope="module")
def scanner(cfg):
    return Scanner(cfg.verify, cfg.wording["v03_allowed_literals"])


@pytest.mark.parametrize("text", ALLOWED)
def test_allowed(scanner, text):
    assert scanner.v03_hits(text) == []


@pytest.mark.parametrize("text", REJECTED)
def test_rejected(scanner, text):
    assert scanner.v03_hits(text)
