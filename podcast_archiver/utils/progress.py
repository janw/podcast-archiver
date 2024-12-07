from __future__ import annotations

from threading import Event, Lock, Thread
from typing import Iterable

from rich import progress as rp

from podcast_archiver.console import console
from podcast_archiver.logging import REDIRECT_VIA_LOGGING

PROGRESS_COLUMNS: tuple[rp.ProgressColumn, ...] = (
    rp.SpinnerColumn(finished_text="[success]✔[/]"),
    rp.TextColumn("{task.description}"),
    rp.BarColumn(bar_width=25),
    rp.TaskProgressColumn(),
    rp.TimeRemainingColumn(),
    rp.DownloadColumn(),
    rp.TransferSpeedColumn(),
)


class _ProgressRefreshThread(Thread):
    progress: rp.Progress
    stop_event: Event

    __slots__ = ("progress", "stop_event")

    def __init__(self, progress_obj: rp.Progress) -> None:
        self.progress = progress_obj
        self.stop_event = Event()
        super().__init__(daemon=True)

    def run(self) -> None:
        update_period = 1 / self.progress.live.refresh_per_second
        wait = self.stop_event.wait
        while not wait(update_period) and self.progress.live.is_started:
            self.progress.refresh()

    def stop(self) -> None:
        self.stop_event.set()
        self.join()


class ProgressManager:
    _progress: rp.Progress
    _lock: Lock
    _refresher: _ProgressRefreshThread
    _started: bool

    __slots__ = ("_progress", "_lock", "_refresher", "_started")

    def __init__(self) -> None:
        self._started = False
        self._lock = Lock()
        self._progress = rp.Progress(
            *PROGRESS_COLUMNS,
            console=console,
            transient=True,
            auto_refresh=False,
            redirect_stdout=False,
            refresh_per_second=8,
        )

    def track(self, iterable: Iterable[bytes], description: str, total: int) -> Iterable[bytes]:
        if REDIRECT_VIA_LOGGING:
            yield from iterable
            return

        self.start()
        task_id = self._progress.add_task(description=description, total=total)
        try:
            for it in iterable:
                yield it
                self._progress.advance(task_id, advance=len(it))
        finally:
            self._progress.remove_task(task_id)
            self._progress.refresh()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._progress.start()
            self._refresher = _ProgressRefreshThread(self._progress)
            self._refresher.start()
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._progress.stop()
            self._started = False
            self._refresher.stop()


progress_manager = ProgressManager()
