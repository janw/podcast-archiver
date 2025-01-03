from __future__ import annotations

import os
import re
from contextlib import contextmanager
from functools import partial
from string import Formatter
from typing import IO, TYPE_CHECKING, Any, Generator, Iterable, Iterator, Literal, TypedDict, overload
from urllib.parse import urlparse

from pydantic import ValidationError
from requests import HTTPError
from slugify import slugify as _slugify

from podcast_archiver.exceptions import NotModified, NotSupported
from podcast_archiver.logging import logger, rprint

if TYPE_CHECKING:
    from pathlib import Path

    from podcast_archiver.config import Settings
    from podcast_archiver.models.episode import BaseEpisode
    from podcast_archiver.models.feed import FeedInfo

filename_safe_re = re.compile(r'[/\\?%*:|"<>]')
slug_safe_re = re.compile(r"[^A-Za-z0-9-_\.]+")


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
    return _slugify(
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
    )


def truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    truncated = value[:max_length]
    prefix, sep, suffix = truncated.rpartition(" ")
    if prefix and sep:
        return "".join((prefix, sep, "…"))
    return truncated[: max_length - 1] + "…"


class FormatterKwargs(TypedDict, total=False):
    episode: BaseEpisode
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

    def format(self, episode: BaseEpisode, feed_info: FeedInfo) -> Path:  # type: ignore[override]
        kwargs: FormatterKwargs = {
            "episode": episode,
            "show": feed_info,
            "ext": episode.ext,
        }
        return self._path_root / self.vformat(self._template, args=(), kwargs=kwargs)


@overload
@contextmanager
def atomic_write(target: Path, mode: Literal["w"] = "w") -> Iterator[IO[str]]: ...


@overload
@contextmanager
def atomic_write(target: Path, mode: Literal["wb"]) -> Iterator[IO[bytes]]: ...


@contextmanager
def atomic_write(target: Path, mode: Literal["w", "wb"] = "w") -> Iterator[IO[bytes]] | Iterator[IO[str]]:
    tempfile = target.with_suffix(".part")
    try:
        with tempfile.open(mode) as fp:
            yield fp
            fp.flush()
            os.fsync(fp.fileno())
        logger.debug("Moving file '%s' => '%s'", tempfile, target)
        os.rename(tempfile, target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        tempfile.unlink(missing_ok=True)


@contextmanager
def handle_feed_request(url: str) -> Generator[None, Any, None]:
    printerr = partial(rprint, style="error")
    try:
        yield
    except HTTPError as exc:
        logger.debug("Failed to request feed url %s", url, exc_info=exc)
        if (response := getattr(exc, "response", None)) is None:
            printerr(f"Failed to retrieve feed {url}: {exc}")
            return

        printerr(f"Received status code {response.status_code} for {exc.response.url}")
        if exc.response.url != url:
            rprint(f"Was redirect from {url}", style="errorhint")

    except ValidationError as exc:
        logger.debug("Feed validation failed for %s", url, exc_info=exc)
        printerr(f"Received invalid feed from {url}")

    except NotSupported as exc:
        logger.debug("Might not be a feed: %s", url, exc_info=exc)
        rprint(f"[error]URL {url} is not supported, might not be a feed.[/]")

    except NotModified as exc:
        logger.debug("Skipping retrieval for %s", exc.info)
        rprint(f"⏲ Feed of {exc.info} is unchanged, skipping.", style="success")

    except Exception as exc:
        logger.debug("Unexpected error for url %s", url, exc_info=exc)
        printerr(f"Failed to retrieve feed {url}: {exc}")


def get_field_titles() -> str:
    from podcast_archiver.models.episode import Episode
    from podcast_archiver.models.feed import FeedInfo

    all_field_titles = Episode.field_titles() + FeedInfo.field_titles()
    return "'" + ", '".join(all_field_titles) + "'"


def sanitize_url(url: str) -> str:
    parsed_url = urlparse(url)
    sanitized_netloc = parsed_url.hostname or ""
    if parsed_url.port:
        sanitized_netloc += f":{parsed_url.port}"
    return parsed_url._replace(netloc=sanitized_netloc, query="").geturl()
