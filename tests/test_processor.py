from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import patch

import pytest

from podcast_archiver.enums import DownloadResult
from podcast_archiver.models import FeedPage
from podcast_archiver.processor import FeedProcessor, ProcessingResult
from podcast_archiver.types import EpisodeResult

if TYPE_CHECKING:
    from pydantic_core import Url
    from responses import RequestsMock

    from podcast_archiver.models import Episode
    from podcast_archiver.types import EpisodeResultsList


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
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]
    target = Path("file.mp3")
    proc = FeedProcessor()
    if file_exists:
        target.touch()
    with patch.object(proc.database, "exists", return_value=database_exists):
        result = proc._preflight_check(episode, target=target)

    assert result == expected_result


def test_retrieve_failure(responses: RequestsMock) -> None:
    proc = FeedProcessor()

    result = proc.process("https://broken.url.invalid")

    assert result == ProcessingResult()
    assert result.feed is None


def test_download_success(tmp_path_cd: Path, feed_lautsprecher: str) -> None:
    proc = FeedProcessor()

    result = proc.process(feed_lautsprecher)

    assert result != ProcessingResult()
    assert result.success == 5
    assert result.feed
    assert result.feed.url == feed_lautsprecher


def test_handle_results_mixed(episode: Episode) -> None:
    proc = FeedProcessor()
    episodes: EpisodeResultsList = [
        EpisodeResult(episode=episode, result=DownloadResult.COMPLETED_SUCCESSFULLY),
        EpisodeResult(episode=episode, result=DownloadResult.FAILED),
    ]

    with mock.patch.object(proc.database, "add", return_value=None) as mock_add:
        success, failures = proc._handle_results(episodes)

    assert success == 1
    assert failures == 1
    assert mock_add.call_count == 1


def test_handle_results_failure(episode: Episode) -> None:
    proc = FeedProcessor()
    episodes: EpisodeResultsList = [EpisodeResult(episode=episode, result=DownloadResult.ABORTED)]

    with mock.patch.object(proc.database, "add", return_value=None) as mock_add:
        success, failures = proc._handle_results(episodes)

    assert success == 0
    assert failures == 1
    mock_add.assert_not_called()


def test_handle_results_failed_future(episode: Episode) -> None:
    proc = FeedProcessor()
    episodes: EpisodeResultsList = [EpisodeResult(episode=episode, result=DownloadResult.ABORTED)]

    with mock.patch.object(proc.database, "add", return_value=None) as mock_add:
        success, failures = proc._handle_results(episodes)

    assert success == 0
    assert failures == 1
    mock_add.assert_not_called()
