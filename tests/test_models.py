from __future__ import annotations

import time
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Protocol

import pytest
from pydantic import ValidationError
from responses import RequestsMock

from podcast_archiver.exceptions import NotModified, NotSupported
from podcast_archiver.models.episode import Episode
from podcast_archiver.models.feed import Feed, FeedInfo, FeedPage
from podcast_archiver.utils import MIMETYPE_EXTENSION_MAPPING
from tests.conftest import FEED_CONTENT

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class EpisodeDict(TypedDict, total=False):
        title: str
        title_detail: dict[str, Any]
        summary: str
        summary_detail: dict[str, Any]
        published: str
        published_parsed: time.struct_time
        links: list[dict[str, Any]]
        id: str
        guidislink: bool
        authors: list[dict[str, Any]]
        author: str
        author_detail: dict[str, Any]
        subtitle: str
        subtitle_detail: dict[str, Any]
        content: list[dict[str, Any]]
        image: dict[str, Any]
        itunes_explicit: bool | None


# cSpell:ignore Napolitano, WWDC, Ritchie, Siri
EPISODE_FIXTURE: EpisodeDict = {
    "title": "83: Linda Dong & Lia Napolitano on prototyping experience",
    "title_detail": {
        "type": "text/plain",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "83: Linda Dong & Lia Napolitano on prototyping experience",
    },
    "summary": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
    "summary_detail": {
        "type": "text/html",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
    },
    "published": "Fri, 23 Dec 2016 09:55:09 -0500",
    "published_parsed": time.struct_time((2016, 12, 23, 14, 55, 9, 4, 358, 0)),
    "links": [
        {
            "length": "85468157",
            "type": "audio/mpeg",
            "href": "http://traffic.libsyn.com/zenandtech/debug83.mp3",
            "rel": "enclosure",
        }
    ],
    "id": "5A8152FA-82F0-4BF2-9F29-EC87A46DADD3",
    "guidislink": False,
    "authors": [{"name": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie"}],
    "author": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie",
    "author_detail": {"name": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie"},
    "subtitle": "Formerly on the Apple prototype team that brought us Pencil, and Siri experience team that put voices in cars and TV, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded after WWDC 2016 in June… but saved for now!",
    "subtitle_detail": {
        "type": "text/plain",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "Formerly on the Apple prototype team that brought us Pencil, and Siri experience team that put voices in cars and TV, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded after WWDC 2016 in June… but saved for now!",
    },
    "content": [
        {
            "type": "application/json",
            "language": None,
            "value": '{\\"some_value\\":12}',
        },
        {
            "type": "text/plain",
            "language": None,
            "base": "https://feeds.feedburner.com/debugshow",
            "value": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
        },
        {
            "type": "text/html",
            "language": None,
            "base": "https://feeds.feedburner.com/debugshow",
            "value": "<p>Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!</p>",
        },
    ],
    "image": {"href": "http://www.mobilenations.com/broadcasting/podcast_debug_1400.jpg"},
    "itunes_explicit": None,
}


def test_episode_validation() -> None:
    episode = Episode.model_validate(EPISODE_FIXTURE)

    assert episode.title == "83: Linda Dong & Lia Napolitano on prototyping experience"
    assert episode.enclosure.href == "http://traffic.libsyn.com/zenandtech/debug83.mp3"
    assert episode.original_filename == "debug83.mp3"
    assert episode.ext == "mp3"

    assert episode.shownotes
    assert episode.shownotes.startswith("<p>")
    assert episode.shownotes.endswith("</p>")


def test_episode_validation_invalid_enclosure() -> None:
    fixture = deepcopy(EPISODE_FIXTURE)
    fixture["links"][0]["href"] = "www.i-cannot-even-http.invalid"

    with pytest.raises(ValidationError):
        Episode.model_validate(fixture)


def test_episode_validation_invalid_other_link() -> None:
    fixture = deepcopy(EPISODE_FIXTURE)
    fixture["links"].append(
        {
            "href": "www.i-cannot-even-http.invalid",
        }
    )

    episode = Episode.model_validate(fixture)

    assert episode.title == "83: Linda Dong & Lia Napolitano on prototyping experience"
    assert episode.enclosure.href == "http://traffic.libsyn.com/zenandtech/debug83.mp3"
    assert episode.original_filename == "debug83.mp3"
    assert episode.ext == "mp3"

    assert episode.shownotes
    assert episode.shownotes.startswith("<p>")
    assert episode.shownotes.endswith("</p>")


def test_episode_validation_shownotes_fallback() -> None:
    data = EPISODE_FIXTURE.copy()
    data["content"].pop(-1)

    episode = Episode.model_validate(data)

    assert episode.shownotes
    assert episode.shownotes.startswith("Formerly on the Apple")
    assert episode.shownotes.endswith("Grab a beverage and hit play!")


@pytest.mark.parametrize("urlpath", ["", "zenandtech/debug83"])
@pytest.mark.parametrize("mimetype,expected_ext", list(MIMETYPE_EXTENSION_MAPPING.items()))
def test_episode_missing_ext(urlpath: str, mimetype: str, expected_ext: str) -> None:
    episode = Episode.model_validate(
        {
            "title": "83: …",
            "published_parsed": time.struct_time((2016, 12, 23, 14, 55, 9, 4, 358, 0)),
            "links": [
                {
                    "length": "85468157",
                    "type": mimetype,
                    "href": f"http://traffic.libsyn.com/{urlpath}",
                    "rel": "enclosure",
                }
            ],
        }
    )

    assert episode.enclosure.href == f"http://traffic.libsyn.com/{urlpath}"
    assert episode.ext == expected_ext


def test_invalid_link_length() -> None:
    assert Episode.model_validate(
        {
            "title": "83: …",
            "published_parsed": time.struct_time((2016, 12, 23, 14, 55, 9, 4, 358, 0)),
            "links": [
                {
                    "length": "nonsense",
                    "type": "audio/mpeg",
                    "href": "http://traffic.libsyn.com/zenandtech/debug83",
                    "rel": "enclosure",
                }
            ],
        }
    )


class FeedConstructor(Protocol):
    def __call__(self, url: str, *, known_info: FeedInfo | None = None) -> object: ...


@pytest.mark.vcr
def test_feed_from_webpage_with_alternate() -> None:
    page = FeedPage.from_url("https://der-lautsprecher.de/")
    assert page.feed.title == "Der Lautsprecher"


@pytest.mark.vcr
def test_feed_from_webpage_not_supported() -> None:
    with pytest.raises(NotSupported):
        FeedPage.from_url("https://example.com/")


@pytest.mark.parametrize("constructor", [FeedPage.from_url, Feed])
def test_feed_with_known_info_not_modified(constructor: FeedConstructor, feed_lautsprecher_onlyfeed: str) -> None:
    info = FeedPage.from_url(feed_lautsprecher_onlyfeed).feed
    info.last_modified = "sometime"

    with RequestsMock() as responses, pytest.raises(NotModified):
        responses.get(feed_lautsprecher_onlyfeed, status=304)
        constructor(feed_lautsprecher_onlyfeed, known_info=info)


@pytest.mark.parametrize("constructor", [FeedPage.from_url, Feed])
def test_feed_with_known_info_updated_time(constructor: FeedConstructor, feed_lautsprecher_onlyfeed: str) -> None:
    info = FeedPage.from_url(feed_lautsprecher_onlyfeed).feed
    info.last_modified = None

    with RequestsMock() as responses, pytest.raises(NotModified):
        responses.get(feed_lautsprecher_onlyfeed, FEED_CONTENT)
        constructor(feed_lautsprecher_onlyfeed, known_info=info)


@pytest.mark.parametrize("constructor", [FeedPage.from_url, Feed])
def test_feed_with_known_info_updated_time_empty(constructor: FeedConstructor, feed_lautsprecher_onlyfeed: str) -> None:
    info = FeedPage.from_url(feed_lautsprecher_onlyfeed).feed
    info.updated_time = None
    with RequestsMock() as responses:
        responses.get(feed_lautsprecher_onlyfeed, FEED_CONTENT)
        assert constructor(feed_lautsprecher_onlyfeed, known_info=info)
