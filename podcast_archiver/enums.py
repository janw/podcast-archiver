from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
    from rich.console import RenderableType


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class QueueCompletionType(StrEnum):
    COMPLETED = "✔ Archived all episodes"
    DRY_RUN = "✔ Dry-run completed"
    FOUND_EXISTING = "✔ Archive is up to date"
    MAX_EPISODES = "✔ Maximum episode count reached"
    FAILED = "✘ Failed"

    @property
    def style(self) -> str:
        if self in self.successful():
            return "completed"
        return "error"

    @classmethod
    def successful(cls) -> set[QueueCompletionType]:
        return {
            cls.COMPLETED,
            cls.DRY_RUN,
            cls.FOUND_EXISTING,
            cls.MAX_EPISODES,
        }

    def __rich__(self) -> RenderableType:
        return Text(self.value, style=self.style, end="")


class DownloadResult(StrEnum):
    ALREADY_EXISTS = "✓ Present"
    COMPLETED_SUCCESSFULLY = "✓ Archived"
    MISSING = "✘ Missing"
    FAILED = "✘ Failed"
    ABORTED = "✘ Aborted"

    @property
    def style(self) -> str:
        if self in self.successful():
            return "success"
        if self is self.MISSING:
            return "missing"
        return "error"

    @classmethod
    def successful(cls) -> set[DownloadResult]:
        return {
            cls.ALREADY_EXISTS,
            cls.COMPLETED_SUCCESSFULLY,
        }

    def render_padded(self, padding: str = "   ") -> RenderableType:
        return Text(f"{self.value:{RESULT_MAX_LEN}s}{padding}", style=self.style, end="")

    def __rich__(self) -> RenderableType:
        return self.render_padded()


RESULT_MAX_LEN = max(len(result.value) for result in DownloadResult)
