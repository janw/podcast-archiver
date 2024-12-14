from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class QueueCompletionType(StrEnum):
    COMPLETED = "✔ Archived all episodes"
    FOUND_EXISTING = "✔ Archive is up to date"
    MAX_EPISODES = "✔ Maximum episode count reached"
    FAILED = "✘ Failed"


class DownloadResult(StrEnum):
    ALREADY_EXISTS = "Present"
    COMPLETED_SUCCESSFULLY = "Archived"
    FAILED = " Failed"
    ABORTED = "Aborted"

    @classmethod
    def successful(cls) -> set[DownloadResult]:
        return {
            cls.ALREADY_EXISTS,
            cls.COMPLETED_SUCCESSFULLY,
        }

    def __str__(self) -> str:
        return self.value
