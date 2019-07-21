from requests import Session

from podcast_archiver import __version__

USER_AGENT = f"podcast-archiver/{__version__} +https://github.com/janw/podcast-archiver"

session = Session()
session.headers = {"User-Agent": USER_AGENT}
