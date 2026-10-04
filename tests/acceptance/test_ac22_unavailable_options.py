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


@pytest.mark.parametrize("local,message", [
    ({"user": {"color": "both"}}, "Opzione disponibile da M4"),
    ({"user": {"detail_level": 2}}, "Opzione disponibile da M4"),
    ({"user": {"elo_white": 1500}}, "Opzione disponibile da M4"),
    ({"user": {"elo_scale": "chesscom"}}, "Scala chess.com non ancora configurata"),
])
def test_refused_from_configuration_also_in_interactive_flow(root, tmp_path, monkeypatch, capsys, local, message):
    """A value of a later milestone in config/local.yaml is refused, never ignored (D-30)."""
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
