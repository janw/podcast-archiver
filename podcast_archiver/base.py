import logging

from podcast_archiver.podcast import Podcast
from podcast_archiver.downloader import PodcastDownloader

logger = logging.getLogger(__name__)


class PodcastArchiver:
    savedir = ""
    verbose = 0
    subdirs = False
    update = False
    progress = False
    maximumEpisodes = None

    feedlist = None

    def __init__(self, feeds):
        self.feedlist = feeds

    def addArguments(self, args):

        self.verbose = args.verbose or 0
        if self.verbose > 2:
            print("Input arguments:", args)

        if args.dir:
            self.savedir = args.dir

        self.subdirs = args.subdirs
        self.update = args.update
        self.progress = args.progress
        self.slugify = args.slugify
        self.maximumEpisodes = args.max_episodes or None

        if self.verbose > 1:
            print("Verbose level: ", self.verbose)

    def processFeeds(self):
        logger.info("Start downloading archive")

        for feed in self.feedlist:
            logger.info(f"Feed {feed}")
            podcast = Podcast.from_link(feed)
            downloader = PodcastDownloader(podcast)
            downloader.download()

        logger.info("Done!")

    def __repr__(self):
        return f"<podcast-archiver ({len(self.feedlist)} feeds)>"
