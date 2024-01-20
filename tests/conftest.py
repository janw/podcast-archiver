from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import feedparser
import pytest
from pydantic_core import Url

if TYPE_CHECKING:
    from responses import RequestsMock

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FEED_URL = "https://feeds.metaebene.me/lautsprecher/m4a"
MEDIA_URL = re.compile("https://der-lautsprecher.de/.*.m4a")


FEED_CONTENT = (FIXTURES_DIR / "feed_lautsprecher.xml").read_text()
FEED_CONTENT_EMPTY = (FIXTURES_DIR / "feed_lautsprecher_empty.xml").read_text()

FEED_OBJ = feedparser.parse(FEED_CONTENT)


@pytest.fixture
def feed_lautsprecher(responses: RequestsMock) -> Url:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT)
    responses.add(responses.GET, MEDIA_URL, b"BLOB")
    return Url(FEED_URL)


@pytest.fixture
def feed_lautsprecher_notconsumed(responses: RequestsMock) -> Url:
    return Url(FEED_URL)


@pytest.fixture
def feed_lautsprecher_onlyfeed(responses: RequestsMock) -> Url:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT)
    return Url(FEED_URL)


@pytest.fixture
def feed_lautsprecher_empty(responses: RequestsMock) -> Url:
    responses.add(responses.GET, FEED_URL, FEED_CONTENT_EMPTY)
    return Url(FEED_URL)


@pytest.fixture
def feedobj_lautsprecher(responses: RequestsMock) -> Url:
    responses.add(responses.GET, MEDIA_URL, b"BLOB")
    return FEED_OBJ


@pytest.fixture
def feedobj_lautsprecher_notconsumed(responses: RequestsMock) -> Url:
    return FEED_OBJ


@pytest.fixture
def tmp_path_cd(request: pytest.FixtureRequest, tmp_path: str) -> Iterable[str]:
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(request.config.invocation_params.dir)
