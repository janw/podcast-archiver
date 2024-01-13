from enum import Enum


class QueueCompletionMsg(str, Enum):
    COMPLETED = "All episodes downloaded."
    FOUND_EXISTING = "Archive is up to date."
    MAX_EPISODES = "Maximum episode count reached."
