from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import feedparser
import pytest
from responses import RequestsMock

from podcast_archiver.models.episode import Episode
from podcast_archiver.models.misc import Link

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FEED_URL = "https://feeds.metaebene.me/lautsprecher/m4a"
MEDIA_URL = re.compile("https://der-lautsprecher.de/.*.m4a")


FEED_CONTENT = (FIXTURES_DIR / "feed_lautsprecher.xml").read_text()
FEED_CONTENT_EMPTY = (FIXTURES_DIR / "feed_lautsprecher_empty.xml").read_text()

FEED_OBJ = feedparser.parse(FEED_CONTENT)


@pytest.fixture(scope="function")
def responses() -> Iterable[RequestsMock]:
    with RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def feed_lautsprecher(responses: RequestsMock) -> str:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT)
    responses.add(responses.GET, MEDIA_URL, b"BLOB")
    return FEED_URL


@pytest.fixture
def feed_lautsprecher_file() -> str:
    return f'file:{FIXTURES_DIR/ "feed_lautsprecher.xml"}'


@pytest.fixture
def feed_lautsprecher_notconsumed(responses: RequestsMock) -> str:
    return FEED_URL


@pytest.fixture
def feed_lautsprecher_onlyfeed(responses: RequestsMock) -> str:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT)
    return FEED_URL


@pytest.fixture
def feed_lautsprecher_empty(responses: RequestsMock) -> str:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT_EMPTY)
    return FEED_URL


@pytest.fixture
def feedobj_lautsprecher(responses: RequestsMock) -> dict[str, Any]:
    responses.assert_all_requests_are_fired = False
    responses.add(responses.GET, MEDIA_URL, b"BLOB")
    return FEED_OBJ


@pytest.fixture
def feedobj_lautsprecher_notconsumed(responses: RequestsMock) -> dict[str, Any]:
    return FEED_OBJ


@pytest.fixture
def tmp_path_cd(request: pytest.FixtureRequest, tmp_path: str) -> Iterable[str]:
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(request.config.invocation_params.dir)


@pytest.fixture
def episode() -> Episode:
    return Episode(
        title="Some Episode",
        subtitle="The unreleased version",
        author="Janw",
        published_parsed=datetime(2023, 3, 12, 12, 34, 56, tzinfo=timezone.utc),
        links=[
            Link(
                rel="enclosure",
                link_type="audio/mpeg",
                href="http://nowhere.invalid/file.mp3",
            ),
        ],
    )
