from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from podcast_archiver.enums import DownloadResult
from podcast_archiver.logging import rprint

if TYPE_CHECKING:
    from podcast_archiver.models.episode import BaseEpisode


MSG_1 = """\
{prefix} {first}"""

MSG_2 = """\
{prefix} {first}
           {last}"""

MSG_MORE = """\
{prefix} {first}
           [dim]...[/]
           {last}"""


@dataclass(slots=True)
class _ValPair:
    prefix: str
    first: BaseEpisode | None = None
    last: BaseEpisode | None = None
    length: int = 0

    def populate(self, obj: BaseEpisode) -> None:
        if not self.first:
            self.first = obj
        else:
            self.last = obj
        self.length += 1

    def emit(self) -> str | None:
        msg = None
        if self.length == 1:
            msg = MSG_1.format(prefix=self.prefix, first=self.first, last=self.last)
        if self.length == 2:
            msg = MSG_2.format(prefix=self.prefix, first=self.first, last=self.last)
        elif self.length > 2:
            msg = MSG_MORE.format(prefix=self.prefix, first=self.first, last=self.last)

        self.first = None
        self.last = None
        self.length = 0
        return msg


class PrettyPrintEpisodeRange:
    _existing: _ValPair
    _missing: _ValPair
    _last_populated: _ValPair

    __slots__ = ("_existing", "_missing", "_last_populated")

    def __init__(self) -> None:
        self._existing = _ValPair(prefix=f"[success]✔ {DownloadResult.ALREADY_EXISTS}:[/]")
        self._missing = self._last_populated = _ValPair(prefix="[missing]✘ Missing:[/]")

    def __enter__(self) -> PrettyPrintEpisodeRange:
        return self

    def __exit__(self, *args: Any) -> None:
        if msg := self._last_populated.emit():
            rprint(msg)

    def _update_state(self, obj: BaseEpisode, to_populate: _ValPair, to_emit: _ValPair) -> None:
        self._last_populated = to_populate
        to_populate.populate(obj)
        if msg := to_emit.emit():
            rprint(msg)

    def update(self, exists: bool, obj: BaseEpisode) -> None:
        if exists:
            self._update_state(obj, to_populate=self._existing, to_emit=self._missing)
        else:
            self._update_state(obj, to_populate=self._missing, to_emit=self._existing)
