import feedparser
from pydantic_core import Url

from podcast_archiver import quirks
from podcast_archiver.models import FeedPage
from tests.conftest import FIXTURES_DIR


def test_invalid_link() -> None:
    fixture = FIXTURES_DIR / "feed_lautsprecher_invalid_link.xml"
    feed = feedparser.parse(fixture)

    page = FeedPage.model_validate(feed)

    assert isinstance(page.episodes[0].link, Url)
    assert page.episodes[0].link.host == quirks.INVALID_URL_PLACEHOLDER
