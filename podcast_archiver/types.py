from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    from podcast_archiver.enums import DownloadResult, QueueCompletionType
    from podcast_archiver.models.episode import BaseEpisode
    from podcast_archiver.models.feed import Feed


@dataclass(slots=True, frozen=True)
class EpisodeResult:
    episode: BaseEpisode
    result: DownloadResult


@dataclass(slots=True, frozen=True)
class ProcessingResult:
    feed: Feed | None
    tombstone: QueueCompletionType
    success: int = 0
    failures: int = 0


class ProgressCallback(Protocol):
    def __call__(self, total: int | None = None, completed: int | None = None) -> None: ...


FutureEpisodeResult: TypeAlias = Future[EpisodeResult] | EpisodeResult
EpisodeResultsList: TypeAlias = list[FutureEpisodeResult]
