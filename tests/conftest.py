from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FEED_URL = "https://feeds.metaebene.me/lautsprecher/m4a"
MEDIA_URL = re.compile("https://der-lautsprecher.de/.*.m4a")


FEED_CONTENT = (FIXTURES_DIR / "feed_lautsprecher.xml").read_text()
FEED_CONTENT_EMPTY = (FIXTURES_DIR / "feed_lautsprecher_empty.xml").read_text()


@pytest.fixture
def feed_lautsprecher(responses):
    responses.add(responses.GET, FEED_URL, FEED_CONTENT)
    responses.add(responses.GET, MEDIA_URL, b"BLOB")
    return FEED_URL


@pytest.fixture
def feed_lautsprecher_empty(responses):
    responses.add(responses.GET, FEED_URL, FEED_CONTENT_EMPTY)
    return FEED_URL
