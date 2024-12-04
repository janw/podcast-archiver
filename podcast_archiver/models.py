from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from http import HTTPStatus
from pathlib import Path
from time import mktime, struct_time
from typing import TYPE_CHECKING, Annotated, Any, Iterator
from urllib.parse import urlparse
from xml.sax import SAXParseException

import feedparser
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
    model_validator,
)
from pydantic.functional_validators import BeforeValidator

from podcast_archiver import compat
from podcast_archiver.constants import DEFAULT_DATETIME_FORMAT, MAX_TITLE_LENGTH
from podcast_archiver.exceptions import MissingDownloadUrl, NotModified
from podcast_archiver.logging import logger, rprint
from podcast_archiver.session import session
from podcast_archiver.utils import get_generic_extension, truncate

if TYPE_CHECKING:
    from requests import Response


def parse_from_struct_time(value: struct_time | datetime) -> datetime:
    if isinstance(value, struct_time):
        value = datetime.fromtimestamp(mktime(value))
    if not value.tzinfo:
        value = value.replace(tzinfo=compat.UTC)
    return value


def val_or_none(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    with suppress(ValidationError):
        return handler(value)
    return None


FallbackToNone = WrapValidator(val_or_none)

LenientDatetime = Annotated[datetime, BeforeValidator(parse_from_struct_time)]
LenientInt = Annotated[int | None, FallbackToNone]


class Link(BaseModel):
    rel: str = ""
    link_type: str = Field("", alias="type")
    href: str
    length: LenientInt = None


class Chapter(BaseModel):
    start: str
    title: str


class Content(BaseModel):
    content_type: str = Field("", alias="type")
    value: str = Field("")


class EpisodeSkeleton(BaseModel):
    title: str = Field(default="Untitled Episode", title="episode.title")
    links: list[Link] = Field(default_factory=list, repr=False)
    enclosure: Link = Field(default=None, repr=False)  # type: ignore[assignment]
    published_time: LenientDatetime = Field(alias="published_parsed", title="episode.published_time")

    original_filename: str = Field(default="", repr=False, title="episode.original_filename")

    guid: str = Field(default=None, alias="id")  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.title} ({self.published_time.strftime(DEFAULT_DATETIME_FORMAT)})"

    @field_validator("title", mode="after")
    @classmethod
    def truncate_title(cls, value: str) -> str:
        return truncate(value, MAX_TITLE_LENGTH)

    @model_validator(mode="after")
    def populate_enclosure(self) -> EpisodeSkeleton:
        for link in self.links:
            if link.rel != "enclosure":
                continue
            parsed_url = urlparse(link.href)
            if parsed_url.scheme and parsed_url.netloc:
                self.enclosure = link
                self.original_filename = Path(parsed_url.path).name if parsed_url.path else ""
                return self

        raise MissingDownloadUrl(f"Episode {self} did not have a supported download URL")

    @model_validator(mode="after")
    def ensure_guid(self) -> EpisodeSkeleton:
        if not self.guid:
            # If no GUID is given, use the enclosure url instead
            # See https://help.apple.com/itc/podcasts_connect/#/itcb54353390
            self.guid = self.enclosure.href
        return self

    @cached_property
    def ext(self) -> str:
        if fname := self.original_filename:
            stem, sep, suffix = fname.rpartition(".")
            if stem and sep and suffix:
                return suffix
        return get_generic_extension(self.enclosure.link_type)


class Episode(EpisodeSkeleton):
    subtitle: str = Field("", repr=False, title="episode.subtitle")
    author: str = Field("", repr=False)

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

    @classmethod
    def field_titles(cls) -> list[str]:
        return [field.title for field in cls.model_fields.values() if field.title]


EpisodeOrFallback = Annotated[Episode | EpisodeSkeleton | None, FallbackToNone]


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


class FeedPage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Bozo first so that following fields can access it in ValidationInfo context
    bozo: bool | int = False
    bozo_exception: Exception | None = None

    feed: FeedInfo

    episodes: list[EpisodeOrFallback] = Field(default_factory=list, validation_alias=AliasChoices("entries", "items"))

    @classmethod
    def parse_feed(cls, source: str | bytes, alt_url: str | None) -> FeedPage:
        feedobj = feedparser.parse(source)
        obj = cls.model_validate(feedobj)
        if obj.bozo and (exc := obj.bozo_exception) and isinstance(exc, SAXParseException):
            url = source if isinstance(source, str) and not alt_url else alt_url
            rprint(f"[orange1]Feed content is not well-formed for {url}[/]")
            rprint(f"[orange1 dim]Continuing processing but here be dragons ({exc.getMessage()})[/]")
        return obj

    @classmethod
    def from_url(cls, url: str, *, known_info: FeedInfo | None = None) -> FeedPage:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return cls.parse_feed(parsed.path, None)

        if not known_info:
            return cls.from_response(session.get_and_raise(url), alt_url=url)

        response = session.get_and_raise(url, last_modified=known_info.last_modified)
        if response.status_code == HTTPStatus.NOT_MODIFIED:
            logger.debug("Server reported 'not modified' from %s, skipping fetch.", known_info.last_modified)
            raise NotModified(known_info)

        instance = cls.from_response(response, alt_url=url)
        if instance.feed.updated_time == known_info.updated_time:
            logger.debug("Feed's updated time %s did not change, skipping fetch.", known_info.updated_time)
            raise NotModified(known_info)

        return instance

    @classmethod
    def from_response(cls, response: Response, alt_url: str | None) -> FeedPage:
        instance = cls.parse_feed(response.content, alt_url=alt_url)
        instance.feed.last_modified = response.headers.get("Last-Modified")
        return instance


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


ALL_FIELD_TITLES = Episode.field_titles() + FeedInfo.field_titles()

ALL_FIELD_TITLES_STR = "'" + ", '".join(ALL_FIELD_TITLES) + "'"
