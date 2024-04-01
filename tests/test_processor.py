from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.enums import DownloadResult
from podcast_archiver.models import FeedPage
from podcast_archiver.processor import FeedProcessor

if TYPE_CHECKING:
    from pydantic_core import Url


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


# def test_download_already_exists(tmp_path_cd: Path, feedobj_lautsprecher_notconsumed: dict[str, Any]) -> None:
#     feed = FeedPage.model_validate(feedobj_lautsprecher_notconsumed)
#     episode = feed.episodes[0]

#     job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
#     job.target.parent.mkdir(exist_ok=True)
#     job.target.touch()
#     result = job()

#     assert result == (episode, DownloadResult.ALREADY_EXISTS)


# def test_download_aborted(tmp_path_cd: Path, feedobj_lautsprecher: dict[str, Any]) -> None:
#     feed = FeedPage.model_validate(feedobj_lautsprecher)
#     episode = feed.episodes[0]

#     job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
#     job.stop_event.set()
#     result = job()

#     assert result == (episode, DownloadResult.ABORTED)


# class PartialObjectMock(Protocol):
#     def __call__(self, side_effect: type[Exception]) -> mock.Mock: ...


# # mypy: disable-error-code="attr-defined"
# @pytest.mark.parametrize(
#     "failure_mode, side_effect, should_download",
#     [
#         (partial(mock.patch.object, download.session, "get"), HTTPError, False),
#         (partial(mock.patch.object, utils.os, "fsync"), IOError, True),
#     ],
# )
# def test_download_failed(
#     tmp_path_cd: Path,
#     feedobj_lautsprecher_notconsumed: dict[str, Any],
#     failure_mode: PartialObjectMock,
#     side_effect: type[Exception],
#     caplog: pytest.LogCaptureFixture,
#     should_download: bool,
#     responses: RequestsMock,
# ) -> None:
#     feed = FeedPage.model_validate(feedobj_lautsprecher_notconsumed)
#     episode = feed.episodes[0]
#     if should_download:
#         responses.add(responses.GET, MEDIA_URL, b"BLOB")

#     job = download.DownloadJob(episode=episode, target=Path("file.mp3"))
#     with failure_mode(side_effect=side_effect), caplog.at_level(logging.ERROR):
#         result = job()

#     assert result == (episode, DownloadResult.FAILED)
#     failure_rec = None
#     for record in caplog.records:
#         if record.message == "Download failed":
#             failure_rec = record
#             break

#     assert failure_rec
#     assert failure_rec.exc_info
#     exc_type, _, _ = failure_rec.exc_info
#     assert exc_type == side_effect, failure_rec.exc_info


# @pytest.mark.parametrize("write_info_json", [False, True])
# def test_download_info_json(tmp_path_cd: Path, feedobj_lautsprecher: dict[str, Any], write_info_json: bool) -> None:
#     feed = FeedPage.model_validate(feedobj_lautsprecher)
#     episode = feed.episodes[0]
#     job = download.DownloadJob(episode=episode, target=tmp_path_cd / "file.mp3", write_info_json=write_info_json)
#     result = job()

#     assert result == (episode, DownloadResult.COMPLETED_SUCCESSFULLY)
#     assert job.infojsonfile.exists() == write_info_json
