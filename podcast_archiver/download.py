from __future__ import annotations

from threading import Event
from typing import IO, TYPE_CHECKING, Any

from podcast_archiver import constants
from podcast_archiver.enums import DownloadResult
from podcast_archiver.logging import logger
from podcast_archiver.session import session
from podcast_archiver.utils import atomic_write

if TYPE_CHECKING:
    from pathlib import Path

    from requests import Response
    from rich import progress as rich_progress

    from podcast_archiver.config import Settings
    from podcast_archiver.models import Episode, FeedInfo


class DownloadJob:
    episode: Episode
    feed_info: FeedInfo
    settings: Settings
    target: Path
    stop_event: Event

    _debug_partial: bool
    _write_info_json: bool

    _progress: rich_progress.Progress | None = None
    _task_id: rich_progress.TaskID | None = None

    def __init__(
        self,
        episode: Episode,
        *,
        target: Path,
        feed_info: FeedInfo,
        debug_partial: bool = False,
        write_info_json: bool = False,
        progress: rich_progress.Progress | None = None,
        stop_event: Event | None = None,
    ) -> None:
        self.episode = episode
        self.target = target
        self.feed_info = feed_info
        self._debug_partial = debug_partial
        self._write_info_json = write_info_json
        self._progress = progress
        self.stop_event = stop_event or Event()

        self.init_progress()

    def __repr__(self) -> str:
        return f"EpisodeDownload({self})"

    def __str__(self) -> str:
        return str(self.episode)

    def __call__(self) -> DownloadResult:
        try:
            return self.run()
        except Exception as exc:
            logger.error("Download failed", exc_info=exc)
            return DownloadResult.FAILED

    def run(self) -> DownloadResult:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.write_info_json()
        if result := self.preflight_check():
            return result

        response = session.get(
            self.episode.enclosure.url,
            stream=True,
            allow_redirects=True,
            timeout=constants.REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", "0"))
        self.update_progress(total=total_size)

        with atomic_write(self.target, mode="wb") as fp:
            receive_complete = self.receive_data(fp, response)

        if not receive_complete:
            self.target.unlink(missing_ok=True)
            return DownloadResult.ABORTED

        logger.info("Completed download of %s", self.target)
        return DownloadResult.COMPLETED_SUCCESSFULLY

    @property
    def infojsonfile(self) -> Path:
        return self.target.with_suffix(".info.json")

    def init_progress(self) -> None:
        if self._progress is None:
            return

        self._task_id = self._progress.add_task(
            description=self.episode.title,
            date=self.episode.published_time,
            total=self.episode.enclosure.length,
            visible=False,
        )

    def update_progress(self, visible: bool = True, **kwargs: Any) -> None:
        if self._task_id is None:
            return
        assert self._progress
        self._progress.update(self._task_id, visible=visible, **kwargs)

    def preflight_check(self) -> DownloadResult | None:
        if self.target_exists:
            logger.debug("Pre-flight check on episode '%s': already exists.", self.episode.title)
            size = self.target.stat().st_size
            self.update_progress(total=size, completed=size)
            return DownloadResult.ALREADY_EXISTS

        return None

    def receive_data(self, fp: IO[str], response: Response) -> bool:
        total_written = 0
        for chunk in response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE):
            total_written += fp.write(chunk)
            self.update_progress(completed=total_written)

            if self._debug_partial and total_written >= constants.DEBUG_PARTIAL_SIZE:
                logger.debug("Partial download completed.")
                return True
            if self.stop_event.is_set():
                logger.debug("Stop event is set, bailing.")
                return False

        return True

    def write_info_json(self) -> None:
        if not self._write_info_json:
            return
        logger.info("Writing episode metadata to %s", self.infojsonfile.name)
        with atomic_write(self.infojsonfile) as fp:
            fp.write(self.episode.model_dump_json(indent=2) + "\n")

    @property
    def target_exists(self) -> bool:
        return self.target.exists()
