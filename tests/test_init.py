from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_instantiate(default_settings_no_feeds: Settings) -> None:
    pa = PodcastArchiver(settings=default_settings_no_feeds)
    pa.run()

    assert len(pa.feeds) == 0
