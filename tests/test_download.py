from __future__ import annotations

import logging
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from unittest import mock

import pytest
from requests import HTTPError

from podcast_archiver import download, utils
from podcast_archiver.enums import DownloadResult
from podcast_archiver.models import FeedPage
from tests.conftest import MEDIA_URL

if TYPE_CHECKING:
    from responses import RequestsMock


def test_download_job(tmp_path_cd: Path, feedobj_lautsprecher: dict[str, Any]) -> None:
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]
    mock_progress = mock.Mock(return_value=None)
    job = download.DownloadJob(episode=episode, target=Path("file.mp3"), progress_callback=mock_progress)
    result = job()

    assert result == (episode, DownloadResult.COMPLETED_SUCCESSFULLY)
    mock_progress.assert_called()
    assert mock_progress.call_count == 2


def test_download_already_exists(tmp_path_cd: Path, feedobj_lautsprecher_notconsumed: dict[str, Any]) -> None:
    feed = FeedPage.model_validate(feedobj_lautsprecher_notconsumed)
    episode = feed.episodes[0]

    job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
    job.target.parent.mkdir(exist_ok=True)
    job.target.touch()
    result = job()

    assert result == (episode, DownloadResult.ALREADY_EXISTS)


def test_download_aborted(tmp_path_cd: Path, feedobj_lautsprecher: dict[str, Any]) -> None:
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]

    job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
    job.stop_event.set()
    result = job()

    assert result == (episode, DownloadResult.ABORTED)


class PartialObjectMock(Protocol):
    def __call__(self, side_effect: type[Exception]) -> mock.Mock: ...


# mypy: disable-error-code="attr-defined"
@pytest.mark.parametrize(
    "failure_mode, side_effect, should_download",
    [
        (partial(mock.patch.object, download.session, "get"), HTTPError, False),
        (partial(mock.patch.object, utils.os, "fsync"), IOError, True),
    ],
)
def test_download_failed(
    tmp_path_cd: Path,
    feedobj_lautsprecher_notconsumed: dict[str, Any],
    failure_mode: PartialObjectMock,
    side_effect: type[Exception],
    caplog: pytest.LogCaptureFixture,
    should_download: bool,
    responses: RequestsMock,
) -> None:
    feed = FeedPage.model_validate(feedobj_lautsprecher_notconsumed)
    episode = feed.episodes[0]
    if should_download:
        responses.add(responses.GET, MEDIA_URL, b"BLOB")

    job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
    with failure_mode(side_effect=side_effect), caplog.at_level(logging.ERROR):
        result = job()

    assert result == (episode, DownloadResult.FAILED)
    failure_rec = None
    for record in caplog.records:
        if record.message == "Download failed":
            failure_rec = record
            break

    assert failure_rec
    assert failure_rec.exc_info
    exc_type, _, _ = failure_rec.exc_info
    assert exc_type == side_effect, failure_rec.exc_info


@pytest.mark.parametrize("write_info_json", [False, True])
def test_download_info_json(tmp_path_cd: Path, feedobj_lautsprecher: dict[str, Any], write_info_json: bool) -> None:
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]
    job = download.DownloadJob(episode=episode, target=tmp_path_cd / "file.mp3", write_info_json=write_info_json)
    result = job()

    assert result == (episode, DownloadResult.COMPLETED_SUCCESSFULLY)
    assert job.infojsonfile.exists() == write_info_json
