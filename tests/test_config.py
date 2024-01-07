from pathlib import Path

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.exceptions import InvalidSettings

DUMMY_FEED = "http://localhost/feed.rss"


def test_load(tmp_path_cd: Path):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{DUMMY_FEED}]")

    settings = Settings.load_from_yaml(configfile)

    assert DUMMY_FEED in settings.feeds


def test_load_invalid_yaml(tmp_path_cd: Path):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("!randomgiberish")

    with pytest.raises(InvalidSettings, match="Not a valid YAML document"):
        Settings.load_from_yaml(configfile)


def test_load_invalid_type(tmp_path_cd: Path):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("feeds: 7")

    with pytest.raises(InvalidSettings, match="Input should be a valid list"):
        Settings.load_from_yaml(configfile)


def test_load_nonexistent(tmp_path_cd: Path):
    configfile = tmp_path_cd / "configtmp.yaml"

    with pytest.raises(FileNotFoundError):
        Settings.load_from_yaml(configfile)
