from requests import Session

from podcast_archiver.constants import USER_AGENT

session = Session()
session.headers.update({"user-agent": USER_AGENT})
