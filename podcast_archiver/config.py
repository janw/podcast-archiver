from __future__ import annotations

import pathlib
import sys
import textwrap
from datetime import datetime
from os import getenv
from typing import IO, Any, Text

import pydantic
from pydantic import (
    BaseModel,
    BeforeValidator,
    DirectoryPath,
    Field,
    FilePath,
    NewPath,
)
from pydantic import ConfigDict as _ConfigDict
from pydantic_core import to_json
from typing_extensions import Annotated
from yaml import YAMLError, safe_load

from podcast_archiver import __version__ as version
from podcast_archiver import constants
from podcast_archiver.database import BaseDatabase, Database, DummyDatabase
from podcast_archiver.exceptions import InvalidSettings
from podcast_archiver.models import ALL_FIELD_TITLES_STR


def expanduser(v: pathlib.Path) -> pathlib.Path:
    if isinstance(v, str):
        v = pathlib.Path(v)
    return v.expanduser()


UserExpandedDir = Annotated[DirectoryPath, BeforeValidator(expanduser)]
UserExpandedFile = Annotated[FilePath, BeforeValidator(expanduser)]
UserExpandedPossibleFile = Annotated[FilePath | NewPath, BeforeValidator(expanduser)]


def in_ci() -> bool:
    val = getenv("CI", "").lower()
    return val.lower() in ("true", "1")


class Settings(BaseModel):
    model_config = _ConfigDict(populate_by_name=True)

    feeds: list[str] = Field(
        default_factory=list,
        description="Feed URLs to archive.",
    )

    opml_files: list[UserExpandedFile] = Field(
        default_factory=list,
        description=(
            "OPML files containing feed URLs to archive. OPML files can be exported from a variety of podcatchers."
        ),
    )

    archive_directory: UserExpandedDir = Field(
        default=UserExpandedDir("."),
        description=(
            "Directory to which to download the podcast archive. "
            "By default, the archive will be created in the current working directory  ('.')."
        ),
    )

    update_archive: bool = Field(
        default=False,
        description=(
            "Update the feeds with newly added episodes only. "
            "Adding episodes ends with the first episode already present in the download directory."
        ),
    )

    write_info_json: bool = Field(
        default=False,
        description="Write episode metadata to a .info.json file next to the media file itself.",
    )

    quiet: bool = Field(
        default=False,
        description="Print only minimal progress information. Errors will always be emitted.",
    )

    verbose: int = Field(
        default=0,
        description="Increase the level of verbosity while downloading.",
    )

    slugify_paths: bool = Field(
        default=False,
        description="Format filenames in the most compatible way, replacing all special characters.",
    )

    filename_template: str = Field(
        default=constants.DEFAULT_FILENAME_TEMPLATE,
        description=(
            "Template to be used when generating filenames. Available template variables are: "
            f"{ALL_FIELD_TITLES_STR}, and 'ext' (the filename extension)"
        ),
    )

    maximum_episode_count: int = Field(
        default=0,
        description=(
            "Only download the given number of episodes per podcast feed. "
            "Useful if you don't really need the entire backlog."
        ),
    )

    concurrency: int = Field(
        default=4,
        description="Maximum number of simultaneous downloads.",
    )

    debug_partial: bool = Field(
        default=False,
        description=f"Download only the first {constants.DEBUG_PARTIAL_SIZE} bytes of episodes for debugging purposes.",
    )

    database: UserExpandedPossibleFile | None = Field(
        default=None,
        description=(
            "Location of the database to keep track of downloaded episodes. By default, the database will be created "
            f"as '{constants.DEFAULT_DATABASE_FILENAME}' in the directory of the config file."
        ),
    )
    ignore_database: bool = Field(
        default=False,
        description=(
            "Ignore the episodes database when downloading. This will cause files to be downloaded again, even if they "
            "already exist in the database."
        ),
    )

    config: FilePath | None = Field(
        default=None,
        exclude=True,
    )

    @classmethod
    def load_from_dict(cls, value: dict[str, Any]) -> Settings:
        try:
            return cls.model_validate(value)
        except pydantic.ValidationError as exc:
            raise InvalidSettings(errors=exc.errors()) from exc

    @classmethod
    def load_from_yaml(cls, path: pathlib.Path) -> Settings:
        try:
            with path.open("r") as filep:
                content = safe_load(filep)
        except YAMLError as exc:
            raise InvalidSettings("Not a valid YAML document") from exc

        content = content or {}

        if not isinstance(content, dict):
            raise InvalidSettings("Not a valid YAML document")

        content.update(config=path)
        return cls.load_from_dict(content)

    @classmethod
    def generate_default_config(cls, file: IO[Text] | None = None) -> None:
        now = datetime.now().replace(microsecond=0).astimezone()
        wrapper = textwrap.TextWrapper(width=80, initial_indent="# ", subsequent_indent="#   ")

        lines = [
            f"## {constants.PROG_NAME.title()} configuration",
            f"## Generated with {constants.PROG_NAME} {version} at {now}",
        ]

        for name, field in cls.model_fields.items():
            if name in ("config",):
                continue
            cli_opt = (
                wrapper.wrap(f"Equivalent command line option: --{field.alias.replace('_', '-')}")
                if field.alias
                else []
            )
            value = field.get_default(call_default_factory=True)
            lines += [
                "",
                *wrapper.wrap(f"Field '{name}': {field.description}"),
                "#",
                *cli_opt,
                "#",
                f"{name}: {to_json(value).decode()}",
            ]

        contents = "\n".join(lines).strip() + "\n"
        if not file:
            sys.stdout.write(contents)
        else:
            with file:
                file.write(contents)

    def get_database(self) -> BaseDatabase:
        if getenv("TESTING", "0").lower() in ("1", "true"):
            return DummyDatabase()

        if self.database:
            db_path = str(self.database)
        elif self.config:
            db_path = str(self.config.parent / constants.DEFAULT_DATABASE_FILENAME)
        else:
            db_path = constants.DEFAULT_DATABASE_FILENAME

        return Database(filename=db_path, ignore_existing=self.ignore_database)
