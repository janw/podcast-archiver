from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rich.table import Table
from rich.text import Text

from podcast_archiver.logging import rprint

if TYPE_CHECKING:
    from rich.console import ConsoleRenderable

    from podcast_archiver.models.episode import BaseEpisode


@dataclass(slots=True)
class _ValPair:
    prefix: str
    style: str
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


class PrettyPrintEpisodeRange:
    _existing: _ValPair
    _missing: _ValPair
    _last_populated: _ValPair
    pairs: list[_ValPair]

    __slots__ = ("_existing", "_missing", "_last_populated", "pairs")

    def __init__(self) -> None:
        self._existing = _ValPair(prefix="✔ Present", style="success")
        self._missing = self._last_populated = _ValPair("✘ Missing", style="missing")
        self.pairs = []

    def __enter__(self) -> PrettyPrintEpisodeRange:
        return self

    def __exit__(self, *args: Any) -> None:
        if emitted := self._last_populated.emit():
            self.pairs.append(emitted)
        rprint(self)

    def _update_state(self, obj: BaseEpisode, to_populate: _ValPair, to_emit: _ValPair) -> _ValPair:
        self._last_populated = to_populate
        to_populate.populate(obj)
        if emitted := to_emit.emit():
            self.pairs.append(emitted)
            return _ValPair(prefix=to_emit.prefix, style=to_emit.style)
        return to_emit

    def update(self, exists: bool, obj: BaseEpisode) -> None:
        if exists:
            self._missing = self._update_state(obj, to_populate=self._existing, to_emit=self._missing)
        else:
            self._existing = self._update_state(obj, to_populate=self._missing, to_emit=self._existing)

    def __rich__(self) -> ConsoleRenderable | str:
        if not self.pairs:
            return ""
        grid = Table.grid()
        grid.add_column()
        grid.add_column()
        grid.add_column()
        for pair in self.pairs:
            grid.add_row(
                Text(pair.prefix, style=pair.style),
                Text("╶┬╴" if pair.length > 1 else "   ", style=pair.style),
                pair.first,
            )
            if pair.length > 2:
                grid.add_row(
                    "",
                    Text(" │ ", style=pair.style),
                    Text("    ︙", style="dim"),
                )
            if pair.length > 1:
                grid.add_row(
                    "",
                    Text(" ╰╴", style=pair.style),
                    pair.last,
                )
            grid.add_row("", "", "")
        return grid
