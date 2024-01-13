from typing import Any

import pydantic_core


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
