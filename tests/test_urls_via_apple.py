from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from podcast_archiver.urls.via_apple import (
    LOOKUP_URL,
    ApplePodcastsByIdSource,
    ApplePodcastsSource,
    ContainingApplePodcastsUrlSource,
)

if TYPE_CHECKING:
    from responses import RequestsMock


@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("https://geo.itunes.apple.com/ca/podcast/feed/id1028908750?at=11lLuB", "1028908750"),
        ("https://podcasts.apple.com/us/podcast/behind-the-bastards/id1373812661?i=1000476632637", "1373812661"),
        ("http://podcasts.apple.com/de/podcast/logbuch-netzpolitik/id476856034?l=en-GB", "476856034"),
        ("https://castro.fm/itunes/1287979850", "1287979850"),
        ("https://overcast.fm/itunes394775318/99-invisible", "394775318"),
        ("https://pca.st/itunes/1687250293", "1687250293"),
        ("https://castbox.fm/channel/id1139548?country=de", "1139548"),
        ("https://castbox.fm/channel/1139548?country=en-US", "1139548"),
        ("https://podcasts.apple.com/us/podcast/serial/id917918570", "917918570"),
    ],
)
def test_urls_supported_via_apple(url: str, expected_id: str) -> None:
    match = ApplePodcastsSource.pattern.match(url)
    assert match is not None
    assert match["podcast_id"] == expected_id


@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("https://apple.com/", None),
    ],
)
def test_urls_not_supported_via_apple(url: str, expected_id: str) -> None:
    match = ApplePodcastsSource.pattern.match(url)
    assert not match


@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("id1028908750", "1028908750"),
        ("1687250293", "1687250293"),
    ],
)
def test_urls_supported_match_via_apple_by_id(url: str, expected_id: str) -> None:
    match = ApplePodcastsByIdSource.pattern.match(url)
    assert match is not None
    assert match["podcast_id"] == expected_id


@pytest.mark.parametrize(
    "podcast_id, expected_feed",
    [
        ("917918570", "https://feeds.simplecast.com/PpzWFGhg"),
        ("1687250293", "https://glitterbrains.org/feed/mp3/"),
    ],
    ids=["serial", "glitterbrains"],
)
@pytest.mark.vcr
def test_lookup_feed_via_apple_by_id(podcast_id: str, expected_feed: str) -> None:
    feed = ApplePodcastsByIdSource.feed_by_id(podcast_id)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "http://podcasts.apple.com/de/podcast/logbuch-netzpolitik/id476856034?l=en-GB",
            "https://feeds.metaebene.me/lnp/mp3",
        ),
        (
            "https://overcast.fm/itunes394775318/99-invisible",
            "https://feeds.simplecast.com/BqbsxVfO",
        ),
        (
            "https://podcasts.apple.com/us/podcast/serial/id917918570",
            "https://feeds.simplecast.com/PpzWFGhg",
        ),
        ("https://apple.com/", None),
    ],
    ids=[
        "logbuch-netzpolitik",
        "99-invisible",
        "serial",
        "no-feed",
    ],
)
@pytest.mark.vcr
def test_parse_via_apple_id(url: str, expected_feed: str | None) -> None:
    feed = ApplePodcastsSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b'{"resultCount":0,"results":[]}',
    ],
)
@pytest.mark.parametrize("status_code", [400, 200])
def test_urls_supported_soundcloud_failure_modes(responses: RequestsMock, body: bytes, status_code: int) -> None:
    responses.get(LOOKUP_URL.format(podcast_id="394775318"), status=status_code, body=body)
    feed = ApplePodcastsSource().parse("https://overcast.fm/itunes394775318/99-invisible")
    assert feed is None


@pytest.mark.parametrize(
    "url, expected_matching",
    [
        (
            "https://castro.fm/podcast/f996ae94-70a2-4d9c-afbc-c70b5bacd120",
            True,
        ),
        (
            "https://overcast.fm/+AAyIOzrEy1g",
            True,
        ),
        ("https://apple.com/", False),
    ],
    ids=[
        "wochendaemmerung",
        "99-invisible",
        "no-feed",
    ],
)
def test_match_via_apple_in_another_page(url: str, expected_matching: bool) -> None:
    match = ContainingApplePodcastsUrlSource.page_pattern.match(url)
    assert bool(match) == expected_matching


@pytest.mark.parametrize(
    "url, expected_feed",
    [
        (
            "https://castro.fm/podcast/f996ae94-70a2-4d9c-afbc-c70b5bacd120",
            "https://wochendaemmerung.podigee.io/feed/mp3",
        ),
        (
            "https://overcast.fm/+AAyIOzrEy1g",
            "https://feeds.simplecast.com/BqbsxVfO",
        ),
        ("https://apple.com/", None),
    ],
    ids=[
        "wochendaemmerung",
        "99-invisible",
        "no-feed",
    ],
)
@pytest.mark.vcr
def test_parse_via_apple_in_another_page(url: str, expected_feed: str | None) -> None:
    feed = ContainingApplePodcastsUrlSource().parse(url)
    assert feed == expected_feed


@pytest.mark.parametrize(
    "url",
    [
        "https://castro.fm/podcast/f996ae94-70a2-4d9c-afbc-c70b5bacd120",
        "https://overcast.fm/+AAyIOzrEy1g",
    ],
    ids=[
        "wochendaemmerung",
        "99-invisible",
    ],
)
@pytest.mark.parametrize("status_code", [400, 200])
def test_parse_via_apple_in_another_page_not_ok(responses: RequestsMock, status_code: int, url: str) -> None:
    responses.get(url, status=status_code)
    feed = ContainingApplePodcastsUrlSource().parse(url)
    assert not feed
