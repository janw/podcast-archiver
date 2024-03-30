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
def test_add_opml(opml_file: Path, default_settings_no_feeds: Settings) -> None:
    pa = PodcastArchiver(default_settings_no_feeds)
    pa.add_from_opml(opml_file)

    assert [str(f) for f in pa.feeds] == [FEED_URL]
