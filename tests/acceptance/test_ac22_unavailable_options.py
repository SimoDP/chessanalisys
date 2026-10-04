"""AC-22: options not available → explicit message and exit code 2 (D-30). From M4 «entrambi»,
``--elo-white``/``--elo-black`` and detail 1–5 are available; the chess.com scale stays refused while its table
is empty; invalid values and combinations are refused, never ignored."""

from __future__ import annotations

import pytest

from chessanalyst.cli import main


@pytest.mark.parametrize("argv,message", [
    (["--elo-scale", "chesscom"], "Scala chess.com non ancora configurata"),
    (["--detail", "0"], "Dettaglio non valido"),
    (["--detail", "6"], "Dettaglio non valido"),
    (["--elo-white", "1500"], "solo con --color both"),
    (["--color", "black", "--elo-black", "1500"], "solo con --color both"),
    (["--color", "both", "--opp-elo", "1500"], "--elo-white e --elo-black"),
    (["--color", "both", "--elo-white", "100"], "Elo non valido"),
])
def test_refused(argv, message, capsys, tmp_path):
    assert main(["analyze", "--yes", "--out", str(tmp_path)] + argv) == 2
    assert message in capsys.readouterr().err
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize("values", [{"detail": d, "color": "w"} for d in (1, 2, 3, 4, 5)]
                         + [{"color": "both", "elo_white": 1500, "elo_black": 2000}])
def test_m4_options_are_accepted_by_the_check(cfg, values):
    from chessanalyst.settings import check_available

    check_available(cfg, values)


@pytest.mark.parametrize("local,message", [
    ({"user": {"detail_level": 7}}, "Dettaglio non valido"),
    ({"user": {"elo_white": 1500}}, "solo con --color both"),
    ({"user": {"elo_scale": "chesscom"}}, "Scala chess.com non ancora configurata"),
])
def test_refused_from_configuration_also_in_interactive_flow(root, tmp_path, monkeypatch, capsys, local, message):
    """An invalid value in config/local.yaml is refused, never ignored (D-30)."""
    import shutil

    import yaml

    from chessanalyst.config import CONFIG_FILES

    proj = tmp_path / "proj"
    (proj / "config").mkdir(parents=True)
    for name in CONFIG_FILES:
        shutil.copy(root / "config" / name, proj / "config" / name)
    shutil.copytree(root / "examples", proj / "examples")
    (proj / "config" / "local.yaml").write_text(yaml.safe_dump(local))
    monkeypatch.setenv("CHESSANALYST_HOME", str(proj))
    monkeypatch.setenv("CHESSANALYST_CONFIG_DIR", str(tmp_path / "conf"))
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert main([]) == 2                                   # interactive flow
    assert message in capsys.readouterr().err
    assert main(["analyze", "--yes", "--out", str(tmp_path / "o")]) == 2
    assert not (tmp_path / "o").exists()
