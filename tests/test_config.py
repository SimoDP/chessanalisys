from __future__ import annotations

import shutil

import pytest

from chessanalyst.config import CONFIG_FILES, load_config, write_local_config
from chessanalyst.errors import ConfigError


def copy_project(root, tmp_path):
    (tmp_path / "config").mkdir()
    for name in CONFIG_FILES:
        shutil.copy(root / "config" / name, tmp_path / "config" / name)
    return tmp_path


def test_all_files_load(cfg):
    assert set(cfg.thresholds.band_params) == {"lt1200", "1200_1600", "1600_2000", "2000_2400", "ge2400"}
    assert cfg.thresholds.band_params["1600_2000"].K == 5
    assert cfg.exploration.profiles["deep"].multipv.root == 16
    assert cfg.maia2_limits.top_bucket_lower == 2000
    assert cfg.default.user.color == "white"  # D-53
    assert cfg.section_titles["S07_alt"]["1900"].startswith("Risposte probabili")
    assert len(cfg.config_hash) == 40


def test_unquoted_numeric_key_is_rejected(root, tmp_path):
    proj = copy_project(root, tmp_path)
    p = proj / "config" / "thresholds.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace('"1200_1600": {lo: 1200', "1200_1600: {lo: 1200"),
                 encoding="utf-8")
    with pytest.raises(ConfigError, match="chiave non stringa"):
        load_config(proj)


def test_unknown_key_is_rejected(root, tmp_path):
    proj = copy_project(root, tmp_path)
    p = proj / "config" / "default.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "surprise: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(proj)


def test_local_overrides_default(root, tmp_path):
    proj = copy_project(root, tmp_path)
    write_local_config(proj, {"engines": {"stockfish": {"path": "/opt/sf"}}})
    cfg = load_config(proj)
    assert cfg.default.engines.stockfish.path == "/opt/sf"
    assert cfg.default.engines.stockfish.hash_mb == 4096  # untouched


def test_config_hash_tracks_exploration_only(root, tmp_path):
    proj = copy_project(root, tmp_path)
    h0 = load_config(proj).config_hash
    w = proj / "config" / "wording.yaml"
    w.write_text(w.read_text(encoding="utf-8") + "\n# commento\n", encoding="utf-8")
    assert load_config(proj).config_hash == h0
    e = proj / "config" / "exploration.yaml"
    e.write_text(e.read_text(encoding="utf-8").replace("e4_min_p: 0.03", "e4_min_p: 0.04"), encoding="utf-8")
    assert load_config(proj).config_hash != h0
