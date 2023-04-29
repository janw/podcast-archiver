from podcast_archiver.base import PodcastArchiver


def test_instantiate():
    pa = PodcastArchiver()

    assert "user-agent" in pa.session.headers
    assert pa.session.headers["user-agent"].startswith("podcast-archiver")
    assert len(pa.feedlist) == 0
