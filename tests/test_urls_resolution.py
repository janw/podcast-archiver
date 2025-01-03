from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from podcast_archiver.urls import registry
from podcast_archiver.urls.base64 import Base64EncodedUrlSource
from podcast_archiver.urls.fireside import FiresideSource
from podcast_archiver.urls.prefixed import UrlPrefixSource
from podcast_archiver.urls.soundcloud import SoundCloudSource

if TYPE_CHECKING:
    from responses import RequestsMock


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://pcasts.in/feed/logbuch-netzpolitik.de/feed/mp3",
            "http://logbuch-netzpolitik.de/feed/mp3",
        ),
    ],
)
def test_urls_prefixed(url: str, expected_feed: str) -> None:
    feed = UrlPrefixSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://podcasts.google.com/?feed=aHR0cHM6Ly9hdWRpb2Jvb20uY29tL2NoYW5uZWxzLzUwMDI0ODIucnNz",
            "https://audioboom.com/channels/5002482.rss",  # defunct
        ),
    ],
)
def test_urls_base64_encoded(url: str, expected_feed: str) -> None:
    feed = Base64EncodedUrlSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://soundcloud.com/the-holden-village-podcast",
            "https://feeds.soundcloud.com/users/soundcloud:users:242076976/sounds.rss",
        ),
        (
            "https://soundcloud.com/trueundergroundone",  # result is defunct, maybe feed not enabled?
            "https://feeds.soundcloud.com/users/soundcloud:users:7315455/sounds.rss",
        ),
        (
            "https://soundcloud.com/janwillhaus",
            "https://feeds.soundcloud.com/users/soundcloud:users:1661683/sounds.rss",
        ),
    ],
)
@pytest.mark.vcr
def test_urls_supported_soundcloud(url: str, expected_feed: str) -> None:
    feed = SoundCloudSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize("status_code", [400, 200])
@pytest.mark.parametrize(
    "url",
    [
        "https://soundcloud.com/janwillhaus",
    ],
)
def test_urls_supported_soundcloud_failure_modes(responses: RequestsMock, status_code: int, url: str) -> None:
    responses.get(url, status=status_code)
    feed = SoundCloudSource().parse(url)
    assert feed is None


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://www.backtowork.limo",
            None,  # hosted on Fireside but uses a custom domain
        ),
        (
            "https://podrocket.logrocket.com",
            None,  # hosted on Fireside but uses a custom domain
        ),
        (
            "https://standinginthefire.fireside.fm/",
            "https://feeds.fireside.fm/standinginthefire/rss",
        ),
    ],
)
def test_urls_supported_fireside(url: str, expected_feed: str) -> None:
    feed = FiresideSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://pcasts.in/feed/logbuch-netzpolitik.de/feed/mp3",
            "http://logbuch-netzpolitik.de/feed/mp3",
        ),
        (
            "https://standinginthefire.fireside.fm/",
            "https://feeds.fireside.fm/standinginthefire/rss",
        ),
        (
            "https://castro.fm/podcast/f996ae94-70a2-4d9c-afbc-c70b5bacd120",
            "https://wochendaemmerung.podigee.io/feed/mp3",
        ),
        (
            "https://podcasts.google.com/?feed=aHR0cHM6Ly9hdWRpb2Jvb20uY29tL2NoYW5uZWxzLzUwMDI0ODIucnNz",
            "https://audioboom.com/channels/5002482.rss",  # defunct
        ),
    ],
    ids=[
        "prefixed",
        "fireside",
        "containing-apple",
        "base64",
    ],
)
@pytest.mark.vcr
def test_registry(url: str, expected_feed: str) -> None:
    feed = registry.get_feed(url)
    assert feed == expected_feed
