import logging
import re
from pathlib import Path
from unittest import mock

import pytest
from pydantic_core import Url

from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_happy_path(tmp_path: Path, feed_lautsprecher: str) -> None:
    settings = Settings(archive_directory=tmp_path, feeds=[feed_lautsprecher], quiet=True)
    pa = PodcastArchiver(settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5


def test_happy_path_info_json(tmp_path: Path, feed_lautsprecher: str) -> None:
    settings = Settings(archive_directory=tmp_path, feeds=[feed_lautsprecher], quiet=True, write_info_json=True)
    pa = PodcastArchiver(settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5
    files = list(tmp_path.glob("**/*.info.json"))
    assert len(files) == 5


def test_happy_path_max_episodes(tmp_path: Path, feed_lautsprecher: str, caplog: pytest.LogCaptureFixture) -> None:
    settings = Settings(
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
        maximum_episode_count=2,
    )
    pa = PodcastArchiver(settings)
    pa.add_feed(feed_lautsprecher)

    with caplog.at_level(logging.INFO):
        pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 2

    for msg in caplog.messages:
        if "Maximum episode count reached" in msg:
            return

    raise AssertionError("Did not see max episode message in messages {caplog.messages}")


def test_happy_path_pretty_episode_range(
    tmp_path: Path, feed_lautsprecher: str, caplog: pytest.LogCaptureFixture
) -> None:
    settings = Settings(
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
    )
    pa = PodcastArchiver(settings)
    pa.add_feed(feed_lautsprecher)

    with (
        caplog.at_level(logging.INFO),
        mock.patch.object(settings.database_obj, "exists", side_effect=[False, False, True, True, False]),
    ):
        pa.run()

    output = caplog.text
    assert re.search(r"Missing:  LS019.+through LS018.+", output, re.MULTILINE)
    assert re.search(r"Exists:   LS017.+through LS016.+", output, re.MULTILINE)


def test_happy_path_files_exist(tmp_path: Path, feed_lautsprecher: str) -> None:
    (tmp_path / "LS015 Der Sender bin ich.m4a").touch()
    settings = Settings(
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
        filename_template="{episode.title}.{ext}",
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5


def test_happy_path_update(tmp_path: Path, feed_lautsprecher: Url, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "LS017 Podcastverzeichnisse.m4a").touch()  # cspell: disable-line
    settings = Settings(
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
        filename_template="{episode.title}.{ext}",
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5
    assert list(tmp_path.glob("LS016*.m4a"))
    assert list(tmp_path.glob("LS015*.m4a"))


def test_happy_path_empty_feed(tmp_path: Path, feed_lautsprecher_empty: Url) -> None:
    settings = Settings(
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher_empty],
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 0
