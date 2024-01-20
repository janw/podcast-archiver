import pathlib
from os import PathLike
from typing import Any, cast

import rich_click as click
from click.core import Context, Parameter

from podcast_archiver import __version__ as version
from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import DEFAULT_SETTINGS, Settings
from podcast_archiver.console import console
from podcast_archiver.constants import ENVVAR_PREFIX, PROG_NAME
from podcast_archiver.exceptions import InvalidSettings
from podcast_archiver.logging import configure_logging

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.OPTIONS_PANEL_TITLE = "Miscellaneous Options"
click.rich_click.OPTION_GROUPS = {
    PROG_NAME: [
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
            "name": "Processing parameters",
            "options": [
                "--filename-template",
                "--update",
                "--slugify",
                "--max-episodes",
                "--date-prefix",
            ],
        },
    ]
}


class ConfigPath(click.Path):
    def __init__(self) -> None:
        return super().__init__(
            exists=True,
            readable=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            path_type=pathlib.Path,
        )

    def convert(  # type: ignore[override]
        self, value: str | PathLike[str], param: Parameter | None, ctx: Context | None
    ) -> str | bytes | PathLike[str] | None:
        if (
            ctx
            and param
            and isinstance(value, pathlib.Path)
            and value == param.get_default(ctx, call=True)
            and not value.exists()
        ):
            try:
                value.parent.mkdir(exist_ok=True, parents=True)
                with value.open("w") as fp:
                    Settings.generate_default_config(file=fp)
            except (OSError, FileNotFoundError):
                return None

        filepath = cast(pathlib.Path, super().convert(value, param, ctx))
        if not ctx or ctx.resilient_parsing:
            return filepath

        try:
            ctx.default_map = ctx.default_map or {}
            settings = Settings.load_from_yaml(filepath)
            ctx.default_map.update(settings.model_dump(exclude_unset=True, exclude_none=True, by_alias=True))
        except InvalidSettings as exc:
            self.fail(f"{self.name.title()} {click.format_filename(filepath)!r} is invalid: {exc}", param, ctx)

        return filepath


def generate_default_config(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    Settings.generate_default_config()
    ctx.exit()


@click.command(
    context_settings={
        "auto_envvar_prefix": ENVVAR_PREFIX,
    },
    help="Archive all of your favorite podcasts",
)
@click.help_option("-h", "--help")
@click.option(
    "-f",
    "--feed",
    multiple=True,
    show_envvar=True,
    help=Settings.model_fields["feeds"].description + " Use repeatedly for multiple feeds.",  # type: ignore[operator]
)
@click.option(
    "-o",
    "--opml",
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
    default=DEFAULT_SETTINGS.archive_directory,
    show_envvar=True,
    help=Settings.model_fields["archive_directory"].description,
)
@click.option(
    "-F",
    "--filename-template",
    type=str,
    show_default=True,
    required=False,
    default=DEFAULT_SETTINGS.filename_template,
    show_envvar=True,
    help=Settings.model_fields["filename_template"].description,
)
@click.option(
    "-u",
    "--update",
    type=bool,
    default=DEFAULT_SETTINGS.update_archive,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["update_archive"].description,
)
@click.option(
    "-q",
    "--quiet",
    type=bool,
    default=DEFAULT_SETTINGS.quiet,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["quiet"].description,
)
@click.option(
    "--debug-partial",
    type=bool,
    default=DEFAULT_SETTINGS.debug_partial,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["debug_partial"].description,
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    show_envvar=True,
    default=DEFAULT_SETTINGS.verbose,
    help=Settings.model_fields["verbose"].description,
)
@click.option(
    "-S",
    "--slugify",
    type=bool,
    default=DEFAULT_SETTINGS.slugify_paths,
    is_flag=True,
    show_envvar=True,
    help=Settings.model_fields["slugify_paths"].description,
)
@click.option(
    "-m",
    "--max-episodes",
    type=int,
    default=DEFAULT_SETTINGS.maximum_episode_count,
    help=Settings.model_fields["maximum_episode_count"].description,
)
@click.version_option(
    version,
    "-V",
    "--version",
    prog_name=PROG_NAME,
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
    type=ConfigPath(),
    expose_value=False,
    default=pathlib.Path(click.get_app_dir(PROG_NAME)) / "config.yaml",
    show_default=False,
    is_eager=True,
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
    main.main(prog_name=PROG_NAME)
