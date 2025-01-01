from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pydantic_core

    from podcast_archiver.models.feed import FeedInfo


class PodcastArchiverException(Exception):
    pass


class InvalidSettings(PodcastArchiverException):
    errors: list[pydantic_core.ErrorDetails]

    def __init__(self, *args: Any, errors: list[pydantic_core.ErrorDetails] | None = None) -> None:
        self.errors = errors or []
        super().__init__(*args)

    @staticmethod
    def _format_error(err: pydantic_core.ErrorDetails) -> str:
        return f"Field '{'.'.join(str(loc) for loc in err['loc'])}': {err['msg']}"

    def __str__(self) -> str:
        msg = super().__str__()
        if not self.errors:
            return msg
        return msg + "\n" + "\n".join("* " + self._format_error(err) for err in self.errors)


class MissingDownloadUrl(ValueError):
    pass


class NotCompleted(RuntimeError):
    pass


class NotModified(PodcastArchiverException):
    info: FeedInfo
    last_modified: str | None = None

    def __init__(self, info: FeedInfo, *args: object) -> None:
        super().__init__(*args)
        self.info = info


class NotSupported(PodcastArchiverException):
    pass
