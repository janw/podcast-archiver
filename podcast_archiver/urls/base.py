from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from podcast_archiver.logging import logger

plugin_folder = Path(__file__).parent / "plugins"


class UrlSource(ABC):
    __slots__ = ()

    @abstractmethod
    def parse(self, url: str) -> str | None: ...

    def __str__(self) -> str:
        name = self.__class__.__name__
        if name.endswith("Source"):
            name = name[:-6]
        return name


@dataclass(slots=True)
class UrlSourceRegistry:
    sources: list[UrlSource] = field(default_factory=list)

    def get_feed(self, url: str) -> str | None:
        for source in self.sources:
            if feed_url := source.parse(url):
                logger.info(f"Resolved feed via {source}: {feed_url}")
                return feed_url
        return None

    def register(self, source_cls: type[UrlSource]) -> None:
        self.sources.append(source_cls())
