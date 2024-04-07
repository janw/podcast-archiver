from __future__ import annotations

import os
import pathlib
import stat
from os import getenv
from typing import TYPE_CHECKING, Any

import rich_click as click

from podcast_archiver import __version__ as version
from podcast_archiver import constants
from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import Settings
from podcast_archiver.console import console
from podcast_archiver.exceptions import InvalidSettings
from podcast_archiver.logging import configure_logging

if TYPE_CHECKING:
    from click.shell_completion import CompletionItem


click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.OPTIONS_PANEL_TITLE = "Miscellaneous Options"
click.rich_click.OPTION_GROUPS = {
    constants.PROG_NAME: [
        {
            "name": "Basic parameters",
            "options": [
                "--feed",
                "--opml",
                "--dir",
                "--config",
            ],
        },
        {
            "name": "Output parameters",
            "options": [
                "--filename-template",
                "--write-info-json",
                "--slugify",
            ],
        },
        {
            "name": "Processing parameters",
            "options": [
                "--update",
                "--max-episodes",
            ],
        },
    ]
}


class ConfigFile(click.ParamType):
    name = "file"

    def _check_existence(self, value: pathlib.Path, param: click.Parameter | None, ctx: click.Context | None) -> None:
        try:
            st = value.stat()
        except OSError:
            if value == get_default_config_path():
                value.parent.mkdir(exist_ok=True, parents=True)
                with value.open("w") as fp:
                    Settings.generate_default_config(file=fp)
                return

            self.fail(f"{self.name.title()} {click.format_filename(value)!r} does not exist.", param, ctx)

        if not stat.S_ISREG(st.st_mode):
            self.fail(f"{self.name.title()} {click.format_filename(value)!r} is not a file.", param, ctx)

        if not os.access(value, os.R_OK):
            self.fail(f"{self.name.title()} {click.format_filename(value)!r} is not readable.", param, ctx)

    def convert(
        self, value: str | pathlib.Path, param: click.Parameter | None, ctx: click.Context | None
    ) -> pathlib.Path:
        if isinstance(value, str):
            value = pathlib.Path(value)
        value = value.resolve()
        self._check_existence(value, param, ctx)

        if ctx:
            try:
                settings = Settings.load_from_yaml(value)
                ctx.default_map = settings.model_dump(exclude_unset=True, exclude_none=True)
            except InvalidSettings as exc:
                self.fail(f"{self.name.title()} {click.format_filename(value)!r} is invalid: {exc}", param, ctx)
        return value

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        from click.shell_completion import CompletionItem

        return [CompletionItem(incomplete, type="file")]


def get_default_config_path() -> pathlib.Path | None:
    if getenv("TESTING", "0").lower() in ("1", "true"):
        return None
    return (pathlib.Path(click.get_app_dir(constants.PROG_NAME)) / "config.yaml").resolve()  # pragma: no cover


def generate_default_config(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    Settings.generate_default_config()
    ctx.exit()


@click.command(
    context_settings={
        "auto_envvar_prefix": constants.ENVVAR_PREFIX,
    },
    help="Archive all of your favorite podcasts",
)
@click.help_option("-h", "--help")
@click.option(
    "-f",
    "--feed",
    "feeds",
    multiple=True,
    show_envvar=True,
    help=Settings.model_fields["feeds"].description + " Use repeatedly for multiple feeds.",  # type: ignore[operator]
)
@click.option(
    "-o",
    "--opml",
    "opml_files",
    type=click.Path(
        exists=True,
        readable=True,
        dir_okay=False,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    multiple=True,
    show_envvar=True,
    help=(
        Settings.model_fields["opml_files"].description  # type: ignore[operator]
        + " Use repeatedly for multiple files."
    ),
)
@click.option(
    "-d",
    "--dir",
    "archive_directory",
    type=click.Path(
        exists=False,
        writable=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    show_default=True,
    required=False,
    default=pathlib.Path("."),
    show_envvar=True,
    help=Settings.model_fields["archive_directory"].description,
)
@click.option(
    "-F",
    "--filename-template",
    type=str,
    show_default=True,
    required=False,
    default=constants.DEFAULT_FILENAME_TEMPLATE,
    show_envvar=True,
    help=Settings.model_fields["filename_template"].description,
)
@click.option(
    "-u",
    "--update",
    "update_archive",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["update_archive"].description,
)
@click.option(
    "--write-info-json",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["write_info_json"].description,
)
@click.option(
    "-q",
    "--quiet",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["quiet"].description,
)
@click.option(
    "-C",
    "--concurrency",
    type=int,
    default=constants.DEFAULT_CONCURRENCY,
    show_envvar=True,
    help=Settings.model_fields["concurrency"].description,
)
@click.option(
    "--debug-partial",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["debug_partial"].description,
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    show_envvar=True,
    help=Settings.model_fields["verbose"].description,
)
@click.option(
    "-S",
    "--slugify",
    "slugify_paths",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["slugify_paths"].description,
)
@click.option(
    "-m",
    "--max-episodes",
    "maximum_episode_count",
    type=int,
    default=0,
    help=Settings.model_fields["maximum_episode_count"].description,
)
@click.version_option(
    version,
    "-V",
    "--version",
    prog_name=constants.PROG_NAME,
)
@click.option(
    "--config-generate",
    type=bool,
    expose_value=False,
    is_flag=True,
    is_eager=True,
    callback=generate_default_config,
    help="Emit an example YAML config file to stdout and exit.",
)
@click.option(
    "-c",
    "--config",
    "config_path",
    type=ConfigFile(),
    default=get_default_config_path,
    show_default=False,
    is_eager=True,
    envvar=constants.ENVVAR_PREFIX + "_CONFIG",
    show_envvar=True,
    help="Path to a config file. Command line arguments will take precedence.",
)
@click.pass_context
def main(ctx: click.RichContext, /, **kwargs: Any) -> int:
    configure_logging(kwargs["verbose"])
    console.quiet = kwargs["quiet"] or kwargs["verbose"] > 1
    try:
        settings = Settings.load_from_dict(kwargs)

        # Replicate click's `no_args_is_help` behavior but only when config file does not contain feeds/OPMLs
        if not (settings.feeds or settings.opml_files):
            click.echo(ctx.command.get_help(ctx))
            return 0

        pa = PodcastArchiver(settings=settings)
        pa.register_cleanup(ctx)
        pa.run()
    except InvalidSettings as exc:
        raise click.BadParameter(f"Invalid settings: {exc}") from exc
    except KeyboardInterrupt as exc:
        raise click.Abort("Interrupted by user") from exc
    except FileNotFoundError as exc:
        raise click.Abort(exc) from exc
    return 0


if __name__ == "__main__":
    main.main(prog_name=constants.PROG_NAME)
