from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING

from podcast_archiver import constants
from podcast_archiver.config import Settings
from podcast_archiver.download import DownloadJob
from podcast_archiver.enums import DownloadResult, QueueCompletionType
from podcast_archiver.logging import logger, rprint
from podcast_archiver.models import Episode, Feed, FeedInfo
from podcast_archiver.types import EpisodeResult, EpisodeResultsList, FutureEpisodeResult
from podcast_archiver.utils import FilenameFormatter, handle_feed_request

if TYPE_CHECKING:
    from pathlib import Path

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

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.filename_formatter = FilenameFormatter(self.settings)
        self.database = self.settings.get_database()
        self.pool_executor = ThreadPoolExecutor(max_workers=self.settings.concurrency)
        self.stop_event = Event()
        self.known_feeds = {}

    def process(self, url: str) -> ProcessingResult:
        if not (feed := self.load_feed(url, known_feeds=self.known_feeds)):
            return ProcessingResult()

        result, tombstone = self.process_feed(feed=feed)

        rprint(f"\n[bar.finished]✔ {tombstone} for: {feed}[/]")
        return result

    def load_feed(self, url: str, known_feeds: dict[str, FeedInfo]) -> Feed | None:
        with handle_feed_request(url):
            feed = Feed(url=url, known_info=known_feeds.get(url))
            known_feeds[feed.url] = feed.info
            return feed

    def _preflight_check(self, episode: Episode, target: Path) -> DownloadResult | None:
        if self.database.exists(episode):
            logger.debug("Pre-flight check on episode '%s': already in database.", episode)
            return DownloadResult.ALREADY_EXISTS

        if target.exists():
            logger.debug("Pre-flight check on episode '%s': already on disk.", episode)
            return DownloadResult.ALREADY_EXISTS

        return None

    def process_feed(self, feed: Feed) -> tuple[ProcessingResult, QueueCompletionType]:
        rprint(f"\n[bold bright_magenta]Downloading archive for: {feed}[/]\n")
        tombstone = QueueCompletionType.COMPLETED
        results: EpisodeResultsList = []
        for idx, episode in enumerate(feed.episode_iter(self.settings.maximum_episode_count), 1):
            if (enqueued := self._enqueue_episode(episode, feed.info)) is None:
                tombstone = QueueCompletionType.FOUND_EXISTING
                break
            results.append(enqueued)
            if (max_count := self.settings.maximum_episode_count) and idx == max_count:
                logger.debug("Reached requested maximum episode count of %s", max_count)
                tombstone = QueueCompletionType.MAX_EPISODES
                break

        success, failures = self._handle_results(results)
        return ProcessingResult(feed=feed, success=success, failures=failures), tombstone

    def _enqueue_episode(self, episode: Episode, feed_info: FeedInfo) -> FutureEpisodeResult | None:
        target = self.filename_formatter.format(episode=episode, feed_info=feed_info)
        if result := self._preflight_check(episode, target):
            rprint(f"[bar.finished]✔ {result}: {episode}[/]")
            if self.settings.update_archive:
                logger.debug("Up to date with %r", episode)
                return None
            return EpisodeResult(episode, result)

        logger.debug("Queueing download for %r", episode)
        return self.pool_executor.submit(
            DownloadJob(
                episode,
                target=target,
                max_download_bytes=constants.DEBUG_PARTIAL_SIZE if self.settings.debug_partial else None,
                write_info_json=self.settings.write_info_json,
                stop_event=self.stop_event,
            )
        )

    def _handle_results(self, episode_results: EpisodeResultsList) -> tuple[int, int]:
        failures = success = 0
        for episode_result in episode_results:
            if not isinstance(episode_result, EpisodeResult):
                try:
                    episode_result = episode_result.result()
                except Exception as exc:
                    logger.debug("Got exception from future %s", episode_result, exc_info=exc)
                    continue

            if episode_result.result not in (DownloadResult.COMPLETED_SUCCESSFULLY, DownloadResult.ALREADY_EXISTS):
                failures += 1
                continue

            self.database.add(episode_result.episode)
            success += 1
        return success, failures

    def shutdown(self) -> None:
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.pool_executor.shutdown(cancel_futures=True)

            logger.debug("Completed processor shutdown")
