from podcast_archiver.base import PodcastArchiver


def test_instantiate():
    pa = PodcastArchiver()

    assert pa._userAgent.startswith("podcast-archiver")
    assert len(pa.feedlist) == 0
