import logging

logger = logging.getLogger(__name__)


class Episode:
    INFO_KEYS = ["author", "link", "subtitle", "title", "published"]

    url = ""

    def __init__(self, url, **kwargs):
        self.url = url

        for key, datum in kwargs.items():
            if key not in self.INFO_KEYS:
                raise ValueError(f"Got unexpected metadatum {key}")

            setattr(self, key, datum)

    @classmethod
    def from_feedentry(cls, episode):
        metadata = {key: episode.get(key, None) for key in cls.INFO_KEYS}
        instance = cls(cls.extract_content_url(episode), **metadata)

        return instance

    @staticmethod
    def extract_content_url(episode):
        for link in episode["links"]:
            if "type" in link.keys():
                if link["type"].startswith("audio"):
                    return link["href"]
                elif link["type"].startswith("video"):
                    return link["href"]

        raise ValueError("Could not extract usable link from Episode")

    def print_info(self):
        print("\tEpisode info:")
        for key in self.INFO_KEYS:
            print("\t * %10s: %s" % (key, getattr(self, key)))


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
