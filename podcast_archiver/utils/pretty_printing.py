from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, Iterator

from rich.console import Group, NewLine, group
from rich.text import Text

from podcast_archiver.enums import RESULT_MAX_LEN, DownloadResult
from podcast_archiver.logging import rprint

if TYPE_CHECKING:
    from rich.console import ConsoleRenderable, RenderableType

    from podcast_archiver.models.episode import BaseEpisode


NEWLINE = NewLine()


@dataclass(slots=True)
class _ValPair:
    prefix: DownloadResult
    first: BaseEpisode | None = None
    last: BaseEpisode | None = None
    length: int = 0

    def populate(self, obj: BaseEpisode) -> None:
        if not self.first:
            self.first = obj
        self.last = obj
        self.length += 1

    def emit(self) -> _ValPair | None:
        if not self.first:
            return None
        return self

    @group(fit=False)
    def render(self) -> Iterator[RenderableType]:
        if not self.first:
            return

        text = partial(Text, style=self.prefix.style, end="")
        yield self.prefix.render_padded("╶┬╴" if self.length > 1 else "   ")
        yield self.first
        yield NEWLINE

        if self.length > 2:
            yield text(" " * RESULT_MAX_LEN + " │ ")
            yield text("    ︙", style="dim")
            yield NEWLINE

        if self.length > 1 and self.last:
            yield text(" " * RESULT_MAX_LEN + " ╰╴")
            yield self.last
            yield NEWLINE
            yield NEWLINE


class PrettyPrintEpisodeRange:
    _present: _ValPair
    _missing: _ValPair
    _last_populated: _ValPair
    pairs: list[_ValPair]

    __slots__ = ("_present", "_missing", "_last_populated", "pairs")

    def __init__(self) -> None:
        self._present = _ValPair(prefix=DownloadResult.ALREADY_EXISTS)
        self._missing = _ValPair(prefix=DownloadResult.MISSING)
        self._last_populated = self._missing
        self.pairs = []

    def __enter__(self) -> PrettyPrintEpisodeRange:
        return self

    def __exit__(self, *args: Any) -> None:
        if emitted := self._last_populated.emit():
            self.pairs.append(emitted)
        if self.pairs:
            rprint(self, no_wrap=True, overflow="ellipsis")

    def _update_state(self, obj: BaseEpisode, to_populate: _ValPair, to_emit: _ValPair) -> _ValPair:
        self._last_populated = to_populate
        to_populate.populate(obj)
        if emitted := to_emit.emit():
            self.pairs.append(emitted)
            return _ValPair(prefix=to_emit.prefix)
        return to_emit

    def update(self, exists: bool, obj: BaseEpisode) -> None:
        if exists:
            self._missing = self._update_state(obj, to_populate=self._present, to_emit=self._missing)
        else:
            self._present = self._update_state(obj, to_populate=self._missing, to_emit=self._present)

    def __rich__(self) -> ConsoleRenderable:
        return Group(*(pair.render() for pair in self.pairs))
