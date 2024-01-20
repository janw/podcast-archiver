from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class QueueCompletionType(StrEnum):
    COMPLETED = "Archived all episodes."
    FOUND_EXISTING = "Archive is up to date."
    MAX_EPISODES = "Maximum episode count reached."


class DownloadResult(StrEnum):
    ALREADY_EXISTS = "File already exists."
    COMPLETED_SUCCESSFULLY = "Completed successfully."
    FAILED = "Failed."
    ABORTED = "Aborted."

    def __str__(self) -> str:
        return self.value
