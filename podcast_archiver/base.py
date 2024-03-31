from __future__ import annotations

import xml.etree.ElementTree as etree
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, ValidationError

from podcast_archiver.console import console
from podcast_archiver.exceptions import InvalidFeed
from podcast_archiver.logging import logger
from podcast_archiver.processor import FeedProcessor

if TYPE_CHECKING:
    import rich_click as click

    from podcast_archiver.config import Settings


class PodcastArchiver:
    settings: Settings
    feeds: set[AnyHttpUrl]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.processor = FeedProcessor(settings=settings)

        logger.debug("Initializing with settings: %s", settings)

        try:
            self.feeds = set()
            for feed in self.settings.feeds:
                self.add_feed(feed)
            for opml in self.settings.opml_files:
                self.add_from_opml(opml)
        except ValidationError as exc:
            raise InvalidFeed(feed=exc.errors()[0]["input"]) from exc

    def register_cleanup(self, ctx: click.RichContext) -> None:
        @ctx.call_on_close
        def _cleanup() -> None:
            self.processor.shutdown()

    def add_feed(self, feed: Path | AnyHttpUrl | str) -> None:
        if isinstance(feed, Path):
            with open(feed, "r") as fp:
                for f in fp.read().strip().splitlines():
                    self.add_feed(f)
            return
        if isinstance(feed, str):
            feed = AnyHttpUrl(feed)
        self.feeds.add(feed)

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

        console.print("\n[bar.finished]Done.[/]\n")
        return failures
