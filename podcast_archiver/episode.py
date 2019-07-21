from os import path
import re
import logging
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen

from podcast_archiver.config import config
from podcast_archiver.utils import slugify
from podcast_archiver.mixins import InfoKeyMixin

logger = logging.getLogger(__name__)

re_linktype = re.compile(r"^(audio|video).*")


class Episode(InfoKeyMixin):
    INFO_KEYS = ["author", "link", "subtitle", "title", "published"]
    url = None

    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.url = url

    @classmethod
    def from_feedentry(cls, episode):
        metadata = {key: episode.get(key, None) for key in cls.INFO_KEYS}
        instance = cls(cls.extract_content_url(episode), **metadata)

        return instance

    @staticmethod
    def extract_content_url(episode):
        for link in episode.get("links", []):
            link_type = link.get("type", "")
            if re_linktype.match(link_type):
                return link["href"]

        raise ValueError("Could not extract usable link from Episode")

    def print_info(self):
        print("\tEpisode info:")
        for key in self.INFO_KEYS:
            print("\t * %10s: %s" % (key, getattr(self, key)))

    @property
    def filename(self):

        # Remove HTTP GET parameters from filename by parsing URL properly
        linkpath = urlparse(self.url).path
        basename = path.basename(linkpath)

        # If requested, slugify the filename
        if config.slugify:
            basename = slugify(basename)
        else:
            basename.replace(path.pathsep, "_")
            basename.replace(path.sep, "_")

        return basename


class EpisodeList(list):
    @classmethod
    def from_feedpage(cls, feedpage):
        instance = cls()
        # Try different feed episode layouts: 'items' or 'entries'
        episodeList = feedpage.get("items", False) or feedpage.get("entries", False)
        if episodeList:
            for episode in episodeList:
                try:
                    instance.append(Episode.from_feedentry(episode))
                except ValueError:
                    logger.warning(f"Could not parse episode {episode}")

        return instance
