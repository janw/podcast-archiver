from os import environ
from pathlib import Path
from unittest import mock

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.exceptions import InvalidSettings

DUMMY_FEED = "http://localhost/feed.rss"
DUMMY_CONFIG = f"""

feeds: [{DUMMY_FEED}]
archive_directory: '~'
opml_files: [~/an_opml.xml]

"""


def test_load(tmp_path_cd: Path) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(DUMMY_CONFIG)

    opml_file = tmp_path_cd / "an_opml.xml"
    opml_file.touch()

    with mock.patch.dict(environ, {"HOME": str(tmp_path_cd)}):
        settings = Settings.load_from_yaml(configfile)

    assert DUMMY_FEED in settings.feeds
    assert opml_file in settings.opml_files
    assert settings.archive_directory == tmp_path_cd


def test_load_invalid_yaml(tmp_path_cd: Path) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("!randomgibberish")

    with pytest.raises(InvalidSettings, match="Not a valid YAML document"):
        Settings.load_from_yaml(configfile)


def test_load_invalid_type(tmp_path_cd: Path) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("feeds: 7")

    with pytest.raises(InvalidSettings, match="Input should be a valid list"):
        Settings.load_from_yaml(configfile)


def test_load_nonexistent(tmp_path_cd: Path) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"

    with pytest.raises(FileNotFoundError):
        Settings.load_from_yaml(configfile)
