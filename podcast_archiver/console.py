from typing import TYPE_CHECKING

from rich import progress, table
from rich.console import Console, RenderableType

console = Console()

if TYPE_CHECKING:
    _MixinBase = progress.ProgressColumn
else:
    _MixinBase = object


class HideableColumnMixin(_MixinBase):
    def __call__(self, task: progress.Task) -> RenderableType:
        speed = task.finished_speed or task.speed
        if speed is None:
            return ""
        return super().__call__(task)


class HideableTimeRemainingColumn(HideableColumnMixin, progress.TimeRemainingColumn):
    pass


class HideableTransferSpeedColumn(HideableColumnMixin, progress.TransferSpeedColumn):
    pass


COMMON_PROGRESS_COLUMNS: list[progress.ProgressColumn] = [
    progress.SpinnerColumn(finished_text="[bar.finished]✔[/]"),
    progress.TextColumn(
        "{task.fields[date]:%Y-%m-%d}",
        style="blue",
        table_column=table.Column(width=len("2023-09-24")),
    ),
    progress.TextColumn(
        "{task.description}",
        style="progress.description",
        table_column=table.Column(no_wrap=True, ratio=2),
    ),
    progress.BarColumn(bar_width=25),
    progress.TaskProgressColumn(),
    progress.DownloadColumn(),
]

TRANSFER_COLUMNS: list[progress.ProgressColumn] = [
    HideableTimeRemainingColumn(),
    HideableTransferSpeedColumn(),
]


def get_progress(console: Console, dry_run: bool, disable: bool) -> progress.Progress:
    cols = COMMON_PROGRESS_COLUMNS
    if dry_run:
        cols += [progress.TextColumn("[bright_black]\\[dry-run][/]")]
    else:
        cols += TRANSFER_COLUMNS

    prog = progress.Progress(*cols, console=console, expand=True, disable=disable)
    prog.live.vertical_overflow = "visible"
    return prog
