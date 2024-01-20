from __future__ import annotations

import shutil
from functools import cached_property
from pathlib import Path
from threading import Event
from typing import Any

from requests import Response
from rich import progress as rich_progress

from podcast_archiver import constants
from podcast_archiver.config import DEFAULT_SETTINGS, Settings
from podcast_archiver.enums import DownloadResult
from podcast_archiver.logging import logger
from podcast_archiver.models import Episode, FeedInfo
from podcast_archiver.session import session


class DownloadJob:
    episode: Episode
    feed_info: FeedInfo
    settings: Settings
    target: Path
    stop_event: Event

    _progress: rich_progress.Progress | None = None
    _task_id: rich_progress.TaskID | None = None

    def __init__(
        self,
        episode: Episode,
        *,
        feed_info: FeedInfo,
        settings: Settings = DEFAULT_SETTINGS,
        progress: rich_progress.Progress | None = None,
        stop_event: Event | None = None,
    ) -> None:
        self.episode = episode
        self.feed_info = feed_info
        self.settings = settings
        self._progress = progress
        self.target = self.settings.filename_formatter.format(episode=self.episode, feed_info=self.feed_info)
        if settings.debug_partial:
            self.target = self.target.with_suffix(".partial" + self.target.suffix)
        self.stop_event = stop_event or Event()

        self.init_progress()

    def __repr__(self) -> str:
        return f"EpisodeDownload({self})"

    def __str__(self) -> str:
        return str(self.episode)

    def __call__(self) -> DownloadResult:
        try:
            if result := self.preflight_check():
                return result

            response = session.get(
                self.episode.media_link.url,
                stream=True,
                allow_redirects=True,
                timeout=constants.REQUESTS_TIMEOUT,
            )
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", "0"))
            self.update_progress(total=total_size, visible=True)

            self.target.parent.mkdir(parents=True, exist_ok=True)
            if not self.receive_data(self.tempfile, response):
                return DownloadResult.ABORTED

            logger.debug("Moving file %s => %s", self.tempfile, self.target)
            shutil.move(self.tempfile, self.target)

            logger.info("Completed download of %s", self.target)
            return DownloadResult.COMPLETED_SUCCESSFULLY
        except Exception as exc:
            logger.error("Download failed", exc_info=exc)
            return DownloadResult.FAILED
        finally:
            self.tempfile.unlink(missing_ok=True)

    @cached_property
    def tempfile(self) -> Path:
        return self.target.with_suffix(self.target.suffix + ".part")

    def init_progress(self) -> None:
        if not self._progress:
            return

        self._task_id = self._progress.add_task(
            description=self.episode.title,
            date=self.episode.published_time,
            total=self.episode.media_link.length,
            visible=False,
        )

    def update_progress(self, visible: bool = True, **kwargs: Any) -> None:
        if not self._progress or not self._task_id:
            return
        self._progress.update(self._task_id, visible=visible, **kwargs)

    def preflight_check(self) -> DownloadResult | None:
        if self.target_exists:
            size = self.target.stat().st_size
            self.update_progress(total=size, completed=size, visible=True)
            return DownloadResult.ALREADY_EXISTS

        return None

    def receive_data(self, filename: Path, response: Response) -> bool:
        total_written = 0
        with filename.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE):
                total_written += fp.write(chunk)
                self.update_progress(completed=total_written)

                if self.settings.debug_partial and total_written >= constants.DEBUG_PARTIAL_SIZE:
                    logger.debug("Partial download completed.")
                    return True
                if self.stop_event.is_set():
                    logger.debug("Stop event is set, bailing.")
                    return False

        return True

    @property
    def target_exists(self) -> bool:
        return self.target.exists()
