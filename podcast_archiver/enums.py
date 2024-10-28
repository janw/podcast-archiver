from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class QueueCompletionType(StrEnum):
    COMPLETED = "Archived all episodes"
    MAX_EPISODES = "Maximum episode count reached"


class JobResult(StrEnum):
    ALREADY_EXISTS_DB = "Exists in database"
    ALREADY_EXISTS_DISK = "Exists on disk"
    COMPLETED_SUCCESSFULLY = "Completed"
    FAILED = "Failed"
    ABORTED = "Aborted"

    def __str__(self) -> str:
        return self.value
