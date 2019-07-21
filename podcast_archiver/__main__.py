import logging
import sys
from argparse import ArgumentTypeError

from podcast_archiver.base import PodcastArchiver
from podcast_archiver.argparser import parser
from podcast_archiver.feedlist import add_feeds_from_feedsfile
from podcast_archiver.feedlist import add_feeds_from_opml


def main():
    try:
        logging.basicConfig(level=logging.DEBUG)

        args = parser.parse_args()

        feeds = args.feed or []
        for f in args.feedsfile or []:
            feeds += add_feeds_from_feedsfile(f)
        for o in args.opml or []:
            feeds += add_feeds_from_opml(o)

        pa = PodcastArchiver(feeds)
        pa.addArguments(args)
        pa.processFeeds()

    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except FileNotFoundError as error:
        sys.exit("\nERROR: %s" % error)
    except ArgumentTypeError as error:
        sys.exit("\nERROR: Your config is invalid: %s" % error)


main()
