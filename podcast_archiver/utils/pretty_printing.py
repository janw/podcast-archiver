from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from podcast_archiver.logging import out

if TYPE_CHECKING:
    from types import TracebackType


T = TypeVar("T")


@dataclass
class _ValPair(Generic[T]):
    prefix: str
    first: T | None = None
    last: T | None = None

    def populate(self, obj: T) -> None:
        if not self.first:
            self.first = obj
        else:
            self.last = obj

    def emit(self) -> str | None:
        msg = None
        if self.first and self.last:
            msg = f"{self.prefix}  {self.first} through {self.last}"
        elif self.first:
            msg = f"{self.prefix}  {self.first}"

        self.first = None
        self.last = None
        return msg


class PrettyPrintRange(Generic[T]):
    _existing: _ValPair[T]
    _missing: _ValPair[T]
    _last_populated: _ValPair[T]

    _type: type[T]

    def __init__(self, range_type: type[T]) -> None:
        self._existing = _ValPair(prefix="✔ Exists: ")
        self._missing = self._last_populated = _ValPair(prefix="✘ Missing:")
        self._type = range_type

    def __enter__(self) -> PrettyPrintRange[T]:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if msg := self._last_populated.emit():
            out.info(msg)

    def _update_state(self, obj: T, to_populate: _ValPair[T], to_emit: _ValPair[T]) -> None:
        self._last_populated = to_populate
        to_populate.populate(obj)
        if msg := to_emit.emit():
            out.info(msg)

    def update(self, exists: bool, obj: T) -> None:
        if exists:
            self._update_state(obj, to_populate=self._existing, to_emit=self._missing)
        else:
            self._update_state(obj, to_populate=self._missing, to_emit=self._existing)
