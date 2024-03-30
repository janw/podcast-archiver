from __future__ import annotations

import pathlib
import textwrap
from contextlib import suppress
from datetime import datetime
from os import PathLike, getenv
from typing import Any, cast

import click
from click.core import Parameter
from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, DirectoryPath, FilePath, ValidationError
from pydantic_core import to_json
from typing_extensions import Annotated
from yaml import YAMLError, safe_load

from podcast_archiver import __version__ as version
from podcast_archiver import constants
from podcast_archiver.console import console
from podcast_archiver.exceptions import InvalidSettings


def get_default_config_path() -> pathlib.Path | None:
    if getenv("TESTING", "0").lower() in ("1", "true"):
        return None
    return pathlib.Path(click.get_app_dir(constants.PROG_NAME)) / "config.yaml"  # pragma: no cover


def generate_default_config(ctx: click.Context) -> str:
    now = datetime.now().replace(microsecond=0).astimezone()
    wrapper = textwrap.TextWrapper(width=80, initial_indent="# ", subsequent_indent="#   ")

    lines = [
        f"## {constants.PROG_NAME.title()} configuration",
        f"## Generated with {constants.PROG_NAME} {version} at {now}",
    ]

    for cli_param in cast(list[Parameter | click.Option], ctx.command.params):
        if (name := cli_param.name) in ("help", "config", "config_generate", "version"):
            continue

        param_value = cli_param.get_default(ctx, call=True)
        param_help = ""
        if _help := getattr(cli_param, "help", ""):
            param_help = f": {_help}"
        lines += [
            "",
            *wrapper.wrap(f"Field '{name}'{param_help}"),
            "#",
            *wrapper.wrap(f"Equivalent command line option: {', '.join(cli_param.opts)}"),
            "#",
            f"{name}: {to_json(param_value).decode()}",
        ]

    return "\n".join(lines).strip()


def print_default_config(ctx: click.Context, param: click.Parameter, value: bool = True) -> None:
    if not value or ctx.resilient_parsing:
        return
    console.print(generate_default_config(ctx), highlight=False)
    ctx.exit()


def write_default_config(
    ctx: click.Context, param: click.Parameter, value: str | PathLike[str]
) -> str | PathLike[str] | None:
    if not value or ctx.resilient_parsing:
        return None
    if not isinstance(value, pathlib.Path) or value != param.get_default(ctx, call=True) or value.exists():
        return None

    with suppress(OSError, FileNotFoundError):
        value.parent.mkdir(exist_ok=True, parents=True)
        with value.open("w") as fh:
            fh.write(generate_default_config(ctx) + "\n")

    return value


def expanduser(v: pathlib.Path) -> pathlib.Path:
    if isinstance(v, str):
        v = pathlib.Path(v)
    return v.expanduser()


UserExpandedDir = Annotated[DirectoryPath, BeforeValidator(expanduser)]
UserExpandedFile = Annotated[FilePath, BeforeValidator(expanduser)]


class Settings(BaseModel):
    feeds: list[str | AnyHttpUrl] = []
    opml_files: list[UserExpandedFile] = []
    archive_directory: UserExpandedDir

    update_archive: bool
    write_info_json: bool
    maximum_episode_count: int
    filename_template: str
    slugify_paths: bool

    quiet: bool
    verbose: int
    concurrency: int
    debug_partial: bool

    @classmethod
    def load_and_merge_settings(cls, config_file: pathlib.Path, **overrides: Any) -> Settings:
        content = None
        if config_file and config_file.exists():
            try:
                with config_file.open("r") as fileh:
                    content = safe_load(fileh)
            except YAMLError as exc:
                raise InvalidSettings(constants.DEFAULT_CONFIG_FILE_ERROR_MESSAGE) from exc
        if content is None:
            content = {}
        if not isinstance(content, dict):
            raise InvalidSettings(constants.DEFAULT_CONFIG_FILE_ERROR_MESSAGE)

        content.update({k: v for k, v in overrides.items() if not isinstance(v, list | tuple) or len(v) > 0})
        try:
            return cls.model_validate(content)
        except ValidationError as exc:
            raise InvalidSettings(errors=exc.errors()) from exc
