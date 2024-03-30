from pathlib import Path

import pytest
from click import BadParameter

from podcast_archiver.cli import main
from podcast_archiver.config import Settings
from podcast_archiver.exceptions import InvalidSettings

DUMMY_FEED = "http://localhost/feed.rss"


def test_load(tmp_path_cd: Path, default_settings_no_feeds: Settings) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{DUMMY_FEED}]")

    settings = Settings.load_and_merge_settings(configfile, **default_settings_no_feeds.model_dump())

    assert DUMMY_FEED in settings.feeds


def test_load_invalid_yaml(tmp_path_cd: Path, default_settings_no_feeds: Settings) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("!randomgibberish")

    with pytest.raises(InvalidSettings, match="Not a valid YAML document"):
        Settings.load_and_merge_settings(configfile, **default_settings_no_feeds.model_dump())


def test_load_invalid_type(tmp_path_cd: Path, default_settings_no_feeds: Settings) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("feeds: 7")

    with pytest.raises(InvalidSettings, match="Input should be a valid list"):
        Settings.load_and_merge_settings(configfile, **default_settings_no_feeds.model_dump())


def test_load_nonexistent(tmp_path_cd: Path) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"

    with pytest.raises(BadParameter, match="does not exist."):
        main.make_context("under_test", ["-c", str(configfile)])
