from __future__ import annotations

import pytest

from chessanalyst.cli import main


def test_rerun_without_pack_exit_2(tmp_path, capsys):
    assert main(["rerun", str(tmp_path)]) == 2
    assert "pack.json" in capsys.readouterr().err


def test_frozen_golden_packs_need_force(capsys):
    assert main(["golden", "--packs"]) == 2          # refused before any engine is started
    assert "--force" in capsys.readouterr().err


def test_unknown_option_exit_2():
    with pytest.raises(SystemExit) as e:
        main(["--bogus"])
    assert e.value.code == 2
