from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
from typing import TYPE_CHECKING

from podcast_archiver import constants
from podcast_archiver.config import Settings
from podcast_archiver.database import get_database
from podcast_archiver.download import DownloadJob
from podcast_archiver.enums import DownloadResult, QueueCompletionType
from podcast_archiver.logging import logger, rprint
from podcast_archiver.models.feed import Feed, FeedInfo
from podcast_archiver.types import EpisodeResult, EpisodeResultsList, FutureEpisodeResult, ProcessingResult
from podcast_archiver.utils import FilenameFormatter, handle_feed_request
from podcast_archiver.utils.pretty_printing import PrettyPrintEpisodeRange

if TYPE_CHECKING:
    from pathlib import Path

    from podcast_archiver.database import BaseDatabase
    from podcast_archiver.models.episode import BaseEpisode


class FeedProcessor:
    settings: Settings
    database: BaseDatabase
    filename_formatter: FilenameFormatter

    pool_executor: ThreadPoolExecutor
    stop_event: Event

    known_feeds: dict[str, FeedInfo]

    __slots__ = ("settings", "database", "filename_formatter", "pool_executor", "stop_event", "known_feeds")

    def __init__(self, settings: Settings | None = None, database: BaseDatabase | None = None) -> None:
        self.settings = settings or Settings()
        database_path = self.settings.database or (self.settings.config.parent if self.settings.config else None)
        self.database = database or get_database(database_path, ignore_existing=self.settings.ignore_database)
        self.filename_formatter = FilenameFormatter(self.settings)
        self.pool_executor = ThreadPoolExecutor(max_workers=self.settings.concurrency)
        self.stop_event = Event()
        self.known_feeds = {}

    def process(self, url: str) -> ProcessingResult:
        if not (feed := self.load_feed(url, known_feeds=self.known_feeds)):
            return ProcessingResult(feed=None, tombstone=QueueCompletionType.FAILED)

        result = self.process_feed(feed=feed)
        rprint(f"[completed]{result.tombstone}[/]")
        return result

    def load_feed(self, url: str, known_feeds: dict[str, FeedInfo]) -> Feed | None:
        with handle_feed_request(url):
            feed = Feed(url=url, known_info=known_feeds.get(url))
            known_feeds[feed.url] = feed.info
            return feed

    def _does_already_exist(self, episode: BaseEpisode, *, target: Path) -> bool:
        if not (existing := self.database.exists(episode)):
            # NOTE on backwards-compatibility: if the episode is not in the DB we'd normally
            # download it again outright. This might cause a complete replacement of
            # episodes on disk for existing users who either used pre-v1.4 until now or
            # always have `ignore_database` enabled.
            #
            # To avoid that, we fall back to the on-disk check if the episode is not in
            # the DB (or ignored via `ignore_database`). Only if the episode is indeed
            # in the DB, we do the additional checks to possibly re-download an episode
            # if it was republished/changed.
            if target.exists():
                logger.debug("Episode '%s': not in db but on disk", episode)
                return True
            logger.debug("Episode '%s': not in db", episode)
            return False

        if existing.length and episode.enclosure.length and existing.length != episode.enclosure.length:
            logger.debug(
                "Episode '%s': length differs in feed: %s (%s in db)",
                episode,
                episode.enclosure.length,
                existing.length,
            )
            return False

        if existing.published_time and episode.published_time and episode.published_time > existing.published_time:
            logger.debug(
                "Episode '%s': is newer in feed: %s (by %s sec)",
                episode,
                episode.published_time,
                (episode.published_time - existing.published_time).total_seconds(),
            )
            return False

        logger.debug("Episode '%s': already in database.", episode)
        return True

    def process_feed(self, feed: Feed) -> ProcessingResult:
        rprint(f"\n[bold bright_magenta]Archiving: {feed}[/]\n")
        tombstone = QueueCompletionType.COMPLETED
        results: EpisodeResultsList = []
        with PrettyPrintEpisodeRange() as pretty_range:
            for idx, episode in enumerate(feed.episodes, 1):
                if episode is None:
                    logger.debug("Skipping invalid episode at idx %s", idx)
                    continue
                enqueued = self._enqueue_episode(episode, feed.info)
                pretty_range.update(isinstance(enqueued, EpisodeResult), episode)
                results.append(enqueued)

                if (max_count := self.settings.maximum_episode_count) and idx == max_count:
                    logger.debug("Reached requested maximum episode count of %s", max_count)
                    tombstone = QueueCompletionType.MAX_EPISODES
                    break

        success, failures = self._handle_results(results)
        return ProcessingResult(feed=feed, success=success, failures=failures, tombstone=tombstone)

    def _enqueue_episode(self, episode: BaseEpisode, feed_info: FeedInfo) -> FutureEpisodeResult | EpisodeResult:
        target = self.filename_formatter.format(episode=episode, feed_info=feed_info)
        if self._does_already_exist(episode, target=target):
            result = DownloadResult.ALREADY_EXISTS
            return EpisodeResult(episode, result)

        logger.debug("Queueing download for %r", episode)
        return self.pool_executor.submit(
            DownloadJob(
                episode,
                target=target,
                max_download_bytes=constants.DEBUG_PARTIAL_SIZE if self.settings.debug_partial else None,
                add_info_json=self.settings.write_info_json,
                stop_event=self.stop_event,
            )
        )

    def _handle_results(self, episode_results: EpisodeResultsList) -> tuple[int, int]:
        failures = success = 0
        for episode_result in episode_results:
            if isinstance(episode_result, Future):
                episode_result = episode_result.result()

            if episode_result.result not in DownloadResult.successful():
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
