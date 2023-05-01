from pathlib import Path

from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_happy_path(tmp_path: Path, feed_lautsprecher):
    settings = Settings(archive_directory=tmp_path, feeds=[feed_lautsprecher])  # type: ignore[call-arg]
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 5


def test_happy_path_max_episodes(tmp_path: Path, feed_lautsprecher):
    settings = Settings(  # type: ignore[call-arg]
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
        maximum_episode_count=2,
    )
    pa = PodcastArchiver(settings)
    pa.addFeed(feed_lautsprecher)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 2


def test_happy_path_files_exist(tmp_path: Path, feed_lautsprecher):
    (tmp_path / "ls017-podcastverzeichnisse.m4a").touch()
    settings = Settings(  # type: ignore[call-arg]
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 5


def test_happy_path_update(tmp_path: Path, feed_lautsprecher):
    (tmp_path / "ls017-podcastverzeichnisse.m4a").touch()
    settings = Settings(  # type: ignore[call-arg]
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher],
        update_archive=True,
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 3
    assert not list(tmp_path.glob("ls016*.m4a"))
    assert not list(tmp_path.glob("ls015*.m4a"))


def test_happy_path_empty_feed(tmp_path: Path, feed_lautsprecher_empty):
    settings = Settings(  # type: ignore[call-arg]
        archive_directory=tmp_path,
        feeds=[feed_lautsprecher_empty],
        update_archive=True,
    )
    pa = PodcastArchiver(settings)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 0
