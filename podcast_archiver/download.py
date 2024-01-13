from __future__ import annotations

import shutil
from pathlib import Path
from threading import Event

from requests import Response
from rich import progress as rich_progress

from podcast_archiver import constants
from podcast_archiver.config import Settings
from podcast_archiver.logging import logger
from podcast_archiver.models import Episode, FeedInfo
from podcast_archiver.session import session


class DownloadJob:
    episode: Episode
    settings: Settings
    progress: rich_progress.Progress
    target: Path
    stop_event: Event
    task_id: rich_progress.TaskID

    def __init__(
        self,
        episode: Episode,
        *,
        feed_info: FeedInfo,
        settings: Settings,
        progress: rich_progress.Progress,
        stop_event: Event | None = None,
    ) -> None:
        self.episode = episode
        self.settings = settings
        self.progress = progress
        self.target = self.settings.filename_formatter.format(episode=self.episode, feed_info=feed_info)
        if settings.debug_partial:
            self.target = self.target.with_suffix(".partial" + self.target.suffix)
        self.stop_event = stop_event or Event()
        self.task_id = self.progress.add_task(
            description=self.episode.title,
            date=self.episode.published_time,
            total=self.episode.media_link.length,
            visible=False,
        )

    def __repr__(self) -> str:
        return f"EpisodeDownload({self})"

    def __str__(self) -> str:
        return str(self.episode)

    def __call__(self) -> DownloadJob:
        if not self.preflight_check():
            return self

        response = session.get(
            self.episode.media_link.url,
            stream=True,
            allow_redirects=True,
            timeout=constants.REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", "0"))
        self.progress.update(self.task_id, total=total_size, visible=True)

        self.target.parent.mkdir(parents=True, exist_ok=True)
        tempfile = self.target.with_suffix(self.target.suffix + ".part")
        self.receive_data(tempfile, response)

        logger.debug("Moving file %s => %s", tempfile, self.target)
        shutil.move(tempfile, self.target)

        logger.info("Completed download of %s", self.target)
        return self

    def preflight_check(self) -> bool:
        if self.target_exists:
            size = self.target.stat().st_size
            self.progress.update(self.task_id, total=size, completed=size, visible=True)
            return False

        return True

    def receive_data(self, filename: Path, response: Response) -> None:
        total_written = 0
        with filename.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE):
                total_written += fp.write(chunk)
                self.progress.update(self.task_id, completed=total_written)

                if self.settings.debug_partial and total_written >= constants.DEBUG_PARTIAL_SIZE:
                    logger.debug("Partial download completed.")
                    break
                if self.stop_event.is_set():
                    logger.debug("Stop event is set, bailing.")
                    break

        if self.stop_event.is_set():
            filename.unlink()

    @property
    def target_exists(self) -> bool:
        return self.target.exists()
