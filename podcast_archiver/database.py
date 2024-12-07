from __future__ import annotations

import sqlite3
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Iterator, Literal

from podcast_archiver import constants
from podcast_archiver.logging import logger

if TYPE_CHECKING:
    from podcast_archiver.models.episode import BaseEpisode


def adapt_datetime_iso(val: datetime) -> str:
    return val.isoformat()


def convert_datetime_iso(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())


sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("TIMESTAMP", convert_datetime_iso)


@dataclass(frozen=True, slots=True)
class EpisodeInDb:
    length: int | None = None
    published_time: datetime | None = None


class BaseDatabase:
    filename: str
    ignore_existing: bool

    __slots__ = ("filename", "ignore_existing")

    def __init__(self, filename: str, ignore_existing: bool = False) -> None:
        self.filename = filename
        self.ignore_existing = ignore_existing

    @abstractmethod
    def add(self, episode: BaseEpisode) -> None:
        pass  # pragma: no cover

    @abstractmethod
    def exists(self, episode: BaseEpisode) -> EpisodeInDb | None:
        pass  # pragma: no cover


class DummyDatabase(BaseDatabase):
    def add(self, episode: BaseEpisode) -> None:
        pass

    def exists(self, episode: BaseEpisode) -> EpisodeInDb | None:
        return None


class Database(BaseDatabase):
    lock: Lock
    conn: sqlite3.Connection

    __slots__ = ("lock", "conn")

    def __init__(self, filename: str, ignore_existing: bool) -> None:
        super().__init__(filename=filename, ignore_existing=ignore_existing)
        self.lock = Lock()
        self.conn = sqlite3.connect(self.filename, detect_types=sqlite3.PARSE_DECLTYPES)
        self.migrate()

    @contextmanager
    def get_conn(self) -> Iterator[sqlite3.Connection]:
        with self.lock, self.conn as conn:
            conn.row_factory = sqlite3.Row
            yield conn

    def migrate(self) -> None:
        logger.debug(f"Migrating database at {self.filename}")
        with self.get_conn() as conn:
            conn.execute(
                """\
                CREATE TABLE IF NOT EXISTS episodes(
                    guid TEXT UNIQUE NOT NULL,
                    title TEXT
                )"""
            )

        # NOTE: This is is a rudimentary migration system. It's not perfect but it's
        # good enough for now, and does not require additional dependencies.
        self._add_column_if_missing(
            "length",
            "ALTER TABLE episodes ADD COLUMN length UNSIGNED BIG INT",
        )
        self._add_column_if_missing(
            "published_time",
            "ALTER TABLE episodes ADD COLUMN published_time TIMESTAMP",
        )

    def _add_column_if_missing(self, name: str, alter_stmt: str) -> None:
        with self.get_conn() as conn:
            if not self._has_column(conn, name):
                logger.debug(f"Adding missing DB column {name}")
                conn.execute(alter_stmt)

    def _has_column(self, conn: sqlite3.Connection, name: str) -> bool:
        result = conn.execute(
            "SELECT EXISTS(SELECT 1 FROM pragma_table_info('episodes') WHERE name = ?)",
            (name,),
        )
        return bool(result.fetchone()[0])

    def add(self, episode: BaseEpisode) -> None:
        with self.get_conn() as conn:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO episodes(guid, title, length, published_time) VALUES (?, ?, ?, ?)",
                    (
                        episode.guid,
                        episode.title,
                        episode.enclosure.length,
                        episode.published_time,
                    ),
                )
            except sqlite3.DatabaseError as exc:
                logger.debug("Error adding %s to db", episode, exc_info=exc)

    def exists(self, episode: BaseEpisode) -> EpisodeInDb | None:
        if self.ignore_existing:
            return None
        with self.get_conn() as conn:
            result = conn.execute(
                "SELECT length, published_time FROM episodes WHERE guid = ?",
                (episode.guid,),
            )
            match = result.fetchone()
        return EpisodeInDb(**match) if match else None


def get_database(path: Path | Literal[":memory:"] | None, ignore_existing: bool = False) -> Database:
    if path is None:
        db_path = constants.DEFAULT_DATABASE_FILENAME
    elif isinstance(path, Path) and path.is_dir():
        db_path = str(path / constants.DEFAULT_DATABASE_FILENAME)
    else:
        db_path = str(path)

    return Database(filename=db_path, ignore_existing=ignore_existing)
