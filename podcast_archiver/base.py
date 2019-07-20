import feedparser
from feedparser import CharacterEncodingOverride
from urllib.request import urlopen, Request
import urllib.error
from shutil import copyfileobj
from os import path, remove, makedirs
from urllib.parse import urlparse
import unicodedata
import re
import xml.etree.ElementTree as etree

__version__ = "1.0.0-alpha"


class PodcastArchiver:
    _feed_title = ""
    _feedobj = None
    _feed_info_dict = {}

    _userAgent = (
        f"Podcast-Archiver/{{__version__}} (https://github.com/janw/podcast-archiver)"
    )
    _headers = {"User-Agent": _userAgent}
    _global_info_keys = ["author", "language", "link", "subtitle", "title"]
    _episode_info_keys = ["author", "link", "subtitle", "title"]
    _date_keys = ["published"]

    savedir = ""
    verbose = 0
    subdirs = False
    update = False
    progress = False
    maximumEpisodes = None

    feedlist = []

    def __init__(self):

        feedparser.USER_AGENT = self._userAgent

    def addArguments(self, args):

        self.verbose = args.verbose or 0
        if self.verbose > 2:
            print("Input arguments:", args)

        for feed in args.feed or []:
            self.addFeed(feed)

        for opml in args.opml or []:
            self.parseOpmlFile(opml)

        if args.dir:
            self.savedir = args.dir

        self.subdirs = args.subdirs
        self.update = args.update
        self.progress = args.progress
        self.slugify = args.slugify
        self.maximumEpisodes = args.max_episodes or None

        if self.verbose > 1:
            print("Verbose level: ", self.verbose)

    def addFeed(self, feed):
        if path.isfile(feed):
            self.feedlist += open(feed, "r").read().strip().splitlines()
        else:
            self.feedlist.append(feed)

    def parseOpmlFile(self, opml):
        with opml as file:
            tree = etree.fromstringlist(file)

        for feed in [
            node.get("xmlUrl")
            for node in tree.findall("*/outline/[@type='rss']")
            if node.get("xmlUrl") is not None
        ]:

            self.addFeed(feed)

    def processFeeds(self):

        if self.verbose > 0 and self.update:
            print("Updating archive")

        for feed in self.feedlist:
            if self.verbose > 0:
                print("\nDownloading archive for: " + feed)
            linklist = self.processPodcastLink(feed)
            self.downloadPodcastFiles(linklist)

        if self.verbose > 0:
            print("\nDone.")

    def parseGlobalFeedInfo(self, feedobj=None):
        if feedobj is None:
            feedobj = self._feedobj

        self._feed_info_dict = {}
        if "feed" in feedobj:
            for key in self._global_info_keys:
                self._feed_info_dict["feed_" + key] = feedobj["feed"].get(key, None)

        return self._feed_info_dict

    def slugifyString(filename):
        filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore")
        filename = re.sub(r"[^\w\s\-\.]", "", filename.decode("ascii")).strip()
        filename = re.sub(r"[-\s]+", "-", filename)

        return filename

    def linkToTargetFilename(self, link):

        # Remove HTTP GET parameters from filename by parsing URL properly
        linkpath = urlparse(link).path
        basename = path.basename(linkpath)

        # If requested, slugify the filename
        if self.slugify:
            basename = PodcastArchiver.slugifyString(basename)
            self._feed_title = PodcastArchiver.slugifyString(self._feed_title)
        else:
            basename.replace(path.pathsep, "_")
            basename.replace(path.sep, "_")
            self._feed_title.replace(path.pathsep, "_")
            self._feed_title.replace(path.sep, "_")

        # Generate local path and check for existence
        if self.subdirs:
            filename = path.join(self.savedir, self._feed_title, basename)
        else:
            filename = path.join(self.savedir, basename)

        return filename

    def parseFeedToNextPage(self, feedobj=None):

        if feedobj is None:
            feedobj = self._feedobj

        # Assuming there will only be one link declared as 'next'
        self._feed_next_page = [
            link["href"] for link in feedobj["feed"]["links"] if link["rel"] == "next"
        ]

        if len(self._feed_next_page) > 0:
            self._feed_next_page = self._feed_next_page[0]
        else:
            self._feed_next_page = None

        return self._feed_next_page

    def parseFeedToLinks(self, feed=None):

        if feed is None:
            feed = self._feedobj

        # Try different feed episode layouts: 'items' or 'entries'
        episodeList = feed.get("items", False) or feed.get("entries", False)
        if episodeList:
            linklist = [self.parseEpisode(episode) for episode in episodeList]
            linklist = [link for link in linklist if len(link) > 0]
        else:
            linklist = []

        return linklist

    def parseEpisode(self, episode):
        url = None
        episode_info = {}
        for link in episode["links"]:
            if "type" in link.keys():
                if link["type"].startswith("audio"):
                    url = link["href"]
                elif link["type"].startswith("video"):
                    url = link["href"]

                if url is not None:
                    for key in self._episode_info_keys + self._date_keys:
                        episode_info[key] = episode.get(key, None)
                    episode_info["url"] = url

        return episode_info

    def processPodcastLink(self, link, first_page_only=False):
        if self.verbose > 0:
            print("1. Gathering link list ...", end="", flush=True)

        self._feed_title = None
        self._feed_next_page = link
        first_page = True
        linklist = []
        while self._feed_next_page is not None:
            if self.verbose > 0:
                print(".", end="", flush=True)

            self._feedobj = feedparser.parse(self._feed_next_page)

            # Escape improper feed-URL
            if "status" in self._feedobj.keys() and self._feedobj["status"] >= 400:
                print("\nQuery returned HTTP error", self._feedobj["status"])
                return None

            # Escape malformatted XML
            if self._feedobj["bozo"] == 1:

                # If the character encoding is wrong, we continue as long as
                # the reparsing succeeded
                if (
                    type(self._feedobj["bozo_exception"])
                    is not CharacterEncodingOverride
                ):
                    print("\nDownloaded feed is malformatted on", self._feed_next_page)
                    return None

            if first_page:
                self.parseGlobalFeedInfo()
                first_page = False

            # Parse the feed object for episodes and the next page
            linklist += self.parseFeedToLinks(self._feedobj)
            self._feed_next_page = self.parseFeedToNextPage(self._feedobj)

            if self._feed_title is None:
                self._feed_title = self._feedobj["feed"]["title"]

            numberOfLinks = len(linklist)

            # On given option, run an update, break at first existing episode
            if self.update:
                for index, episode_dict in enumerate(linklist):
                    link = episode_dict["url"]
                    filename = self.linkToTargetFilename(link)

                    if path.isfile(filename):
                        del linklist[index:]
                        break
                numberOfLinks = len(linklist)

            # On given option, crop linklist to maximum number of episodes
            if (
                self.maximumEpisodes is not None
                and self.maximumEpisodes < numberOfLinks
            ):
                linklist = linklist[0 : self.maximumEpisodes]
                numberOfLinks = self.maximumEpisodes

            if self.maximumEpisodes is not None or self.update:
                break

            if first_page_only:
                break

        linklist.reverse()

        if self.verbose > 0:
            print(" %d episodes" % numberOfLinks)

        if self.verbose > 2:
            import json

            print("Feed info:\n%s\n" % json.dumps(self._feed_info_dict, indent=2))

        return linklist

    def downloadPodcastFiles(self, linklist):
        if linklist is None or self._feed_title is None:
            return

        nlinks = len(linklist)
        if nlinks > 0:
            if self.verbose == 1:
                print("2. Downloading content ... ", end="")
            elif self.verbose > 1:
                print("2. Downloading content ...")

        for cnt, episode_dict in enumerate(linklist):
            link = episode_dict["url"]
            if self.verbose == 1:
                print(
                    "\r2. Downloading content ... {0}/{1}".format(cnt + 1, nlinks),
                    end="",
                    flush=True,
                )
            elif self.verbose > 1:
                print(
                    "\n\tDownloading file no. {0}/{1}:\n\t{2}".format(
                        cnt + 1, nlinks, link
                    )
                )

                if self.verbose > 2:
                    print("\tEpisode info:")
                    for key in episode_dict.keys():
                        print("\t * %10s: %s" % (key, episode_dict[key]))

            # Check existence once ...
            filename = self.linkToTargetFilename(link)

            if self.verbose > 1:
                print("\tLocal filename:", filename)

            if path.isfile(filename):
                if self.verbose > 1:
                    print("\t✓ Already exists.")
                continue

            # Begin downloading
            prepared_request = Request(link, headers=self._headers)
            try:
                with urlopen(prepared_request) as response:

                    # Check existence another time, with resolved link
                    link = response.geturl()
                    total_size = int(response.getheader("content-length", "0"))
                    old_filename = filename
                    filename = self.linkToTargetFilename(link)

                    if old_filename != filename:
                        if self.verbose > 1:
                            print("\tResolved filename:", filename)

                        if path.isfile(filename):
                            if self.verbose > 1:
                                print("\t✓ Already exists.")
                            continue

                    # Create the subdir, if it does not exist
                    makedirs(path.dirname(filename), exist_ok=True)

                    if self.progress and total_size > 0:

                        with open(filename, "wb") as outfile:
                            self.prettyCopyfileobj(response, outfile)
                    else:
                        with open(filename, "wb") as outfile:
                            copyfileobj(response, outfile)

                if self.verbose > 1:
                    print("\t✓ Download successful.")
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                if self.verbose > 1:
                    print("\t✗ Download failed. Query returned '%s'" % error)
            except KeyboardInterrupt:
                if self.verbose > 0:
                    print("\n\t✗ Unexpected interruption. Deleting unfinished file.")

                remove(filename)
                raise

    def prettyCopyfileobj(self, fsrc, fdst, callback, block_size=8 * 1024):
        while True:
            buf = fsrc.read(block_size)
            if not buf:
                break
            fdst.write(buf)
            callback(len(buf))

    def __str__():
        return "Podcast-Archiver"
