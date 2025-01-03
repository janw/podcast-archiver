from __future__ import annotations

import re

from podcast_archiver.session import session
from podcast_archiver.urls.base import UrlSource

TARGET_URL = "https://feeds.soundcloud.com/users/soundcloud:users:{user_id}/sounds.rss"


class SoundCloudSource(UrlSource):
    page_pattern = re.compile(r"https://soundcloud.com/[\w-]+")
    user_id_pattern = re.compile(r"(soundcloud(:/)?/users:)(?P<user_id>\d+)")

    def parse(self, url: str) -> str | None:
        if not (match := self.page_pattern.match(url)):
            return None

        response = session.get(url)
        if not response.ok:
            return None

        if not (match := self.user_id_pattern.search(response.content.decode())):
            return None

        return TARGET_URL.format(user_id=match["user_id"])
