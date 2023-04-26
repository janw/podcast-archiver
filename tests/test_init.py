from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def test_instantiate():
    pa = PodcastArchiver(settings=Settings())
    pa.run()

    assert "user-agent" in pa.session.headers
    assert pa.session.headers["user-agent"].startswith("podcast-archiver")
    assert len(pa.feedlist) == 0
