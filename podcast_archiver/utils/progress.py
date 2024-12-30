from __future__ import annotations

from functools import partial
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING, Iterable

from rich import progress as rp
from rich.table import Column

from podcast_archiver.console import console
from podcast_archiver.logging import REDIRECT_VIA_LOGGING

if TYPE_CHECKING:
    from rich.console import RenderableType

    from podcast_archiver.models.episode import BaseEpisode


class EpisodeColumn(rp.RenderableColumn):
    def render(self, task: rp.Task) -> RenderableType:
        return task.fields["episode"]


_Column = partial(
    Column,
    no_wrap=True,
    overflow="ignore",
    highlight=False,
)

PROGRESS_COLUMNS: tuple[rp.ProgressColumn, ...] = (
    rp.SpinnerColumn(
        table_column=_Column(width=4),
    ),
    rp.TimeRemainingColumn(
        compact=True,
        table_column=_Column(width=11, justify="center"),
    ),
    EpisodeColumn(
        table_column=_Column(
            overflow="ellipsis",
            min_width=40,
        ),
    ),
    rp.BarColumn(
        bar_width=20,
        table_column=_Column(width=20),
    ),
    rp.TaskProgressColumn(
        table_column=_Column(width=5),
    ),
    rp.TransferSpeedColumn(
        table_column=_Column(width=10),
    ),
)


_widths = sum(col.get_table_column().width or 0 for col in [*PROGRESS_COLUMNS[:1], *PROGRESS_COLUMNS[3:]])
description_col = PROGRESS_COLUMNS[2].get_table_column()
description_col.width = max(console.width - _widths, description_col.min_width or 0)


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

    def track(self, iterable: Iterable[bytes], total: int, episode: BaseEpisode) -> Iterable[bytes]:
        if REDIRECT_VIA_LOGGING:
            yield from iterable
            return

        self.start()
        task_id = self._progress.add_task("downloading", total=total, episode=episode)
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
            console.show_cursor(False)
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._progress.stop()
            self._refresher.stop()
            console.show_cursor(True)
            self._started = False


progress_manager = ProgressManager()
