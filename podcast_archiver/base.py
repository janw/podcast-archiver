from __future__ import annotations

import signal
import sys
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Any

from podcast_archiver.logging import logger, rprint
from podcast_archiver.processor import FeedProcessor

if TYPE_CHECKING:
    from pathlib import Path

    import rich_click as click

    from podcast_archiver.config import Settings


class PodcastArchiver:
    settings: Settings
    feeds: list[str]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.processor = FeedProcessor(settings=self.settings)

        logger.debug("Initializing with settings: %s", settings)

        self.feeds = []
        for feed in self.settings.feeds:
            self.add_feed(feed)
        for opml in self.settings.opml_files:
            self.add_from_opml(opml)

    def register_cleanup(self, ctx: click.RichContext) -> None:
        def _cleanup(signum: int, *args: Any) -> None:
            logger.debug("Signal %s received", signum)
            rprint("[error]Terminating.[/]")
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

    def run(self) -> int:
        failures = 0
        for url in self.feeds:
            result = self.processor.process(url)
            failures += result.failures

        rprint("\n[bar.finished]Done.[/]\n")
        return failures
