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
from podcast_archiver.constants import MAX_TITLE_LENGTH, REQUESTS_TIMEOUT, SUPPORTED_LINK_TYPES_RE
from podcast_archiver.exceptions import MissingDownloadUrl
from podcast_archiver.logging import logger
from podcast_archiver.session import session
from podcast_archiver.utils import get_generic_extension, truncate


class Link(BaseModel):
    rel: str = ""
    link_type: str = Field("", alias="type")
    href: quirks.LenientUrl
    length: int | None = Field(None, repr=False, exclude=True)

    @property
    def url(self) -> str:
        return str(self.href)


class Chapter(BaseModel):
    start: str
    title: str


class Content(BaseModel):
    content_type: str = Field("", alias="type")
    value: str = Field("")


class Episode(BaseModel):
    title: str = Field(default="Untitled Episode", title="episode.title")
    subtitle: str = Field("", repr=False, title="episode.subtitle")
    author: str = Field("", repr=False)
    link: quirks.LenientUrl | None = None
    links: list[Link] = Field(default_factory=list)
    enclosure: Link = Field(default=None, repr=False)  # type: ignore[assignment]
    published_time: datetime = Field(alias="published_parsed", title="episode.published_time")

    original_filename: str = Field(default="", repr=False, title="episode.original_filename")

    # Extended metadata for .info.json
    episode_number: int | None = Field(None, repr=False, alias="itunes_episode")
    episode_type: str | None = Field(
        None,
        repr=False,
        validation_alias="itunes_episodetype",
        serialization_alias="type",
    )
    is_explicit: bool | None = Field(None, repr=False, alias="itunes_explicit")

    summary: str | None = Field(None, repr=False)
    duration: str | None = Field(None, repr=False, alias="itunes_duration")
    chapters: list[Chapter] | None = Field(None, repr=False, alias="psc_chapters.chapters")
    shownotes: str | None = Field(None, repr=False)
    content: list[Content] | None = Field(None, repr=False, alias="content", exclude=True)

    _feed_info: FeedInfo

    @field_validator("published_time", mode="before")
    @classmethod
    def parse_from_struct_time(cls, value: Any) -> Any:
        if isinstance(value, struct_time):
            return datetime.fromtimestamp(mktime(value)).replace(tzinfo=timezone.utc)
        return value

    @field_validator("title", mode="after")
    @classmethod
    def truncate_title(cls, value: str) -> str:
        return truncate(value, MAX_TITLE_LENGTH)

    @model_validator(mode="after")
    def populate_shownotes(self) -> Episode:
        fallback = ""
        for cont in self.content or []:
            match cont.content_type:
                case "text/plain":
                    fallback = cont.value
                case "text/html":
                    self.shownotes = cont.value
                    return self
        if fallback and not self.shownotes:
            self.shownotes = fallback
        return self

    @model_validator(mode="after")
    def populate_enclosure(self) -> Episode:
        if not self.enclosure:
            self.enclosure = self._get_enclosure_url()
        self.original_filename = Path(self.enclosure.href.path).name if self.enclosure.href.path else ""
        return self

    def _get_enclosure_url(self) -> Link:
        for link in self.links:
            if (
                SUPPORTED_LINK_TYPES_RE.match(link.link_type) or link.rel == "enclosure"
            ) and link.href.host != quirks.INVALID_URL_PLACEHOLDER:
                return link
        raise MissingDownloadUrl(f"Episode {self} did not have a supported download URL")

    @cached_property
    def ext(self) -> str:
        if fname := self.original_filename:
            stem, sep, suffix = fname.rpartition(".")
            if stem and sep and suffix:
                return suffix
        return get_generic_extension(self.enclosure.link_type)

    @classmethod
    def field_titles(cls) -> list[str]:
        return [field.title for field in cls.model_fields.values() if field.title]


class FeedInfo(BaseModel):
    title: str = Field(default="Untitled Podcast", title="show.title")
    subtitle: str | None = Field(default=None, title="show.subtitle")
    author: str | None = Field(default=None, title="show.author")
    language: str | None = Field(default=None, title="show.language")
    link: AnyHttpUrl | None = None
    links: list[Link] = []

    @field_validator("title", mode="after")
    @classmethod
    def truncate_title(cls, value: str) -> str:
        return truncate(value, MAX_TITLE_LENGTH)

    @classmethod
    def field_titles(cls) -> list[str]:
        return [field.title for field in cls.model_fields.values() if field.title]


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


ALL_FIELD_TITLES = Episode.field_titles() + FeedInfo.field_titles()

ALL_FIELD_TITLES_STR = "'" + ", '".join(ALL_FIELD_TITLES) + "'"
