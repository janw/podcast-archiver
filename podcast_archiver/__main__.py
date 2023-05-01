import argparse
import sys
from typing import Union

from pydantic import ValidationError

from podcast_archiver import __version__
from podcast_archiver.argparse import get_parser
from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings


def main(argv: Union[list[str], None] = None) -> None:
    try:
        parser = get_parser(Settings)
        args = parser.parse_args(argv)
        if args.version:
            print(__version__)
            sys.exit(0)
        if args.config_generate:
            Settings.generate_example(args.config_generate)
            sys.exit(0)

        settings = Settings.load_from_yaml(args.config)
        settings.merge_argparser_args(args)
        if not (settings.opml_files or settings.feeds):
            parser.error("Must provide at least one of --feed or --opml")

        pa = PodcastArchiver(settings)
        pa.run()
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except (FileNotFoundError, ValidationError) as error:
        sys.exit("\nERROR: %s" % error)
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))


if __name__ == "__main__":  # pragma: no cover
    main()
