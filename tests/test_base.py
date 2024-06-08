from pathlib import Path

import pytest

from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings
from tests.conftest import FEED_URL, FIXTURES_DIR


@pytest.mark.parametrize(
    "opml_file",
    [
        FIXTURES_DIR / "opml_pocketcasts_valid.xml",
        FIXTURES_DIR / "opml_downcast_valid.xml",
    ],
)
def test_add_opml(opml_file: Path) -> None:
    pa = PodcastArchiver(Settings())
    pa.add_from_opml(opml_file)
    pa.add_from_opml(opml_file)
    pa.add_feed(FEED_URL)

    assert pa.feeds == [FEED_URL]
