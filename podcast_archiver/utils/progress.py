from __future__ import annotations

from functools import partial
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING, Any, Iterable

from rich import progress as rp
from rich.table import Column

from podcast_archiver.console import console
from podcast_archiver.enums import RESULT_MAX_LEN
from podcast_archiver.logging import REDIRECT_VIA_LOGGING

if TYPE_CHECKING:
    from rich.console import RenderableType

    from podcast_archiver.models.episode import BaseEpisode


_Column = partial(
    Column,
    no_wrap=True,
    overflow="crop",
)


PROGRESS_COLUMNS: list[rp.ProgressColumn] = [
    rp.SpinnerColumn(
        table_column=_Column(width=2, min_width=2, max_width=2),
    ),
    rp.TimeRemainingColumn(
        compact=True,
        table_column=_Column(
            width=RESULT_MAX_LEN,
            min_width=RESULT_MAX_LEN,
            max_width=RESULT_MAX_LEN,
            justify="center",
        ),
    ),
    rp.BarColumn(
        bar_width=16,
        table_column=_Column(
            width=16,
            min_width=16,
            max_width=16,
        ),
    ),
    rp.TaskProgressColumn(
        justify="right",
        text_format="{task.percentage:2.0f}%",
        style="progress.percentage",
        table_column=_Column(
            width=5,
            min_width=5,
            max_width=5,
            justify="right",
        ),
    ),
    rp.TransferSpeedColumn(
        table_column=_Column(
            width=10,
            min_width=8,
            max_width=10,
            justify="right",
        ),
    ),
]


class EpisodeColumn(rp.RenderableColumn):
    def render(self, task: rp.Task) -> RenderableType:
        return task.fields["episode"]


def make_episode_column(cols: list[rp.ProgressColumn], idx: int = 2) -> None:
    others_width = 0
    for col in cols:
        tabcol = col.get_table_column()
        others_width += tabcol.width or tabcol.min_width or 0

    col = EpisodeColumn(
        table_column=_Column(
            overflow="ellipsis",
            min_width=8,
            max_width=max(console.width - others_width, 8),
        ),
    )
    PROGRESS_COLUMNS.insert(idx, col)


make_episode_column(PROGRESS_COLUMNS)


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

    def __enter__(self) -> ProgressManager:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()

    def track(self, iterable: Iterable[bytes], total: int, episode: BaseEpisode) -> Iterable[bytes]:
        if REDIRECT_VIA_LOGGING:
            yield from iterable
            return

        task_id = self._progress.add_task("downloading", total=total, episode=episode)
        try:
            for it in iterable:
                yield it
                self._progress.advance(task_id, advance=len(it))
        finally:
            self._progress.remove_task(task_id)
            self._progress.refresh()

    def start(self) -> None:
        if REDIRECT_VIA_LOGGING:
            return
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
