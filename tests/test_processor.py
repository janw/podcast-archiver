from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.enums import JobResult
from podcast_archiver.models import FeedPage
from podcast_archiver.processor import FeedProcessor

if TYPE_CHECKING:
    from pydantic_core import Url
    from responses import RequestsMock


@pytest.mark.parametrize(
    "file_exists,database_exists,expected_result",
    [
        (False, False, None),
        (True, False, JobResult.ALREADY_EXISTS_DISK),
        (False, True, JobResult.ALREADY_EXISTS_DB),
    ],
)
def test_preflight_check(
    tmp_path_cd: Path,
    feedobj_lautsprecher: Url,
    file_exists: bool,
    database_exists: bool,
    expected_result: JobResult | None,
) -> None:
    settings = Settings()
    feed = FeedPage.model_validate(feedobj_lautsprecher)
    episode = feed.episodes[0]
    target = Path("file.mp3")
    proc = FeedProcessor(settings)
    if file_exists:
        target.touch()
    with patch.object(settings.database_obj, "exists", return_value=database_exists):
        result = proc._preflight_check(episode, target=target)

    assert result == expected_result


def test_retrieve_failure(responses: RequestsMock) -> None:
    settings = Settings()
    proc = FeedProcessor(settings)

    assert proc.process("https://broken.url.invalid") is False
