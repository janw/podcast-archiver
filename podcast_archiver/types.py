from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias

from rich.console import Group

if TYPE_CHECKING:
    from rich.console import RenderableType

    from podcast_archiver.enums import DownloadResult, QueueCompletionType
    from podcast_archiver.models.episode import BaseEpisode
    from podcast_archiver.models.feed import Feed


@dataclass(slots=True, frozen=True)
class EpisodeResult:
    episode: BaseEpisode
    result: DownloadResult
    is_eager: bool = False

    def __rich__(self) -> RenderableType:
        return Group(self.result, self.episode)


@dataclass(slots=True, frozen=True)
class ProcessingResult:
    feed: Feed | None
    tombstone: QueueCompletionType
    success: int = 0
    failures: int = 0

    def __rich__(self) -> RenderableType:
        return self.tombstone


class ProgressCallback(Protocol):
    def __call__(self, total: int | None = None, completed: int | None = None) -> None: ...


FutureEpisodeResult: TypeAlias = Future[EpisodeResult] | EpisodeResult
EpisodeResultsList: TypeAlias = list[FutureEpisodeResult]
