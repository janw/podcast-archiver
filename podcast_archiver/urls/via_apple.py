import re

from pydantic import BaseModel, Field, ValidationError

from podcast_archiver.session import session
from podcast_archiver.urls.base import UrlSource

LOOKUP_URL = "https://itunes.apple.com/lookup?id={podcast_id}&media=podcast"


SUPPORTED_APPLE_PODCASTS_FEED_ID_URLS = re.compile(r"""(?x)https?://( # Verbose mode
    pca\.st/itunes/|                    # Pocket Casts
    castbox\.fm/channel/(id)?|          # Castbox
    castro\.fm/itunes/|                 # Castro
    overcast\.fm/itunes|                # Overcast
    geo\.itunes\.apple\.com/.*?/id|     # iTunes
    podcasts\.apple\.com/.*?/id         # Apple Podcasts
    )(?P<podcast_id>\d+)
""")


SUPPORTED_CONTAINING_APPLE_PODCASTS_FEED_ID_URLS = re.compile(r"""(?x)^https?://( # Verbose mode
    overcast\.fm/\+.+|                  # Overcast episode page
    castro\.fm/(episode|podcast)/.+     # Castro podcast and episode pages
    )$
""")


class LookupResult(BaseModel):
    title: str = Field(alias="collectionName")
    url: str = Field(alias="feedUrl")


class LookupResponse(BaseModel):
    results: list[LookupResult]


class ApplePodcastsSource(UrlSource):
    pattern = SUPPORTED_APPLE_PODCASTS_FEED_ID_URLS

    __slots__ = ()

    def parse(self, url: str) -> str | None:
        if match := self.pattern.match(url):
            return self.feed_by_id(match["podcast_id"])
        return None

    @staticmethod
    def feed_by_id(podcast_id: str) -> str | None:
        response = session.get(LOOKUP_URL.format(podcast_id=podcast_id))
        if not response.ok:
            return None

        try:
            response_obj = LookupResponse.model_validate_json(response.content)
        except ValidationError:
            return None

        if not (results := response_obj.results):
            return None

        return results[0].url


class ApplePodcastsByIdSource(ApplePodcastsSource):
    pattern = re.compile(r"(id)?(?P<podcast_id>\d+)")


class ContainingApplePodcastsUrlSource(ApplePodcastsSource):
    page_pattern = SUPPORTED_CONTAINING_APPLE_PODCASTS_FEED_ID_URLS

    def parse(self, url: str) -> str | None:
        if not (match := self.page_pattern.match(url)):
            return None

        response = session.get(url)
        if not response.ok:
            return None

        if not (match := self.pattern.search(response.content.decode())):
            return None

        return self.feed_by_id(match["podcast_id"])
