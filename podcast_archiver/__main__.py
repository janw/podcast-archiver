import argparse
import sys

from podcast_archiver.argparse import parser
from podcast_archiver.base import PodcastArchiver


def main():
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
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))


main()
