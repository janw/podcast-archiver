from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, ValidationError
from requests import HTTPError
from rich import progress as rich_progress

from podcast_archiver.console import console
from podcast_archiver.download import DownloadJob
from podcast_archiver.enums import DownloadResult, QueueCompletionType
from podcast_archiver.logging import logger
from podcast_archiver.models import Feed
from podcast_archiver.utils import FilenameFormatter

if TYPE_CHECKING:
    from podcast_archiver.config import Settings

PROGRESS_COLUMNS = (
    rich_progress.SpinnerColumn(finished_text="[bar.finished]✔[/]"),
    rich_progress.TextColumn("[blue]{task.fields[date]:%Y-%m-%d}"),
    rich_progress.TextColumn("[progress.description]{task.description}"),
    rich_progress.BarColumn(bar_width=25),
    rich_progress.TaskProgressColumn(),
    rich_progress.TimeRemainingColumn(),
    rich_progress.DownloadColumn(),
    rich_progress.TransferSpeedColumn(),
)


@dataclass
class ProcessingResult:
    feed: Feed | None = None
    started: int = 0
    success: int = 0
    failures: int = 0


class FeedProcessor:
    settings: Settings
    filename_formatter: FilenameFormatter

    pool_executor: ThreadPoolExecutor
    progress: rich_progress.Progress
    stop_event: Event

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.filename_formatter = FilenameFormatter(settings)
        self.pool_executor = ThreadPoolExecutor(max_workers=self.settings.concurrency)
        self.progress = rich_progress.Progress(
            *PROGRESS_COLUMNS,
            console=console,
            disable=settings.verbose > 1 or settings.quiet,
        )
        # self.progress.live.vertical_overflow = "visible"
        self.stop_event = Event()

    def process(self, url: AnyHttpUrl) -> ProcessingResult:
        result = ProcessingResult()
        try:
            feed = Feed.from_url(url)
        except HTTPError as exc:
            if exc.response is not None:
                console.print(f"[error]Received status code {exc.response.status_code} from {url}[/]")
            logger.error("Failed to request feed url %s", url, exc_info=exc)
            return result
        except ValidationError as exc:
            logger.exception("Invalid feed", exc_info=exc)
            console.print(f"[error]Received invalid feed from {url}[/]")
            return result

        result.feed = feed
        console.print(f"\n[bold bright_magenta]Downloading archive for: {feed.info.title}[/]\n")

        with self.progress:
            futures, completion_msg = self._process_episodes(feed=feed)
            self._handle_futures(futures, result=result)

        console.print(f"\n[bar.finished]✔ {completion_msg}[/]")
        return result

    def _process_episodes(self, feed: Feed) -> tuple[list[Future[DownloadResult]], QueueCompletionType]:
        futures: list[Future[DownloadResult]] = []
        for idx, episode in enumerate(feed.episode_iter(self.settings.maximum_episode_count), 1):
            target = self.filename_formatter.format(episode=episode, feed_info=feed.info)
            download_job = DownloadJob(
                episode,
                target=target,
                feed_info=feed.info,
                debug_partial=self.settings.debug_partial,
                write_info_json=self.settings.write_info_json,
                progress=self.progress,
                stop_event=self.stop_event,
            )
            if self.settings.update_archive and download_job.target_exists:
                logger.info("Up to date with %r", episode)
                return futures, QueueCompletionType.FOUND_EXISTING

            logger.info("Queueing download for %r", episode)
            futures.append(self.pool_executor.submit(download_job))
            if (max_count := self.settings.maximum_episode_count) and idx == max_count:
                logger.info("Reached requested maximum episode count of %s", max_count)
                return futures, QueueCompletionType.MAX_EPISODES

        return futures, QueueCompletionType.COMPLETED

    def _handle_futures(self, futures: list[Future[DownloadResult]], *, result: ProcessingResult) -> None:
        for future in futures:
            try:
                _result = future.result()
                logger.debug("Got future result %s", _result)
            except Exception:
                result.failures += 1
            else:
                result.success += 1

    def shutdown(self) -> None:
        self.stop_event.set()
        self.pool_executor.shutdown(cancel_futures=True)

        for task in self.progress.tasks or []:
            if not task.finished:
                task.visible = False
        self.progress.stop()

        logger.debug("Completed processor shutdown")
