from podcast_archiver.urls.base import UrlSourceRegistry
from podcast_archiver.urls.base64 import Base64EncodedUrlSource
from podcast_archiver.urls.fireside import FiresideSource
from podcast_archiver.urls.prefixed import UrlPrefixSource
from podcast_archiver.urls.soundcloud import SoundCloudSource
from podcast_archiver.urls.via_apple import (
    ApplePodcastsByIdSource,
    ApplePodcastsSource,
    ContainingApplePodcastsUrlSource,
)

registry = UrlSourceRegistry()

registry.register(ApplePodcastsSource)
registry.register(ApplePodcastsByIdSource)
registry.register(ContainingApplePodcastsUrlSource)
registry.register(UrlPrefixSource)
registry.register(Base64EncodedUrlSource)

# Known website sources that define feeds as alternate+application/rss+xml
# or use a deterministic URL pattern to find the feed URL from the website URL.
registry.register(FiresideSource)
registry.register(SoundCloudSource)
