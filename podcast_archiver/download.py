from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from threading import Event
from typing import IO, TYPE_CHECKING, Generator

from podcast_archiver import constants
from podcast_archiver.enums import JobResult
from podcast_archiver.exceptions import NotCompleted
from podcast_archiver.logging import logger, out
from podcast_archiver.session import session
from podcast_archiver.utils import atomic_write

if TYPE_CHECKING:
    from pathlib import Path

    from requests import Response

    from podcast_archiver.models import Episode, FeedInfo


stop_event = Event()


@dataclass
class JobResultCtx:
    episode: Episode
    job_result: JobResult

    def result(self, timeout: float | None = None) -> JobResultCtx:
        # Shortcut for non-future results produced by pre-flight check
        return self


class DownloadJob:
    episode: Episode
    feed_info: FeedInfo
    target: Path

    _max_download_bytes: int | None = None
    _write_info_json: bool

    def __init__(
        self,
        episode: Episode,
        *,
        target: Path,
        max_download_bytes: int | None = None,
        write_info_json: bool = False,
    ) -> None:
        self.episode = episode
        self.target = target
        self._max_download_bytes = max_download_bytes
        self._write_info_json = write_info_json

    def __call__(self) -> JobResultCtx:
        try:
            return JobResultCtx(self.episode, self.run())
        except NotCompleted:
            logger.debug("Download aborted: %s", self.episode)
            return JobResultCtx(self.episode, JobResult.ABORTED)
        except Exception as exc:
            logger.error("Download failed: %s; %s", self.episode, exc)
            logger.debug("Exception while downloading", exc_info=exc)
            return JobResultCtx(self.episode, JobResult.FAILED)

    def run(self) -> JobResult:
        if self.target.exists():
            return JobResult.ALREADY_EXISTS_DISK

        self.target.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading: %s", self.episode)
        response = session.get_and_raise(self.episode.enclosure.href, stream=True)
        with self.write_info_json(), atomic_write(self.target, mode="wb") as fp:
            self.receive_data(fp, response)

        logger.info("Completed: %s", self.episode)
        return JobResult.COMPLETED_SUCCESSFULLY

    @property
    def infojsonfile(self) -> Path:
        return self.target.with_suffix(".info.json")

    def receive_data(self, fp: IO[bytes], response: Response) -> None:
        total_size = int(response.headers.get("content-length", "0"))
        total_written = 0
        max_bytes = self._max_download_bytes
        for chunk in out.progress_bar(
            response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE),
            desc=str(self.episode),
            total=total_size,
        ):
            total_written += fp.write(chunk)

            if max_bytes and total_written >= max_bytes:
                fp.truncate(max_bytes)
                logger.debug("Partial download of first %s bytes completed.", max_bytes)
                return

            if stop_event.is_set():
                raise NotCompleted

    @contextmanager
    def write_info_json(self) -> Generator[None, None, None]:
        if not self._write_info_json:
            yield
            return
        with atomic_write(self.infojsonfile) as fp:
            fp.write(self.episode.model_dump_json(indent=2) + "\n")
            yield
        logger.debug("Wrote episode metadata to %s", self.infojsonfile.name)
