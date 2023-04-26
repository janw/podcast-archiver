from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Union

from pydantic import BaseSettings, DirectoryPath, Field, FilePath, validator
from yaml import safe_load

from podcast_archiver import __version__

if TYPE_CHECKING:
    import argparse


class Settings(BaseSettings):
    class Config:
        env_prefix = "PODCAST_ARCHIVER_"

    feeds: list[str] = Field(
        default_factory=list,
        flags=("-f", "--feed"),
        description=(
            "Provide feed URLs to the archiver. The command line flag can be used repeatedly to input multiple feeds."
        ),
        argparse_action="append",
        argparse_metavar="FEED_URL_OR_FILE",
    )
    opml_files: list[FilePath] = Field(
        default_factory=list,
        flags=("-o", "--opml"),
        description=(
            "Provide an OPML file (as exported by many other podcatchers) containing your feeds. The parameter can be"
            " used multiple times, once for every OPML file."
        ),
        argparse_action="append",
        argparse_metavar="OPML_FILE",
    )
    archive_directory: DirectoryPath = Field(  # noqa: A003
        None,
        flags=("-d", "--dir"),
        description="Set the output directory of the podcast archive.",
    )

    create_subdirectories: bool = Field(
        False,
        flags=("-s", "--subdirs"),
        description="Place downloaded podcasts in separate subdirectories per podcast (named with their title).",
    )
    update_archive: bool = Field(
        False,
        flags=("-u", "--update"),
        description=(
            "Force the archiver to only update the feeds with newly added episodes. As soon as the first old episode"
            " found in the download directory, further downloading is interrupted."
        ),
    )
    verbose: int = Field(
        0,
        flags=("-v", "--verbose"),
        description="Increase the level of verbosity while downloading.",
        argparse_action="count",
    )
    show_progress_bars: bool = Field(
        False,
        flags=("-p", "--progress"),
        description="Show progress bars while downloading episodes.",
    )

    slugify_paths: bool = Field(
        False,
        flags=("-S", "--slugify"),
        description=(
            "Clean all folders and filename of potentially weird characters that might cause trouble with one or"
            " another target filesystem."
        ),
    )

    maximum_episode_count: int = Field(
        0,
        flags=("-m", "--max-episodes"),
        description=(
            "Only download the given number of episodes per podcast feed. Useful if you don't really need the entire"
            " backlog."
        ),
    )

    add_date_prefix: bool = Field(
        False,
        flags=("--date-prefix",),
        description=(
            "Prefix all episodes with an ISO8602 formatted date of when they were published. Useful to ensure"
            " chronological ordering."
        ),
    )

    @validator("archive_directory", pre=True)
    def normalize_archive_directory(cls, v):
        if v is None:
            return Path.cwd()
        return Path(v).expanduser()

    @validator("opml_files", pre=True, each_item=True)
    def normalize_opml_files(cls, v):
        return Path(v).expanduser()

    @classmethod
    def load_from_yaml(cls, path: Union[Path, None]) -> Settings:
        if path and path.is_file():
            with path.open("r") as filep:
                content = safe_load(filep)
            if content:
                return cls.parse_obj(content)
        return cls()

    @classmethod
    def load_and_merge(cls, path: Union[Path, None], args: argparse.Namespace):
        settings = cls.load_from_yaml(path)
        for name, field in settings.__fields__.items():
            if (args_value := getattr(args, name, None)) is None:
                continue

            settings_value = getattr(settings, name)
            if isinstance(settings_value, list) and isinstance(args_value, list):
                setattr(settings, name, settings_value + args_value)
                continue

            if args_value != field.get_default():
                setattr(settings, name, args_value)

        merged_settings = settings.dict(exclude_defaults=True, exclude_unset=True)
        return cls.parse_obj(merged_settings)

    @classmethod
    def generate_example(cls, path: Path) -> str:
        text = ["## Configuration for podcast-archiver"]
        text.append(f"## Generated with version {__version__}\n")
        for name, field in cls.__fields__.items():
            text.extend(
                textwrap.wrap(f"## Field '{name}': {field.field_info.description}\n", subsequent_indent="##   ")
            )
            text.append(f"# {name}: {field.get_default()}\n")

        with path.open("w") as filep:
            filep.write("\n".join(text))
