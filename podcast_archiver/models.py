from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from time import mktime, struct_time
from typing import Any, Iterator

import feedparser
from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from podcast_archiver import quirks
from podcast_archiver.constants import REQUESTS_TIMEOUT, SUPPORTED_LINK_TYPES_RE
from podcast_archiver.exceptions import MissingDownloadUrl
from podcast_archiver.logging import logger
from podcast_archiver.session import session
from podcast_archiver.utils import get_generic_extension


class Link(BaseModel):
    rel: str = ""
    link_type: str = Field("", alias="type")
    href: quirks.LenientUrl
    length: int | None = Field(None, repr=False)

    @property
    def url(self) -> str:
        return str(self.href)


class Episode(BaseModel):
    title: str = "Untitled Episode"
    subtitle: str = Field("", repr=False)
    author: str = Field("", repr=False)
    link: quirks.LenientUrl | None = None
    links: list[Link] = Field(default_factory=list)
    media_link: Link = Field(default=None, repr=False)  # type: ignore[assignment]
    published_time: datetime = Field(alias="published_parsed")

    _feed_info: FeedInfo

    @field_validator("published_time", mode="before")
    @classmethod
    def parse_from_struct_time(cls, value: Any) -> Any:
        if isinstance(value, struct_time):
            return datetime.fromtimestamp(mktime(value)).replace(tzinfo=timezone.utc)
        return value

    @model_validator(mode="after")
    def populate_media_link(self) -> Episode:
        for link in self.links:
            if (
                SUPPORTED_LINK_TYPES_RE.match(link.link_type) or link.rel == "enclosure"
            ) and link.href.host != quirks.INVALID_URL_PLACEHOLDER:
                self.media_link = link
                return self
        raise MissingDownloadUrl(f"Episode {self} did not have a supported download URL")

    @cached_property
    def ext(self) -> str:
        if self.media_link.href.path and (fname := Path(self.media_link.href.path).name):
            stem, sep, suffix = fname.rpartition(".")
            if stem and sep and suffix:
                return suffix
        return get_generic_extension(self.media_link.link_type)


class FeedInfo(BaseModel):
    title: str = "Untitled Podcast"
    subtitle: str | None = None
    author: str | None = None
    language: str | None = None
    link: AnyHttpUrl | None = None
    links: list[Link] = []


class FeedPage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    feed: FeedInfo

    episodes: list[Episode] = Field(default_factory=list, validation_alias=AliasChoices("entries", "items"))

    bozo: bool | int = False
    bozo_exception: Exception | None = None

    @classmethod
    def from_url(cls, url: AnyHttpUrl) -> FeedPage:
        response = session.get(str(url), allow_redirects=True, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        feedobj = feedparser.parse(response.content)
        return cls.model_validate(feedobj)


class Feed:
    info: FeedInfo
    url: AnyHttpUrl

    _page: FeedPage | None

    def __init__(self, page: FeedPage, url: AnyHttpUrl) -> None:
        self.info = page.feed
        self.url = url
        self._page = page

        logger.info("Loaded feed for '%s' by %s", self.info.title, self.info.author)

    def __repr__(self) -> str:
        return f"Feed(name='{self}', url='{self.url}')"

    def __str__(self) -> str:
        return f"{self.info.title}"

    @classmethod
    def from_url(cls, url: AnyHttpUrl) -> Feed:
        logger.info("Parsing feed %s", url)
        return cls(page=FeedPage.from_url(url), url=url)

    def episode_iter(self, maximum_episode_count: int = 0) -> Iterator[Episode]:
        episode_count_total = 0
        page_count = 0
        while self._page:
            page_count += 1
            episode_count_page = 0
            for episode in self._page.episodes:
                yield episode
                episode_count_page += 1
                episode_count_total += 1

            logger.info("Found %s episodes on page %s", episode_count_page, page_count)
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
