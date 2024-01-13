from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_instantiate() -> None:
    pa = PodcastArchiver(settings=Settings())
    pa.run()

    assert len(pa.feeds) == 0
