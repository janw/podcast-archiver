from __future__ import annotations

from threading import Event
from typing import IO, TYPE_CHECKING

from podcast_archiver import constants
from podcast_archiver.console import noop_callback
from podcast_archiver.enums import DownloadResult
from podcast_archiver.logging import logger
from podcast_archiver.session import session
from podcast_archiver.types import EpisodeResult, ProgressCallback
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
        debug_partial: bool = False,
        write_info_json: bool = False,
        progress_callback: ProgressCallback = noop_callback,
        stop_event: Event | None = None,
    ) -> None:
        self.episode = episode
        self.target = target
        self._debug_partial = debug_partial
        self._write_info_json = write_info_json
        self.progress_callback = progress_callback
        self.stop_event = stop_event or Event()

    def __repr__(self) -> str:
        return f"EpisodeDownload({self})"

    def __str__(self) -> str:
        return str(self.episode)

    def __call__(self) -> EpisodeResult:
        try:
            return self.run()
        except Exception as exc:
            logger.error("Download failed", exc_info=exc)
            return EpisodeResult(self.episode, DownloadResult.FAILED)

    def run(self) -> EpisodeResult:
        if self.target.exists():
            return EpisodeResult(self.episode, DownloadResult.ALREADY_EXISTS)

        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.write_info_json()

        response = session.get(
            self.episode.enclosure.url,
            stream=True,
            allow_redirects=True,
            timeout=constants.REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", "0"))
        self.progress_callback(total=total_size)

        with atomic_write(self.target, mode="wb") as fp:
            receive_complete = self.receive_data(fp, response)

        if not receive_complete:
            self.target.unlink(missing_ok=True)
            return EpisodeResult(self.episode, DownloadResult.ABORTED)

        logger.info("Completed download of %s", self.target)
        return EpisodeResult(self.episode, DownloadResult.COMPLETED_SUCCESSFULLY)

    @property
    def infojsonfile(self) -> Path:
        return self.target.with_suffix(".info.json")

    def receive_data(self, fp: IO[str], response: Response) -> bool:
        total_written = 0
        for chunk in response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE):
            total_written += fp.write(chunk)
            self.progress_callback(completed=total_written)

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
