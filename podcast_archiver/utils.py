from __future__ import annotations

import re
from pathlib import Path
from string import Formatter
from typing import TYPE_CHECKING, Any, Iterable, TypedDict, cast

from slugify import slugify as _slugify

if TYPE_CHECKING:
    from podcast_archiver.config import Settings
    from podcast_archiver.models import Episode, FeedInfo

filename_safe_re = re.compile(r'[/\\?%*:|"<>]')
slug_safe_re = re.compile(r"[^A-Za-z0-9-_\.\/]+")


MIMETYPE_EXTENSION_MAPPING: dict[str, str] = {
    "audio/mp4": "m4a",
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
}


def get_generic_extension(link_type: str) -> str:
    return MIMETYPE_EXTENSION_MAPPING.get(link_type, "ext")


def make_filename_safe(value: str) -> str:
    return filename_safe_re.sub("-", value)


def slugify(value: str) -> str:
    return cast(
        str,
        _slugify(
            value,
            lowercase=False,
            regex_pattern=slug_safe_re,
            replacements=[
                ("Ü", "UE"),
                ("ü", "ue"),
                ("Ö", "OE"),
                ("ö", "oe"),
                ("Ä", "AE"),
                ("ä", "ae"),
            ],
        ),
    )


class FormatterKwargs(TypedDict, total=False):
    episode: Episode
    show: FeedInfo
    ext: str


DATETIME_FIELDS = {"episode.published_time"}
DEFAULT_DATETIME_FMT = "%Y-%m-%d"


class FilenameFormatter(Formatter):
    _template: str
    _slugify: bool
    _path_root: Path

    _parsed: list[tuple[str, str | None, str | None, str | None]]

    def __init__(self, settings: Settings) -> None:
        self._template = settings.filename_template
        self._slugify = settings.slugify_paths
        self._path_root = settings.archive_directory

    def parse(  # type: ignore[override]
        self,
        format_string: str,
    ) -> Iterable[tuple[str, str | None, str | None, str | None]]:
        for literal_text, field_name, format_spec, conversion in super().parse(format_string):
            if field_name in DATETIME_FIELDS and not format_spec:
                format_spec = DEFAULT_DATETIME_FMT
            yield literal_text, field_name, format_spec, conversion

    def format_field(self, value: Any, format_spec: str) -> str:
        formatted: str = super().format_field(value, format_spec)
        if self._slugify:
            return slugify(formatted)
        return make_filename_safe(formatted)

    def format(self, episode: Episode, feed_info: FeedInfo) -> Path:  # type: ignore[override] # noqa: A003
        kwargs: FormatterKwargs = {
            "episode": episode,
            "show": feed_info,
            "ext": episode.ext,
        }
        return self._path_root / self.vformat(self._template, args=(), kwargs=kwargs)
