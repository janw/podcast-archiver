from __future__ import annotations

import pathlib
from typing import Any

import rich_click as click

from podcast_archiver import __version__ as version
from podcast_archiver import constants
from podcast_archiver.base import PodcastArchiver
from podcast_archiver.config import (
    Settings,
    get_default_config_path,
    print_default_config,
    write_default_config,
)
from podcast_archiver.console import console
from podcast_archiver.constants import ENVVAR_PREFIX, PROG_NAME
from podcast_archiver.exceptions import InvalidFeed, InvalidSettings
from podcast_archiver.logging import configure_logging
from podcast_archiver.models import ALL_FIELD_TITLES_STR

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
    "feeds",
    default=[],
    multiple=True,
    show_envvar=True,
    help="Feed URLs to archive. Use repeatedly for multiple feeds.",
)
@click.option(
    "-o",
    "--opml",
    "opml_files",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    default=[],
    multiple=True,
    show_envvar=True,
    help=(
        "OPML files containing feed URLs to archive. OPML files can be exported from a variety of podcatchers."
        "Use repeatedly for multiple files."
    ),
)
@click.option(
    "-d",
    "--dir",
    "archive_directory",
    type=click.Path(
        exists=True,
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
    help=(
        "Directory to which to download the podcast archive. "
        "By default, the archive will be created in the current working directory ('.')."
    ),
)
@click.option(
    "-F",
    "--filename-template",
    type=str,
    show_default=True,
    required=False,
    default=constants.DEFAULT_FILENAME_TEMPLATE,
    show_envvar=True,
    help=(
        "Template to be used when generating filenames. Available template variables are: "
        f"{ALL_FIELD_TITLES_STR}, and 'ext' (the filename extension)."
    ),
)
@click.option(
    "-u",
    "--update",
    "update_archive",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=(
        "Update the feeds with newly added episodes only. "
        "Adding episodes ends with the first episode already present in the download directory."
    ),
)
@click.option(
    "--write-info-json",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help="Write episode metadata to a .info.json file next to the media file itself.",
)
@click.option(
    "-q",
    "--quiet",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help="Print only minimal progress information. Errors will always be emitted.",
)
@click.option(
    "-C",
    "--concurrency",
    type=int,
    default=constants.DEFAULT_CONCURRENCY,
    show_envvar=True,
    help="Maximum number of simultaneous downloads.",
)
@click.option(
    "--debug-partial",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help=f"Download only the first {constants.DEBUG_PARTIAL_SIZE} bytes of episodes for debugging purposes.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    show_envvar=True,
    is_eager=True,
    callback=configure_logging,
    help="Increase the level of verbosity while downloading.",
)
@click.option(
    "-S",
    "--slugify",
    "slugify_paths",
    type=bool,
    is_flag=True,
    show_envvar=True,
    help="Format filenames in the most compatible way, replacing all special characters.",
)
@click.option(
    "-m",
    "--max-episodes",
    "maximum_episode_count",
    type=int,
    default=0,
    help=(
        "Only download the given number of episodes per podcast feed. "
        "Useful if you don't really need the entire backlog."
    ),
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
    callback=print_default_config,
    help="Emit an example YAML config file to stdout and exit.",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(
        exists=True,
        readable=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    default=get_default_config_path,
    show_default=False,
    show_envvar=True,
    callback=write_default_config,
    help="Path to a config file. Command line arguments will take precedence.",
)
@click.pass_context
def main(ctx: click.RichContext, config: pathlib.Path, **kwargs: Any) -> int:
    try:
        settings = Settings.load_and_merge_settings(config_file=config, **kwargs)
        console.quiet = settings.quiet or settings.verbose > 1
        # Replicate click's `no_args_is_help` behavior but only when config file does not contain feeds/OPMLs
        if not (settings.feeds or settings.opml_files):
            click.echo(ctx.command.get_help(ctx))
            return 0

        pa = PodcastArchiver(settings=settings)
        pa.register_cleanup(ctx)
        pa.run()
    except InvalidFeed as exc:
        raise click.BadParameter(f"Cannot parse feed '{exc.feed}'") from exc
    except InvalidSettings as exc:
        raise click.UsageError(f"Invalid config: {exc}") from exc
    except KeyboardInterrupt as exc:
        raise click.Abort("Interrupted by user") from exc
    except FileNotFoundError as exc:
        raise click.Abort(exc) from exc
    return 0


if __name__ == "__main__":
    main.main(prog_name=PROG_NAME)
