from __future__ import annotations

from typing import TYPE_CHECKING

from podcast_archiver.database import Database

if TYPE_CHECKING:
    from pathlib import Path

    from podcast_archiver.models.episode import Episode


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
