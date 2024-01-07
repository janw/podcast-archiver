from __future__ import annotations

import pathlib
import textwrap
from datetime import datetime
from typing import IO, TYPE_CHECKING, Any

import pydantic
import rich
from pydantic import BaseModel, BeforeValidator, DirectoryPath, Field, FilePath
from pydantic import ConfigDict as _ConfigDict
from pydantic_core import to_json
from typing_extensions import Annotated
from yaml import YAMLError, safe_load

from podcast_archiver import __version__ as version
from podcast_archiver.constants import PROG_NAME
from podcast_archiver.exceptions import InvalidSettings

if TYPE_CHECKING:
    pass


def defaultcwd(v: pathlib.Path | None) -> pathlib.Path:
    if not v:
        return pathlib.Path.cwd()
    return v


def expanduser(v: pathlib.Path) -> pathlib.Path:
    if isinstance(v, str):
        v = pathlib.Path(v)
    return v.expanduser()


UserExpandedDir = Annotated[DirectoryPath, BeforeValidator(expanduser), BeforeValidator(defaultcwd)]
UserExpandedFile = Annotated[FilePath, BeforeValidator(expanduser)]


class Settings(BaseModel):
    model_config = _ConfigDict(populate_by_name=True)

    feeds: list[str] = Field(
        default_factory=list,
        alias="feed",
        description="Feed URLs to archive.",
    )

    opml_files: list[UserExpandedFile] = Field(
        default_factory=list,
        alias="opml",
        description=(
            "OPML files containing feed URLs to archive. OPML files can be exported from a variety of podcatchers."
        ),
    )

    archive_directory: UserExpandedDir = Field(
        default=None,
        alias="dir",
        description=(
            "Directory to which to download the podcast archive. "
            "If unset, the archive will be created in the current working directory."
        ),
    )

    create_subdirectories: bool = Field(
        default=False,
        alias="subdirs",
        description="Creates one directory per podcast (named with their title) within the archive directory.",
    )

    update_archive: bool = Field(
        default=False,
        alias="update",
        description=(
            "Update the feeds with newly added episodes only. "
            "Adding episodes ends with the first episode already present in the download directory."
        ),
    )

    verbose: int = Field(
        default=0,
        alias="verbose",
        description="Increase the level of verbosity while downloading.",
    )

    show_progress_bars: bool = Field(
        default=False,
        alias="progress",
        description="Show progress bars while downloading episodes.",
    )

    slugify_paths: bool = Field(
        default=False,
        alias="slugify",
        description="Format filenames in the most compatible way, replacing all special characters.",
    )

    maximum_episode_count: int = Field(
        default=0,
        alias="max_episodes",
        description=(
            "Only download the given number of episodes per podcast feed. "
            "Useful if you don't really need the entire backlog."
        ),
    )

    add_date_prefix: bool = Field(
        default=False,
        alias="date_prefix",
        description="Prefix episodes with their publishing date. Useful to ensure chronological ordering.",
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

        if content:
            return cls.load_from_dict(content)
        return cls()  # type: ignore[call-arg]

    @classmethod
    def generate_default_config(cls, file: IO | None = None) -> None:
        now = datetime.now().replace(microsecond=0).astimezone()
        wrapper = textwrap.TextWrapper(width=80, initial_indent="# ", subsequent_indent="#   ")

        lines = [
            f"[bright_black]## {PROG_NAME.title()} configuration",
            f"## Generated with [bold magenta]{PROG_NAME} {version}[/] at [bold magenta]{now}[/]",
        ]
        for name, field in cls.model_fields.items():
            value = field.get_default(call_default_factory=True)
            lines += [
                "",
                *wrapper.wrap(f"Field '{name}': {field.description}"),
                "#",
                *wrapper.wrap(f"Equivalent command line option: --{field.alias}"),
                "#",
                f"[red]{name}[/][white]:[/] [bold blue]{to_json(value).decode()}[/]",
            ]

        rich.print("\n".join(lines).strip(), file=file)


DEFAULT_SETTINGS = Settings()
