import re

from podcast_archiver.urls.base import UrlSource

TARGET_URL = "https://feeds.fireside.fm/{slug}/rss"


class FiresideSource(UrlSource):
    pattern = re.compile(r"^https?://(?P<slug>[\w-]+)\.fireside\.fm")

    def parse(self, url: str) -> str | None:
        if match := self.pattern.match(url):
            return TARGET_URL.format(slug=match["slug"])
        return None
