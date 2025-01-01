import re
from base64 import b64decode

from podcast_archiver.urls.base import UrlSource

# cspell: disable
SUPPORTED_PREFIXED_FEED_URL_URLS = re.compile(r"""(?x)^(
    https?://podcasts\.google\.com/\?feed=       #  Google Podcasts
    )(?P<base64_feed>.+)$
""")


class Base64EncodedUrlSource(UrlSource):
    pattern = SUPPORTED_PREFIXED_FEED_URL_URLS

    def parse(self, url: str) -> str | None:
        if match := self.pattern.match(url):
            return b64decode(match["base64_feed"]).decode("utf-8")
        return None
