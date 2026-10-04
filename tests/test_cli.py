from __future__ import annotations

import pytest

from chessanalyst.cli import main


@pytest.mark.parametrize("argv", [[], ["analyze", "--yes"], ["rerun", "out"], ["golden", "--packs"],
                                  ["golden", "--render"]])
def test_not_yet_available_commands_exit_2(argv, capsys):
    assert main(argv) == 2
    assert "disponibile da M1" in capsys.readouterr().err


def test_unknown_option_exit_2():
    with pytest.raises(SystemExit) as e:
        main(["--bogus"])
    assert e.value.code == 2
