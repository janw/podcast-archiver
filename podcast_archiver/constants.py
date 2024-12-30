import pathlib
import re

import click

from podcast_archiver import __version__

GH_REPO = "janw/podcast-archiver"
PROG_NAME = "podcast-archiver"
USER_AGENT = f"{PROG_NAME}/{__version__} (https://github.com/{GH_REPO})"
ENVVAR_PREFIX = "PODCAST_ARCHIVER"
APP_DIR = pathlib.Path(click.get_app_dir(PROG_NAME))

REQUESTS_TIMEOUT = 30

SUPPORTED_LINK_TYPES_RE = re.compile(r"^(audio|video)/")
DOWNLOAD_CHUNK_SIZE = 256 * 1024
DEBUG_PARTIAL_SIZE = DOWNLOAD_CHUNK_SIZE * 4

MAX_TITLE_LENGTH = 120

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d"
DEFAULT_ARCHIVE_DIRECTORY = pathlib.Path(".")
DEFAULT_FILENAME_TEMPLATE = "{show.title}/{episode.published_time:%Y-%m-%d} - {episode.title}.{ext}"
DEFAULT_CONCURRENCY = 4
DEFAULT_DATABASE_FILENAME = "podcast-archiver.db"

DEPRECATION_MESSAGE = "will be removed in the next major release"
