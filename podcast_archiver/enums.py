from enum import Enum


class QueueCompletionType(str, Enum):
    COMPLETED = "Archived all episodes."
    FOUND_EXISTING = "Archive is up to date."
    MAX_EPISODES = "Maximum episode count reached."
