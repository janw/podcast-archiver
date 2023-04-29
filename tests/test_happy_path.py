from pathlib import Path

from podcast_archiver.base import PodcastArchiver


def test_happy_path(tmp_path: Path, feed_lautsprecher):
    pa = PodcastArchiver()
    pa.savedir = tmp_path
    pa.addFeed(feed_lautsprecher)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 5


def test_happy_path_max_episodes(tmp_path: Path, feed_lautsprecher):
    pa = PodcastArchiver()
    pa.savedir = tmp_path
    pa.addFeed(feed_lautsprecher)

    pa.maximumEpisodes = 2
    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 2


def test_happy_path_files_exist(tmp_path: Path, feed_lautsprecher):
    (tmp_path / "ls017-podcastverzeichnisse.m4a").touch()
    pa = PodcastArchiver()
    pa.savedir = tmp_path
    pa.addFeed(feed_lautsprecher)

    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 5


def test_happy_path_update(tmp_path: Path, feed_lautsprecher):
    (tmp_path / "ls017-podcastverzeichnisse.m4a").touch()
    pa = PodcastArchiver()
    pa.savedir = tmp_path
    pa.addFeed(feed_lautsprecher)

    pa.update = True
    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 3
    assert not list(tmp_path.glob("ls016*.m4a"))
    assert not list(tmp_path.glob("ls015*.m4a"))


def test_happy_path_empty_feed(tmp_path: Path, feed_lautsprecher_empty):
    pa = PodcastArchiver()
    pa.savedir = tmp_path
    pa.addFeed(feed_lautsprecher_empty)

    pa.update = True
    pa.run()

    files = list(tmp_path.glob("*.m4a"))
    assert len(files) == 0
