from pathlib import Path

import pytest

from podcast_archiver.models import Feed

FILE_FIXTURE = Path(__file__).parent / "fixtures" / "feed_lautsprecher.xml"


def test_fetch_from_http(feed_lautsprecher_onlyfeed: str) -> None:
    assert Feed.from_url(feed_lautsprecher_onlyfeed)


@pytest.mark.parametrize(
    "url",
    [
        f"file:{FILE_FIXTURE}",
        f"file://{FILE_FIXTURE}",
    ],
)
def test_fetch_from_file(url: str) -> None:
    assert Feed.from_url(url)
