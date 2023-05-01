from pathlib import Path

import pytest

from podcast_archiver.config import Settings

DUMMY_FEED = "http://localhost/feed.rss"


def test_load_from_envvar_config_path(tmp_path_cd: Path, monkeypatch):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{DUMMY_FEED}]")

    monkeypatch.setenv("PODCAST_ARCHIVER_CONFIG", configfile)
    settings = Settings.load_from_yaml(None)

    assert DUMMY_FEED in settings.feeds


def test_load_from_envvar_config_path_nonexistent(monkeypatch):
    monkeypatch.setenv("PODCAST_ARCHIVER_CONFIG", "nonexistent")
    with pytest.raises(FileNotFoundError):
        Settings.load_from_yaml(None)


def test_load_from_envvar_config_path_overridden_by_arg(tmp_path_cd: Path, monkeypatch):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{DUMMY_FEED}]")

    monkeypatch.setenv("PODCAST_ARCHIVER_CONFIG", "nonexistent")
    settings = Settings.load_from_yaml(configfile)

    assert DUMMY_FEED in settings.feeds
