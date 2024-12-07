from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest

from podcast_archiver.database import Database, DummyDatabase, get_database

if TYPE_CHECKING:
    from pathlib import Path

    from podcast_archiver.models.episode import Episode


def test_dummy(tmp_path_cd: Path, episode: Episode) -> None:
    db = DummyDatabase("db.db", ignore_existing=False)

    assert not (tmp_path_cd / "db.db").is_file()
    assert not db.exists(episode)
    db.add(episode)
    assert not db.exists(episode)
    db.add(episode)
    assert not db.exists(episode)


def test_add(tmp_path_cd: Path, episode: Episode) -> None:
    db = Database("db.db", ignore_existing=False)

    assert (tmp_path_cd / "db.db").is_file()
    assert not db.exists(episode)
    db.add(episode)
    assert db.exists(episode)
    db.add(episode)
    assert db.exists(episode)


def test_add_ignore_existing(tmp_path_cd: Path, episode: Episode) -> None:
    db = Database("db.db", ignore_existing=True)

    assert not db.exists(episode)
    db.add(episode)
    assert not db.exists(episode)


def test_migrate_idempotency(tmp_path_cd: Path) -> None:
    db = Database("db.db", ignore_existing=False)

    db.migrate()
    db.migrate()

    assert (tmp_path_cd / "db.db").is_file()


@pytest.mark.parametrize(
    "input_path,expected_result_path",
    [
        (None, "podcast-archiver.db"),
        (":memory:", ":memory:"),
    ],
)
def test_get_database(
    tmp_path_cd: Path, input_path: Path | Literal[":memory:"] | None, expected_result_path: str
) -> None:
    db = get_database(input_path)

    assert db.filename == expected_result_path
    assert (tmp_path_cd / "podcast-archiver.db").is_file() == (expected_result_path != ":memory:")
