from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.enums import DownloadResult
from podcast_archiver.models import FeedPage
from podcast_archiver.processor import FeedProcessor, ProcessingResult

if TYPE_CHECKING:
    from pydantic_core import Url
    from responses import RequestsMock


@pytest.mark.parametrize(
    "file_exists,database_exists,expected_result",
    [
        (False, False, None),
        (True, False, DownloadResult.ALREADY_EXISTS),
        (False, True, DownloadResult.ALREADY_EXISTS),
    ],
)
def test_preflight_check(
    tmp_path_cd: Path,
    feedobj_lautsprecher: Url,
    file_exists: bool,
    database_exists: bool,
    expected_result: DownloadResult | None,
) -> None:
    settings = Settings()
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]
    target = Path("file.mp3")
    proc = FeedProcessor(settings)
    if file_exists:
        target.touch()
    with patch.object(proc.database, "exists", return_value=database_exists):
        result = proc._preflight_check(episode, target=target)

    assert result == expected_result


def test_retrieve_failure(responses: RequestsMock) -> None:
    settings = Settings()
    proc = FeedProcessor(settings)

    result = proc.process("https://broken.url.invalid")

    assert result == ProcessingResult()
    assert result.feed is None
