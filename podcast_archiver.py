#!/usr/bin/env python3

import argparse
import re
import sys
import unicodedata
import urllib.error
import xml.etree.ElementTree as etree
from argparse import ArgumentTypeError
from os import W_OK, access, makedirs, path, remove
from shutil import copyfileobj
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser
from dateutil.parser import parse as dateparse
from feedparser import CharacterEncodingOverride


class writeable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not path.isdir(prospective_dir):
            raise ArgumentTypeError(f"{prospective_dir} does not exist")
        if access(prospective_dir, W_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ArgumentTypeError(f"{prospective_dir} is not writeable")


class PodcastArchiver:
    _userAgent = "Podcast-Archiver/0.4 (https://github.com/janwh/podcast-archiver)"
    _headers = {"User-Agent": _userAgent}
    _global_info_keys = [
        "author",
        "language",
        "link",
        "subtitle",
        "title",
    ]
    _episode_info_keys = [
        "author",
        "link",
        "subtitle",
        "title",
    ]
    _date_keys = [
        "published",
    ]

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
        self.prefix_with_date = args.date_prefix or None

        if self.verbose > 1:
            print("Verbose level: ", self.verbose)

    def addFeed(self, feed):
        if path.isfile(feed):
            with open(feed, "r") as fp:
                self.feedlist += fp.read().strip().splitlines()
        else:
            self.feedlist.append(feed)

    def parseOpmlFile(self, opml):
        with opml as file:
            tree = etree.fromstringlist(file)

        for feed in [
            node.get("xmlUrl") for node in tree.findall("*/outline/[@type='rss']") if node.get("xmlUrl") is not None
        ]:
            self.addFeed(feed)

    def processFeed(self, feed_url):
        if self.verbose > 0:
            print(f"\nDownloading archive for: {feed_url}\n1. Gathering link list ...", end="", flush=True)

        linklist, feed_info = self.processPodcastLink(feed_url)
        if self.verbose == 1:
            print("%d episodes to process" % len(linklist))
        if self.verbose > 2:
            print("\n\tFeed info:")
            for key, value in feed_info.items():
                print("\t * %10s: %s" % (key, value))
            print()
        if not linklist:
            return
        if self.verbose == 1:
            print("2. Downloading content ... ", end="")
        elif self.verbose > 1:
            print("2. Downloading content ...")
        self.downloadEpisodes(linklist, feed_info)

    def processFeeds(self):
        if self.verbose > 0 and self.update:
            print("Updating archive")
        for feed_url in self.feedlist:
            self.processFeed(feed_url)
        if self.verbose > 0:
            print("\nDone.")

    @staticmethod
    def slugifyString(filename):
        filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore")
        filename = re.sub("[^\w\s\-\.]", "", filename.decode("ascii")).strip()
        filename = re.sub("[-\s]+", "-", filename)

        return filename

    def linkToTargetFilename(self, link, feed_info, must_have_ext=False, episode_info=None):
        linkpath = urlparse(link).path
        basename = path.basename(linkpath)
        feed_title = feed_info["title"]

        if self.prefix_with_date and episode_info:
            date_str = dateparse(episode_info["published"]).strftime("%Y-%m-%d")
            basename = f"{date_str} {basename}"

        _, ext = path.splitext(basename)
        if must_have_ext and not ext:
            return None

        if self.slugify:
            basename = self.slugifyString(basename)
            feed_title = self.slugifyString(feed_title)
        else:
            basename.replace(path.pathsep, "_")
            basename.replace(path.sep, "_")
            feed_title.replace(path.pathsep, "_")
            feed_title.replace(path.sep, "_")

        if self.subdirs:
            filename = path.join(self.savedir, feed_title, basename)
        else:
            filename = path.join(self.savedir, basename)

        return filename

    def parseFeedToNextPage(self, feedobj):
        # Assuming there will only be one link declared as 'next'
        feed_next_page = [link["href"] for link in feedobj["feed"]["links"] if link["rel"] == "next"]
        if len(feed_next_page) > 0:
            return feed_next_page[0]

    def parseFeedToLinks(self, feedobj):
        # Try different feed episode layouts: 'items' or 'entries'
        episodeList = feedobj.get("items", False) or feedobj.get("entries", False)
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
            if "type" in link:
                if link["type"].startswith("audio") or link["type"].startswith("video"):
                    url = link["href"]

                if url is not None:
                    for key in self._episode_info_keys + self._date_keys:
                        episode_info[key] = episode.get(key, None)
                    episode_info["url"] = url

        return episode_info

    def getFeedObj(self, feed_url):
        feedobj = feedparser.parse(feed_url)

        # Escape improper feed-URL
        if "status" in feedobj and feedobj["status"] >= 400:
            print("\nQuery returned HTTP error", feedobj["status"])
            return None

        # Escape malformatted XML; If the character encoding is wrong, continue as long as the reparsing succeeded
        if feedobj["bozo"] == 1 and not isinstance(feedobj["bozo_exception"], CharacterEncodingOverride):
            print("\nDownloaded feed is malformatted on", feed_url)
            return None

        return feedobj

    def truncateLinkList(self, linklist, feed_info):
        # On given option, run an update, break at first existing episode
        if self.update:
            for index, episode_dict in enumerate(linklist):
                link = episode_dict["url"]
                filename = self.linkToTargetFilename(link, feed_info)

                if path.isfile(filename):
                    del linklist[index:]
                    if self.verbose > 1:
                        print(f" found existing episodes, {len(linklist)} new to process")
                    return True, linklist

        # On given option, crop linklist to maximum number of episodes
        if self.maximumEpisodes is not None and self.maximumEpisodes < len(linklist):
            linklist = linklist[0 : self.maximumEpisodes]
            if self.verbose > 1:
                print(f" reached maximum episode count of {self.maximumEpisodes}")
            return True, linklist

        return False, linklist

    def parseFeedInfo(self, feedobj):
        feed_header = feedobj.get("feed", {})
        feed_info = {key: feed_header.get(key, None) for key in self._global_info_keys}
        if feed_info.get("title"):
            return feed_info

        print("✗ Feed is missing title information.")
        return None

    def processPodcastLink(self, feed_next_page):
        feed_info = None
        linklist = []
        while True:
            if not (feedobj := self.getFeedObj(feed_next_page)):
                break

            if not feed_info:
                feed_info = self.parseFeedInfo(feedobj)
                if not feed_info:
                    return [], {}

            # Parse the feed object for episodes and the next page
            linklist += self.parseFeedToLinks(feedobj)
            feed_next_page = self.parseFeedToNextPage(feedobj)
            was_truncated, linklist = self.truncateLinkList(linklist, feed_info)

            if not feed_next_page or was_truncated:
                break

            if self.verbose > 0:
                print(".", end="", flush=True)

        if self.verbose == 1:
            print(" ", end="", flush=True)
        linklist.reverse()
        return linklist, feed_info

    def checkEpisodeExistsPreflight(self, link, *, feed_info, episode_dict):
        # Check existence once ...
        filename = self.linkToTargetFilename(link, feed_info=feed_info, episode_info=episode_dict)

        if self.verbose > 1:
            print("\tLocal filename:", filename)

        if path.isfile(filename):
            if self.verbose > 1:
                print("\t✓ Already exists.")
            return None

        return filename

    def logDownloadHeader(self, link, episode_dict, *, index, total):
        if self.verbose == 1:
            print("\r2. Downloading episodes ... {0}/{1}".format(index + 1, total), end="", flush=True)
        elif self.verbose > 1:
            print("\n\tDownloading episode no. {0}/{1}:\n\t{2}".format(index + 1, total, link))
        if self.verbose > 2:
            print("\tEpisode info:")
            for key, value in episode_dict.items():
                print("\t * %10s: %s" % (key, value))

    def processResponse(self, response, *, filename, feed_info, episode_dict):
        # Check existence another time, with resolved link
        link = response.geturl()
        total_size = int(response.getheader("content-length", "0"))
        new_filename = self.linkToTargetFilename(link, feed_info, must_have_ext=True, episode_info=episode_dict)

        if new_filename and new_filename != filename:
            filename = new_filename
            if self.verbose > 1:
                print("\tResolved filename:", filename)

            if path.isfile(filename):
                if self.verbose > 1:
                    print("\t✓ Already exists.")
                return

        # Create the subdir, if it does not exist
        makedirs(path.dirname(filename), exist_ok=True)

        if self.progress and total_size > 0:
            from tqdm import tqdm

            if self.verbose < 2:
                print(f"\nDownloading {filename}")
            with (
                tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024) as progress_bar,
                open(filename, "wb") as outfile,
            ):
                self.prettyCopyfileobj(response, outfile, callback=progress_bar.update)
        else:
            with open(filename, "wb") as outfile:
                copyfileobj(response, outfile)

    def downloadEpisode(self, link, *, feed_info, episode_dict):
        filename = self.checkEpisodeExistsPreflight(link, feed_info=feed_info, episode_dict=episode_dict)
        if not filename:
            return
        prepared_request = Request(link, headers=self._headers)
        try:
            with urlopen(prepared_request) as response:
                self.processResponse(response, filename=filename, feed_info=feed_info, episode_dict=episode_dict)
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

    def downloadEpisodes(self, linklist, feed_info):
        nlinks = len(linklist)
        for cnt, episode_dict in enumerate(linklist):
            link = episode_dict["url"]

            self.logDownloadHeader(link, episode_dict, index=cnt, total=nlinks)
            self.downloadEpisode(link, feed_info=feed_info, episode_dict=episode_dict)

    def prettyCopyfileobj(self, fsrc, fdst, callback, block_size=128 * 1024):
        while True:
            buf = fsrc.read(block_size)
            if not buf:
                break
            fdst.write(buf)
            callback(len(buf))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--opml",
        action="append",
        type=argparse.FileType("r"),
        help=(
            "Provide an OPML file (as exported by many other podcatchers) containing your feeds. The parameter can be"
            " used multiple times, once for every OPML file."
        ),
    )
    parser.add_argument(
        "-f",
        "--feed",
        action="append",
        help="Add a feed URl to the archiver. The parameter can be used multiple times, once for every feed.",
    )
    parser.add_argument("-d", "--dir", action=writeable_dir, help="Set the output directory of the podcast archive.")
    parser.add_argument(
        "-s",
        "--subdirs",
        action="store_true",
        help="Place downloaded podcasts in separate subdirectories per podcast (named with their title).",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help=(
            "Force the archiver to only update the feeds with newly added episodes. As soon as the first old episode"
            " found in the download directory, further downloading is interrupted."
        ),
    )
    parser.add_argument("-v", "--verbose", action="count", help="Increase the level of verbosity while downloading.")
    parser.add_argument("-p", "--progress", action="store_true", help="Show progress bars while downloading episodes.")
    parser.add_argument(
        "-S",
        "--slugify",
        action="store_true",
        help=(
            "Clean all folders and filename of potentially weird characters that might cause trouble with one or"
            " another target filesystem."
        ),
    )
    parser.add_argument(
        "-m",
        "--max-episodes",
        type=int,
        help=(
            "Only download the given number of episodes per podcast feed. Useful if you don't really need the entire"
            " backlog."
        ),
    )
    parser.add_argument(
        "--date-prefix",
        action="store_true",
        help=(
            "Prefix all episodes with an ISO8602 formatted date of when they were published. Useful to ensure"
            " chronological ordering."
        ),
    )

    try:
        args = parser.parse_args()
        if not (args.opml or args.feed):
            parser.error("Must provide at least one of --feed or --opml")

        pa = PodcastArchiver()
        pa.addArguments(args)
        pa.processFeeds()
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except FileNotFoundError as error:
        sys.exit("\nERROR: %s" % error)
    except ArgumentTypeError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
