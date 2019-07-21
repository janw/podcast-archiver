from io import StringIO

import pytest

from podcast_archiver.feedlist import add_feeds_from_feedsfile
from podcast_archiver.feedlist import add_feeds_from_opml
from tests import fixturefile

TEST_FEEDS = [
    "http://alternativlos.org/alternativlos.rss",
    "http://logbuch-netzpolitik.de/feed/m4a",
    "http://not-safe-for-work.de/feed/m4a/",
    "http://raumzeit-podcast.de/feed/m4a/",
    "http://www.ard.de/static/radio/radiofeature/rss/podcast.xml",
]


@pytest.fixture(scope="module")
def feedsfile():
    return StringIO("\n".join(TEST_FEEDS))


def test_from_feedsfile(feedsfile):

    with feedsfile as fp:
        feeds = add_feeds_from_feedsfile(fp)

    assert feeds == TEST_FEEDS


def test_from_opml(feedsfile):

    with open(fixturefile("feeds.opml")) as fp:
        feeds = add_feeds_from_opml(fp)

    for feed in TEST_FEEDS:
        assert feed in feeds
