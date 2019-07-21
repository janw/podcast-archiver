import logging
from os import path

import feedparser
from feedparser import CharacterEncodingOverride

from podcast_archiver.session import session
from podcast_archiver.episode import EpisodeList
from podcast_archiver.mixins import InfoKeyMixin
from podcast_archiver.utils import slugify

logger = logging.getLogger(__name__)


class Podcast(InfoKeyMixin):
    INFO_KEYS = ["author", "language", "link", "subtitle", "title", "published"]
    episodes = None

    def __init__(self, episodes, **kwargs):
        super().__init__(**kwargs)
        self.episodes = episodes

    def __len__(self):
        return len(self.episodes)

    def __iter__(self):
        return iter(self.episodes)

    @staticmethod
    def get_feed_page(feedpage):
        with session as s:
            response = s.get(feedpage)
        feedobj = feedparser.parse(response.content)

        # Check for download errors
        if "status" in feedobj.keys() and feedobj["status"] >= 400:
            logger.error(f"Query returned HTTP error {feedobj['status']}")
            return None

        # Check for malformatted XML
        # Continue as long as the reparsing succeeded
        if feedobj["bozo"] == 1 and not isinstance(
            feedobj["bozo_exception"], CharacterEncodingOverride
        ):
            logger.error(f"Downloaded feed is malformatted on", feedpage)
            return None

        return feedobj, Podcast.extract_next_page(feedobj)

    @staticmethod
    def extract_next_page(feedobj):
        links = feedobj["feed"].get("links", [])

        for link in links:
            if link.get("rel", "") == "next":
                return link.get("href")

    @staticmethod
    def extract_podcast_info(feedobj):
        return {key: feedobj["feed"].get(key, None) for key in Podcast.INFO_KEYS}

    @classmethod
    def from_link(cls, link, first_page_only=False, preprocessing_callback=None):
        logger.info("Gathering episodes for podcast")

        next_page = link
        episodes = []
        metadata = None
        while next_page is not None:
            feedobj, next_page = cls.get_feed_page(next_page)

            if metadata is None:
                metadata = cls.extract_podcast_info(feedobj)

            current_episodes = EpisodeList.from_feedpage(feedobj)
            if preprocessing_callback:
                current_episodes, cb_break = preprocessing_callback(current_episodes)

            episodes += current_episodes

            if first_page_only or (preprocessing_callback and cb_break):
                break

        episodes.reverse()

        logger.debug(f"Gathered {len(episodes)} episodes for podcast")

        return cls(episodes, **metadata)

    def download(self, destination):
        destination = path.join(destination, slugify(self.title), "")

        logger.debug(f"Downloading episodes to {destination}")
        for episode in self:
            episode.download(destination)
