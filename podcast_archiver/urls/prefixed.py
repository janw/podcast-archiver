import re

from podcast_archiver.urls.base import UrlSource

# cspell: disable
SUPPORTED_PREFIXED_FEED_URL_URLS = re.compile(r"""(?x)^(
    https?://pcasts\.in/feed/|      #  Pocket Casts
    pktc://subscribe/|              #  Pocket Casts
    podcastrepublic://subscribe/|   #  Podcast Republic
    (
        overcast|           # https://overcast.fm
        beyondpod|          # http://beyondpod.mobi
        downcast|           # https://www.downcastapp.com
        gpodder|            # https://gpodder.github.io
        icatcher|           # https://icatcher.app/
        instacast|          # Instacast
        podcat|             # Podcat
        podcastaddict|      # Podcast Addict
        podscout|           # Podscout
        rssradio|           # http://rssrad.io
        pcast|              # Google Podcasts
        itpc|               # iTunes and misc Android apps
        podcasts            # Apple Podcasts
    )://
    )(?P<hostpath>.+)$
""")


class UrlPrefixSource(UrlSource):
    pattern = SUPPORTED_PREFIXED_FEED_URL_URLS

    def parse(self, url: str) -> str | None:
        if match := self.pattern.match(url):
            feed = match["hostpath"]
            if not feed.startswith("http://") and not feed.startswith("https://"):
                feed = f"http://{feed}"
            return feed
        return None
