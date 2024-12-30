from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Event
from typing import IO, TYPE_CHECKING, Generator

from podcast_archiver import constants
from podcast_archiver.enums import DownloadResult
from podcast_archiver.exceptions import NotCompleted
from podcast_archiver.logging import logger
from podcast_archiver.session import session
from podcast_archiver.types import EpisodeResult
from podcast_archiver.utils import atomic_write
from podcast_archiver.utils.progress import progress_manager

if TYPE_CHECKING:
    from pathlib import Path

    from requests import Response

    from podcast_archiver.models.episode import BaseEpisode


@dataclass(slots=True)
class DownloadJob:
    episode: BaseEpisode
    target: Path
    add_info_json: bool = False
    stop_event: Event = field(default_factory=Event)
    max_download_bytes: int | None = None

    def __call__(self) -> EpisodeResult:
        try:
            self.run()
            result = DownloadResult.COMPLETED_SUCCESSFULLY
        except NotCompleted:
            result = DownloadResult.ABORTED
        except Exception as exc:
            logger.error("Download failed: %s; %s", self.episode, exc)
            logger.debug("Exception while downloading", exc_info=exc)
            result = DownloadResult.FAILED

        return EpisodeResult(self.episode, result)

    def run(self) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading: %s", self.episode)
        response = session.get_and_raise(self.episode.enclosure.href, stream=True)
        with self.write_info_json(), atomic_write(self.target, mode="wb") as fp:
            self.receive_data(fp, response)
        logger.info("Completed: %s", self.episode)

    @property
    def infojsonfile(self) -> Path:
        return self.target.with_suffix(".info.json")

    def receive_data(self, fp: IO[bytes], response: Response) -> None:
        total_size = int(response.headers.get("content-length", "0"))
        total_written = 0
        max_bytes = self.max_download_bytes
        for chunk in progress_manager.track(
            response.iter_content(chunk_size=constants.DOWNLOAD_CHUNK_SIZE),
            episode=self.episode,
            total=total_size,
        ):
            total_written += fp.write(chunk)

            if max_bytes and total_written >= max_bytes:
                fp.truncate(max_bytes)
                logger.debug("Partial download of first %s bytes completed.", max_bytes)
                return

            if self.stop_event.is_set():
                logger.debug("Stop event is set, bailing on %s.", self.episode)
                raise NotCompleted

    @contextmanager
    def write_info_json(self) -> Generator[None, None, None]:
        if not self.add_info_json:
            yield
            return
        with atomic_write(self.infojsonfile) as fp:
            fp.write(self.episode.model_dump_json(indent=2) + "\n")
            yield
        logger.debug("Wrote episode metadata to %s", self.infojsonfile.name)
