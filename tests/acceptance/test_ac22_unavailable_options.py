"""AC-22: options not yet available → explicit message and exit code 2 (D-30)."""

from __future__ import annotations

import pytest

from chessanalyst.cli import main


@pytest.mark.parametrize("argv,message", [
    (["--color", "both"], "Opzione disponibile da M4"),
    (["--detail", "3"], "Opzione disponibile da M4"),
    (["--detail", "5"], "Opzione disponibile da M4"),
    (["--elo-white", "1500"], "Opzione disponibile da M4"),
    (["--elo-black", "1500"], "Opzione disponibile da M4"),
    (["--elo-scale", "chesscom"], "Scala chess.com non ancora configurata"),
])
def test_refused(argv, message, capsys, tmp_path):
    assert main(["analyze", "--yes", "--out", str(tmp_path)] + argv) == 2
    assert message in capsys.readouterr().err
    assert not any(tmp_path.iterdir())


def test_detail_4_is_accepted_by_the_check(cfg):
    from chessanalyst.settings import check_available

    check_available(cfg, {"detail": 4, "color": "w"})
