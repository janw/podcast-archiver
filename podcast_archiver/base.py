from __future__ import annotations

import signal
import sys
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Any

from podcast_archiver.config import Settings
from podcast_archiver.logging import logger, rprint
from podcast_archiver.processor import FeedProcessor

if TYPE_CHECKING:
    from pathlib import Path

    import rich_click as click

    from podcast_archiver.database import BaseDatabase


class PodcastArchiver:
    settings: Settings
    feeds: list[str]

    def __init__(self, settings: Settings | None = None, database: BaseDatabase | None = None):
        self.settings = settings or Settings()
        self.processor = FeedProcessor(settings=self.settings, database=database)

        logger.debug("Initializing with settings: %s", settings)

        self.feeds = []
        for feed in self.settings.feeds:
            self.add_feed(feed)
        for opml in self.settings.opml_files:
            self.add_from_opml(opml)

    def register_cleanup(self, ctx: click.RichContext) -> None:
        def _cleanup(signum: int, *args: Any) -> None:
            logger.debug("Signal %s received", signum)
            rprint("✘ Terminating", style="error")
            self.processor.shutdown()
            ctx.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, _cleanup)
        signal.signal(signal.SIGTERM, _cleanup)

    def add_feed(self, feed: Path | str) -> None:
        new_feeds = [feed] if isinstance(feed, str) else feed.read_text().strip().splitlines()
        for feed in new_feeds:
            if feed not in self.feeds:
                self.feeds.append(feed)

    def add_from_opml(self, opml: Path) -> None:
        with opml.open("r") as file:
            tree = etree.parse(file)

        # TODO: Move parsing to pydantic
        for elem in tree.findall(".//outline[@type='rss'][@xmlUrl!='']"):
            if url := elem.get("xmlUrl"):
                self.add_feed(url)

    def run(self, dry_run: bool = False) -> int:
        failures = 0
        for url in self.feeds:
            result = self.processor.process(url, dry_run=dry_run)
            failures += result.failures

        rprint("✔ All done", style="completed")
        return failures
