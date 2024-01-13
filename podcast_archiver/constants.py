import re

from podcast_archiver import __version__

PROG_NAME = "podcast-archiver"
USER_AGENT = f"{PROG_NAME}/{__version__} (https://github.com/janw/podcast-archiver)"
ENVVAR_PREFIX = "PODCAST_ARCHIVER"

REQUESTS_TIMEOUT = 30

SUPPORTED_LINK_TYPES_RE = re.compile(r"^(audio|video)/")
DOWNLOAD_CHUNK_SIZE = 256 * 1024
DEBUG_PARTIAL_SIZE = DOWNLOAD_CHUNK_SIZE * 4
