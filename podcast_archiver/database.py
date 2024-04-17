from __future__ import annotations

import sqlite3
from abc import abstractmethod
from contextlib import contextmanager
from threading import Lock
from typing import TYPE_CHECKING, Iterator

from podcast_archiver.logging import logger

if TYPE_CHECKING:
    from podcast_archiver.models import Episode


class BaseDatabase:
    @abstractmethod
    def add(self, episode: Episode) -> None:
        pass  # pragma: no cover

    @abstractmethod
    def exists(self, episode: Episode) -> bool:
        pass  # pragma: no cover


class DummyDatabase(BaseDatabase):
    def add(self, episode: Episode) -> None:
        pass

    def exists(self, episode: Episode) -> bool:
        return False


class Database(BaseDatabase):
    filename: str
    ignore_existing: bool

    lock = Lock()

    def __init__(self, filename: str, ignore_existing: bool) -> None:
        self.filename = filename
        self.ignore_existing = ignore_existing
        self.migrate()

    @contextmanager
    def get_conn(self) -> Iterator[sqlite3.Connection]:
        with self.lock, sqlite3.connect(self.filename) as conn:
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

    def add(self, episode: Episode) -> None:
        with self.get_conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO episodes(guid, title) VALUES (?, ?)",
                    (episode.guid, episode.title),
                )
            except sqlite3.IntegrityError:
                logger.debug(f"Episode exists: {episode}")

    def exists(self, episode: Episode) -> bool:
        if self.ignore_existing:
            return False
        with self.get_conn() as conn:
            result = conn.execute(
                "SELECT EXISTS(SELECT 1 FROM episodes WHERE guid = ?)",
                (episode.guid,),
            )
            return bool(result.fetchone()[0])
