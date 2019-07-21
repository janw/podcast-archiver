from os import path, makedirs, remove
import re
import logging
from urllib.parse import urlparse

from requests import RequestException

from podcast_archiver.config import config
from podcast_archiver.session import session
from podcast_archiver.utils import slugify
from podcast_archiver.mixins import InfoKeyMixin

logger = logging.getLogger(__name__)

re_linktype = re.compile(r"^(audio|video).*")


class Episode(InfoKeyMixin):
    INFO_KEYS = ["author", "link", "subtitle", "title", "published"]
    url = None
    url_resolved = None

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
        return self.url_to_filename(self.url)

    @property
    def filename_resolved(self):
        return self.url_to_filename(self.url_resolved)

    @staticmethod
    def url_to_filename(url):
        if url is None:
            return None

        # Remove HTTP GET parameters from filename by parsing URL properly
        linkpath = urlparse(url).path
        filename = path.basename(linkpath)

        # If requested, slugify the filename
        if config.slugify:
            filename = slugify(filename)
        else:
            filename.replace(path.pathsep, "_")
            filename.replace(path.sep, "_")

        return filename

    def download(self, destination):
        makedirs(destination, exist_ok=True)
        filename = path.join(destination, self.filename)
        logger.debug(f"Downloading {self.filename} from {self.url}")

        try:
            with session as s:
                response = s.get(self.url, stream=True)

                self.url_resolved = response.url
                if self.url_resolved != self.url:
                    logger.debug(f"Resolved URL to {self.url_resolved}")

                with open(filename, "wb") as outfile:
                    for chunk in response.iter_content(chunk_size=128):
                        outfile.write(chunk)

            logger.debug("Download successful")
        except RequestException as exc:
            logger.warning(f"Download failed for {filename}. Query returned {exc}")
        except KeyboardInterrupt:
            logger.error(f"Unexpected interruption. Deleting unfinished file.")
            remove(filename)
            raise


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
