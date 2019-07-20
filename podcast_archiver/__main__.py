import sys
import argparse
from argparse import ArgumentTypeError

from podcast_archiver.utils import writeable_dir
from podcast_archiver import PodcastArchiver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--opml",
        action="append",
        type=argparse.FileType("r"),
        help="""Provide an OPML file (as exported by many other podcatchers)
                containing your feeds. The parameter can be used multiple
                times, once for every OPML file.""",
    )
    parser.add_argument(
        "-f",
        "--feed",
        action="append",
        help="""Add a feed URl to the archiver. The parameter can be used
                multiple times, once for every feed.""",
    )
    parser.add_argument(
        "-d",
        "--dir",
        action=writeable_dir,
        help="""Set the output directory of the podcast archive.""",
    )
    parser.add_argument(
        "-s",
        "--subdirs",
        action="store_true",
        help="""Place downloaded podcasts in separate subdirectories per
                podcast (named with their title).""",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="""Force the archiver to only update the feeds with newly added
                episodes. As soon as the first old episode found in the
                download directory, further downloading is interrupted.""",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="""Increase the level of verbosity while downloading.""",
    )
    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="""Show progress bars while downloading episodes.""",
    )
    parser.add_argument(
        "-S",
        "--slugify",
        action="store_true",
        help="""Clean all folders and filename of potentially weird
                characters that might cause trouble with one or another
                target filesystem.""",
    )
    parser.add_argument(
        "-m",
        "--max-episodes",
        type=int,
        help="""Only download the given number of episodes per podcast
                feed. Useful if you don't really need the entire backlog.""",
    )

    args = parser.parse_args()

    pa = PodcastArchiver()
    pa.addArguments(args)
    pa.processFeeds()


try:
    main()
except KeyboardInterrupt:
    sys.exit("\nERROR: Interrupted by user")
except FileNotFoundError as error:
    sys.exit("\nERROR: %s" % error)
except ArgumentTypeError as error:
    sys.exit("\nERROR: Your config is invalid: %s" % error)
