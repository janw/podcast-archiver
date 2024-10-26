from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING

from podcast_archiver import constants
from podcast_archiver.download import DownloadJob
from podcast_archiver.enums import DownloadResult, QueueCompletionType
from podcast_archiver.logging import logger, rprint
from podcast_archiver.models import Episode, Feed, FeedInfo
from podcast_archiver.types import EpisodeResult, EpisodeResultsList
from podcast_archiver.utils import FilenameFormatter, handle_feed_request

if TYPE_CHECKING:
    from pathlib import Path

    from podcast_archiver.config import Settings
    from podcast_archiver.database import BaseDatabase


@dataclass
class ProcessingResult:
    feed: Feed | None = None
    started: int = 0
    success: int = 0
    failures: int = 0


class FeedProcessor:
    settings: Settings
    database: BaseDatabase
    filename_formatter: FilenameFormatter

    pool_executor: ThreadPoolExecutor
    stop_event: Event

    known_feeds: dict[str, FeedInfo]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.filename_formatter = FilenameFormatter(settings)
        self.database = settings.get_database()
        self.pool_executor = ThreadPoolExecutor(max_workers=self.settings.concurrency)
        self.stop_event = Event()
        self.known_feeds = {}

    def process(self, url: str) -> ProcessingResult:
        result = ProcessingResult()
        with handle_feed_request(url):
            result.feed = Feed(url=url, known_info=self.known_feeds.get(url))

        if result.feed:
            rprint(f"\n[bold bright_magenta]Downloading archive for: {result.feed}[/]\n")
            episode_results, completion_msg = self._process_episodes(feed=result.feed)
            self._handle_results(episode_results, result=result)

            rprint(f"\n[bar.finished]✔ {completion_msg} for: {result.feed}[/]")
        return result

    def _preflight_check(self, episode: Episode, target: Path) -> DownloadResult | None:
        if self.database.exists(episode):
            logger.debug("Pre-flight check on episode '%s': already in database.", episode)
            return DownloadResult.ALREADY_EXISTS

        if target.exists():
            logger.debug("Pre-flight check on episode '%s': already on disk.", episode)
            return DownloadResult.ALREADY_EXISTS

        return None

    def _process_episodes(self, feed: Feed) -> tuple[EpisodeResultsList, QueueCompletionType]:
        results: EpisodeResultsList = []
        for idx, episode in enumerate(feed.episode_iter(self.settings.maximum_episode_count), 1):
            if completion := self._process_episode(episode, feed.info, results):
                return results, completion

            if (max_count := self.settings.maximum_episode_count) and idx == max_count:
                logger.debug("Reached requested maximum episode count of %s", max_count)
                return results, QueueCompletionType.MAX_EPISODES

        return results, QueueCompletionType.COMPLETED

    def _process_episode(
        self, episode: Episode, feed_info: FeedInfo, results: EpisodeResultsList
    ) -> QueueCompletionType | None:
        target = self.filename_formatter.format(episode=episode, feed_info=feed_info)
        if result := self._preflight_check(episode, target):
            rprint(f"[bar.finished]✔ {result}: {episode}[/]")
            results.append(EpisodeResult(episode, result))
            if self.settings.update_archive:
                logger.debug("Up to date with %r", episode)
                return QueueCompletionType.FOUND_EXISTING
            return None

        logger.debug("Queueing download for %r", episode)
        results.append(
            self.pool_executor.submit(
                DownloadJob(
                    episode,
                    target=target,
                    max_download_bytes=constants.DEBUG_PARTIAL_SIZE if self.settings.debug_partial else None,
                    write_info_json=self.settings.write_info_json,
                    stop_event=self.stop_event,
                )
            )
        )
        return None

    def _handle_results(self, episode_results: EpisodeResultsList, *, result: ProcessingResult) -> None:
        if not result.feed:
            return
        for episode_result in episode_results:
            if not isinstance(episode_result, EpisodeResult):
                try:
                    episode_result = episode_result.result()
                    logger.debug("Got future result %s", episode_result)
                except Exception:
                    result.failures += 1
                    continue
            self.database.add(episode_result.episode)
            result.success += 1
        self.known_feeds[result.feed.url] = result.feed.info

    def shutdown(self) -> None:
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.pool_executor.shutdown(cancel_futures=True)

            logger.debug("Completed processor shutdown")
