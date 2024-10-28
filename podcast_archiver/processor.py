from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from podcast_archiver import constants
from podcast_archiver.download import DownloadJob, JobResultCtx, stop_event
from podcast_archiver.enums import JobResult
from podcast_archiver.exceptions import MaxEpisodes
from podcast_archiver.logging import logger, out
from podcast_archiver.models import Episode, Feed, FeedInfo
from podcast_archiver.utils import FilenameFormatter, handle_feed_request
from podcast_archiver.utils.pretty_printing import PrettyPrintRange

if TYPE_CHECKING:
    from concurrent.futures import Future
    from pathlib import Path

    from podcast_archiver.config import Settings
    from podcast_archiver.database import BaseDatabase
    from podcast_archiver.models import FeedInfo

    JobResultCtxsList: TypeAlias = list[Future["JobResultCtx"] | "JobResultCtx"]


@dataclass
class ProcessingResult:
    feed: Feed | None = None
    success: int = 0
    failures: int = 0
    failed_url: str | None = None


class FeedProcessor:
    settings: Settings
    database: BaseDatabase
    filename_formatter: FilenameFormatter

    pool_executor: ThreadPoolExecutor

    known_feeds: dict[str, FeedInfo]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.filename_formatter = FilenameFormatter(settings)
        self.pool_executor = ThreadPoolExecutor(max_workers=self.settings.concurrency)
        self.known_feeds = {}

    def process(self, url: str) -> bool:
        feed: Feed | None = None
        out.info(f"Retrieving feed from {url} ...")
        with handle_feed_request(url):
            feed = Feed(url=url, known_info=self.known_feeds.get(url))
        if not feed:
            return False

        out.header(f"Downloading episodes from: {feed}")
        self._process_episodes(feed)
        self.known_feeds[feed.url] = feed.info
        return True

    def _preflight_check(self, episode: Episode, target: Path) -> JobResult | None:
        if self.settings.database_obj.exists(episode):
            logger.debug("Pre-flight check on %s: already in database.", episode)
            return JobResult.ALREADY_EXISTS_DB

        if target.exists():
            logger.debug("Pre-flight check on %s: already on disk.", episode)
            return JobResult.ALREADY_EXISTS_DISK

        return None

    def _process_episodes(self, feed: Feed) -> None:
        results: JobResultCtxsList = []
        partial = False
        try:
            with PrettyPrintRange(Episode) as pretty_range:
                for episode in feed.episode_iter(self.settings.maximum_episode_count):
                    exists = self._process_episode(episode, feed.info, results)
                    pretty_range.update(exists, episode)
        except MaxEpisodes:
            partial = True

        self._handle_results(results)
        if partial:
            out.success(f"✔ Maximum episode count reached for: {feed}")
        else:
            out.success(f"✔ Archived episodes for: {feed}")

    def _process_episode(self, episode: Episode, feed_info: FeedInfo, results: JobResultCtxsList) -> bool:
        target = self.filename_formatter.format(episode=episode, feed_info=feed_info)
        if result := self._preflight_check(episode, target):
            results.append(JobResultCtx(episode, result))
            return True

        logger.debug("Queueing download for %r", episode)
        results.append(
            self.pool_executor.submit(
                DownloadJob(
                    episode,
                    target=target,
                    max_download_bytes=constants.DEBUG_PARTIAL_SIZE if self.settings.debug_partial else None,
                    write_info_json=self.settings.write_info_json,
                )
            )
        )
        return False

    def _handle_results(self, results: JobResultCtxsList) -> None:
        for result in results:
            try:
                result = result.result()
                logger.debug("Got future result %s", result)
            except Exception:
                continue
            if result.job_result != JobResult.ALREADY_EXISTS_DB:
                self.settings.database_obj.add(result.episode)

    def shutdown(self) -> None:
        if not stop_event.is_set():
            stop_event.set()
            out.info("Terminating.")
            self.pool_executor.shutdown(cancel_futures=True)

            logger.debug("Completed processor shutdown")
