from __future__ import annotations

from concurrent.futures import Future
from typing import TYPE_CHECKING, NamedTuple, Protocol, TypeAlias

if TYPE_CHECKING:
    from podcast_archiver.enums import DownloadResult
    from podcast_archiver.models import Episode


class EpisodeResult(NamedTuple):
    episode: Episode
    result: DownloadResult


class ProgressCallback(Protocol):
    def __call__(self, total: int | None = None, completed: int | None = None) -> None: ...


EpisodeResultsList: TypeAlias = list[Future[EpisodeResult] | EpisodeResult]
