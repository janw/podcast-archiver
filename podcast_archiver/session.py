from typing import Any

from requests import PreparedRequest, Session
from requests.adapters import HTTPAdapter
from requests.models import Response as Response
from urllib3.util import Retry

from podcast_archiver.constants import REQUESTS_TIMEOUT, USER_AGENT


class DefaultTimeoutHTTPAdapter(HTTPAdapter):
    def send(
        self,
        request: PreparedRequest,
        timeout: None | float | tuple[float, float] | tuple[float, None] = None,
        **kwargs: Any,
    ) -> Response:
        return super().send(request, timeout=timeout or REQUESTS_TIMEOUT, **kwargs)


_retries = Retry(
    total=3,
    connect=1,
    backoff_factor=0.5,
    status_forcelist=[500, 501, 502, 503, 504],
)

_adapter = DefaultTimeoutHTTPAdapter(max_retries=_retries)

session = Session()
session.mount("http://", _adapter)
session.mount("https://", _adapter)
session.headers.update({"user-agent": USER_AGENT})
