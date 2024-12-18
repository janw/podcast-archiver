from pathlib import Path

import pytest

from podcast_archiver.models.feed import Feed

FILE_FIXTURE = Path(__file__).parent / "fixtures" / "feed_lautsprecher.xml"


def test_fetch_from_http(feed_lautsprecher_onlyfeed: str) -> None:
    assert Feed(feed_lautsprecher_onlyfeed, None)


@pytest.mark.parametrize(
    "url",
    [
        f"file:{FILE_FIXTURE}",
        f"file://{FILE_FIXTURE}",
    ],
)
def test_fetch_from_file(url: str) -> None:
    assert Feed(url, None)
