from pathlib import Path

import pytest
from pydantic_core import Url

from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_happy_path(tmp_path: Path, default_settings: Settings) -> None:
    default_settings.quiet = True

    pa = PodcastArchiver(default_settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5


def test_happy_path_info_json(tmp_path: Path, default_settings: Settings) -> None:
    default_settings.quiet = True
    default_settings.write_info_json = True

    pa = PodcastArchiver(default_settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5
    files = list(tmp_path.glob("**/*.info.json"))
    assert len(files) == 5


def test_happy_path_max_episodes(
    tmp_path: Path, feed_lautsprecher: Url, capsys: pytest.CaptureFixture[str], default_settings: Settings
) -> None:
    default_settings.archive_directory = tmp_path
    default_settings.maximum_episode_count = 2

    pa = PodcastArchiver(default_settings)
    pa.add_feed(feed_lautsprecher)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    outerr = capsys.readouterr()
    assert len(files) == 2
    assert "Maximum episode count reached" in outerr.out


def test_happy_path_files_exist(tmp_path: Path, default_settings: Settings) -> None:
    (tmp_path / "LS015 Der Sender bin ich.m4a").touch()
    default_settings.filename_template = "{episode.title}.{ext}"

    pa = PodcastArchiver(default_settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 5


def test_happy_path_update(tmp_path: Path, default_settings: Settings) -> None:
    (tmp_path / "LS017 Podcastverzeichnisse.m4a").touch()  # cspell: disable-line
    default_settings.update_archive = True
    default_settings.filename_template = "{episode.title}.{ext}"

    pa = PodcastArchiver(default_settings)
    pa.run()

    files = list(tmp_path.glob("**/*.m4a"))
    assert len(files) == 3
    assert not list(tmp_path.glob("LS016*.m4a"))
    assert not list(tmp_path.glob("LS015*.m4a"))


def test_happy_path_empty_feed(
    tmp_path: Path, feed_lautsprecher_empty: Url, default_settings_no_feeds: Settings
) -> None:
    default_settings_no_feeds.feeds = [feed_lautsprecher_empty]

    pa = PodcastArchiver(default_settings_no_feeds)
    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 0
