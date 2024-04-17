from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich import progress
from rich.console import Console

if TYPE_CHECKING:
    from podcast_archiver.config import Settings
    from podcast_archiver.models import Episode
    from podcast_archiver.types import ProgressCallback

console = Console()


PROGRESS_COLUMNS = (
    progress.SpinnerColumn(finished_text="[bar.finished]✔[/]"),
    progress.TextColumn("[blue]{task.fields[date]:%Y-%m-%d}"),
    progress.TextColumn("[progress.description]{task.description}"),
    progress.BarColumn(bar_width=25),
    progress.TaskProgressColumn(),
    progress.TimeRemainingColumn(),
    progress.DownloadColumn(),
    progress.TransferSpeedColumn(),
)


def noop_callback(total: int | None = None, completed: int | None = None) -> None:
    pass


class ProgressDisplay:
    disabled: bool

    _progress: progress.Progress
    _state: dict[Episode, progress.TaskID]

    def __init__(self, settings: Settings) -> None:
        self.disabled = settings.verbose > 1 or settings.quiet
        self._progress = progress.Progress(
            *PROGRESS_COLUMNS,
            console=console,
            disable=self.disabled,
        )
        self._progress.live.vertical_overflow = "visible"
        self._state = {}

    def _get_task_id(self, episode: Episode) -> progress.TaskID:
        return self._state.get(episode, self.register(episode))

    def __enter__(self) -> ProgressDisplay:
        if not self.disabled:
            self._progress.start()
        return self

    def __exit__(self, *args: Any) -> None:
        if not self.disabled:
            self._progress.stop()
        self._state = {}

    def shutdown(self) -> None:
        for task in self._progress.tasks or []:
            if not task.finished:
                task.visible = False
        self._progress.stop()

    def register(self, episode: Episode) -> progress.TaskID:
        task_id = self._progress.add_task(
            description=episode.title,
            date=episode.published_time,
            total=episode.enclosure.length,
            visible=False,
        )
        self._state[episode] = task_id
        return task_id

    def update(self, episode: Episode, visible: bool = True, **kwargs: Any) -> None:
        if self.disabled:
            return

        task_id = self._get_task_id(episode)
        self._progress.update(task_id, visible=visible, **kwargs)

    def completed(self, episode: Episode, visible: bool = True, **kwargs: Any) -> None:
        if self.disabled:
            return

        task_id = self._get_task_id(episode)
        self._progress.update(task_id, visible=visible, completed=episode.enclosure.length, **kwargs)

    def get_callback(self, episode: Episode) -> ProgressCallback:
        if self.disabled:
            return noop_callback

        task_id = self._get_task_id(episode)

        def _callback(total: int | None = None, completed: int | None = None) -> None:
            self._progress.update(task_id, total=total, completed=completed, visible=True)

        return _callback
