from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Iterator
from urllib.parse import urlparse
from xml.sax import SAXParseException

import feedparser
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from podcast_archiver.constants import MAX_TITLE_LENGTH
from podcast_archiver.exceptions import NotModified, NotSupported
from podcast_archiver.logging import logger, rprint
from podcast_archiver.models.episode import EpisodeOrFallback
from podcast_archiver.models.field_types import LenientDatetime
from podcast_archiver.models.misc import Link
from podcast_archiver.session import session
from podcast_archiver.utils import truncate

if TYPE_CHECKING:
    from requests import Response


@dataclass(slots=True)
class Feed:
    url: str
    known_info: FeedInfo | None = field(repr=False)
    info: FeedInfo = field(init=False)

    _page: FeedPage | None = field(init=False)

    def __post_init__(self) -> None:
        self._page = FeedPage.from_url(self.url, known_info=self.known_info)
        self.info = self._page.feed
        logger.debug("Loaded feed for '%s' by %s from %s", self.info.title, self.info.author, self.url)

    def __repr__(self) -> str:
        return f"Feed(name='{self}', url='{self.url}')"

    def __str__(self) -> str:
        return str(self.info)

    @property
    def episodes(self) -> Iterator[EpisodeOrFallback]:
        episode_count_total = 0
        page_count = 0
        while self._page:
            page_count += 1
            episode_count_page = 0
            for episode in self._page.episodes:
                yield episode
                episode_count_page += 1
                episode_count_total += 1

            logger.debug("Found %s episodes on page %s", episode_count_page, page_count)
            self._get_next_page()

    def _get_next_page(self) -> None:
        if not self._page:
            return
        for link in self._page.feed.links:
            if link.rel == "next" and link.href:
                logger.debug("Found next page at %s", link.href)
                self._page = FeedPage.from_url(link.href)
                return
        logger.debug("Page was the last")
        self._page = None


class FeedInfo(BaseModel):
    title: str = Field(default="Untitled Podcast", title="show.title")
    subtitle: str | None = Field(default=None, title="show.subtitle")
    author: str | None = Field(default=None, title="show.author")
    language: str | None = Field(default=None, title="show.language")
    links: list[Link] = []

    updated_time: LenientDatetime | None = Field(default=None, alias="updated_parsed")
    last_modified: str | None = Field(default=None)

    def __str__(self) -> str:
        return self.title

    @field_validator("title", mode="after")
    @classmethod
    def truncate_title(cls, value: str) -> str:
        return truncate(value, MAX_TITLE_LENGTH)

    @classmethod
    def field_titles(cls) -> list[str]:
        return [field.title for field in cls.model_fields.values() if field.title]

    @property
    def alternate_rss(self) -> str | None:
        for link in self.links:
            if link.rel == "alternate" and link.link_type == "application/rss+xml":
                return link.href
        return None


class FeedPage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Bozo first so that following fields can access it in ValidationInfo context
    bozo: bool | int = False
    bozo_exception: Exception | None = None

    feed: FeedInfo

    episodes: list[EpisodeOrFallback] = Field(default_factory=list, validation_alias=AliasChoices("entries", "items"))

    @classmethod
    def parse_feed(cls, source: str | bytes, alt_url: str | None, retry: bool = False) -> FeedPage:
        feedobj = feedparser.parse(source)
        obj = cls.model_validate(feedobj)
        if not obj.bozo:
            return obj

        if (fallback_url := obj.feed.alternate_rss) and not retry:
            logger.info("Attempting to load alternate feed from '%s'", fallback_url)
            return cls.from_url(fallback_url, retry=True)

        url = source if isinstance(source, str) and not alt_url else alt_url
        if (exc := obj.bozo_exception) and isinstance(exc, SAXParseException):
            rprint(f"Feed content is not well-formed for {url}", style="warning")
            rprint(f"Attemping processing but here be dragons ({exc.getMessage()})", style="warninghint")

        raise NotSupported(f"Content at {url} is not supported")

    @classmethod
    def from_url(cls, url: str, *, known_info: FeedInfo | None = None, retry: bool = False) -> FeedPage:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return cls.parse_feed(parsed.path, None)

        if not known_info:
            return cls.from_response(session.get_and_raise(url), alt_url=url, retry=retry)

        response = session.get_and_raise(url, last_modified=known_info.last_modified)
        if response.status_code == HTTPStatus.NOT_MODIFIED:
            logger.debug("Server reported 'not modified' from %s, skipping fetch.", known_info.last_modified)
            raise NotModified(known_info)

        instance = cls.from_response(response, alt_url=url, retry=retry)
        if instance.feed.updated_time == known_info.updated_time:
            logger.debug("Feed's updated time %s did not change, skipping fetch.", known_info.updated_time)
            raise NotModified(known_info)

        return instance

    @classmethod
    def from_response(cls, response: Response, alt_url: str | None, retry: bool) -> FeedPage:
        instance = cls.parse_feed(response.content, alt_url=alt_url, retry=retry)
        instance.feed.last_modified = response.headers.get("Last-Modified")
        return instance
