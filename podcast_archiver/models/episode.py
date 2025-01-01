from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
from rich.text import Span, Text

from podcast_archiver.constants import DEFAULT_DATETIME_FORMAT, MAX_TITLE_LENGTH
from podcast_archiver.exceptions import MissingDownloadUrl
from podcast_archiver.models.field_types import FallbackToNone, LenientDatetime
from podcast_archiver.models.misc import Link
from podcast_archiver.utils import get_generic_extension, truncate

if TYPE_CHECKING:
    from rich.console import RenderableType


class Chapter(BaseModel):
    start: str
    title: str


class Content(BaseModel):
    content_type: str = Field("", alias="type")
    value: str = Field("")


class BaseEpisode(BaseModel):
    title: str = Field(default="Untitled Episode", title="episode.title")
    links: list[Link] = Field(default_factory=list, repr=False)
    enclosure: Link = Field(default=None, repr=False)  # type: ignore[assignment]
    published_time: LenientDatetime = Field(alias="published_parsed", title="episode.published_time")

    original_filename: str = Field(default="", repr=False, title="episode.original_filename")
    original_title: str = Field(default="Untitled Episode", repr=False, validation_alias="title")

    guid: str = Field(default=None, alias="id")  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.published_time.strftime(DEFAULT_DATETIME_FORMAT)} {self.title}"

    def __rich__(self) -> RenderableType:
        return Text(f"{self.published_time:%Y-%m-%d} {self.title}", spans=[Span(0, 10, "dim")], end="")

    @field_validator("title", mode="after")
    @classmethod
    def truncate_title(cls, value: str) -> str:
        return truncate(value, MAX_TITLE_LENGTH)

    @model_validator(mode="after")
    def populate_enclosure(self) -> BaseEpisode:
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
    def ensure_guid(self) -> BaseEpisode:
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


class Episode(BaseEpisode):
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


EpisodeOrFallback = Annotated[Episode | BaseEpisode | None, FallbackToNone]
