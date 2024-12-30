import json
import re
from time import time

from podcast_archiver import constants
from podcast_archiver.logging import rprint
from podcast_archiver.session import session

LATEST_RELEASE_URL = f"https://api.github.com/repos/{constants.GH_REPO}/releases/latest"
RE_SEMVER = re.compile(r"v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+).*")
NO_VERSION = "v0.0.0"
DAYS = 86400


def has_update(current: str, latest: str) -> bool:
    if not (match := RE_SEMVER.match(current)):
        return False
    local_version = tuple(int(v) for v in match.group("major", "minor", "patch"))
    if not (match := RE_SEMVER.match(latest)):
        return False
    remote_version = tuple(int(v) for v in match.group("major", "minor", "patch"))
    return any(remote > local for local, remote in zip(local_version, remote_version, strict=True))


def get_latest_version() -> str:
    response = session.get(LATEST_RELEASE_URL)
    if response.ok and (tag := response.json().get("tag_name")):
        return tag
    return NO_VERSION


def check_for_updates(*, current_version: str, interval: int) -> None:
    if interval == 0:
        return

    statefile = constants.APP_DIR / "update_check.json"
    now = time()

    last_check, latest_version = 0.0, NO_VERSION
    if statefile.exists():
        with statefile.open("r") as fh:
            state = json.load(fh)
        last_check, latest_version = state["last_check"], state["version"]

    if (not latest_version or last_check + interval * DAYS < now) and (remote_version := get_latest_version()):
        last_check, latest_version = now, remote_version

    with statefile.open("w") as fh:
        json.dump({"last_check": last_check, "version": latest_version}, fh)

    if latest_version == NO_VERSION or not has_update(current_version, latest_version):
        return
    rprint(
        f"An update of {constants.PROG_NAME} available: [b]{current_version} → {latest_version}[/].",
        style="dim",
        highlight=False,
    )
