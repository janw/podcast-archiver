from __future__ import annotations

from typing import TYPE_CHECKING, Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from podcast_archiver.constants import REQUESTS_TIMEOUT, USER_AGENT

if TYPE_CHECKING:
    from requests.models import Response


_retries = Retry(
    total=3,
    connect=1,
    backoff_factor=0.5,
    status_forcelist=[500, 501, 502, 503, 504],
)

_adapter = HTTPAdapter(max_retries=_retries)


class ArchiverSession(Session):
    def get_and_raise(
        self,
        url: str,
        *,
        timeout: None | float | tuple[float, float] | tuple[float, None] = REQUESTS_TIMEOUT,
        last_modified: str | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        if last_modified:
            headers = headers or {}
            headers["If-Modified-Since"] = last_modified

        response = self.get(url, timeout=timeout, headers=headers, **kwargs)
        response.raise_for_status()
        return response


session = ArchiverSession()
session.mount("http://", _adapter)
session.mount("https://", _adapter)
session.headers.update({"user-agent": USER_AGENT})
