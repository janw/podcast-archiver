from __future__ import annotations

import logging
import logging.config
import sys
from os import environ
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

from podcast_archiver.console import console

if TYPE_CHECKING:
    from rich.console import RenderableType

logger = logging.getLogger("podcast_archiver")

plain_console = Console(
    color_system=None,
    no_color=True,
    width=999999,
    highlighter=NullHighlighter(),
)

REDIRECT_VIA_LOGGING: bool = False


def _make_plain(msg: RenderableType) -> str:
    with plain_console.capture() as capture:
        plain_console.print(msg, no_wrap=True)
    return capture.get().rstrip("\n")


def rprint(msg: RenderableType, style: str | None = None, new_line_start: bool = True, **kwargs: Any) -> None:
    if not REDIRECT_VIA_LOGGING:
        console.print(msg, style=style, new_line_start=new_line_start, **kwargs)
        return

    log = logger.info
    if style == "error":
        log = logger.error
    elif style == "warning":
        log = logger.warning

    for plain in _make_plain(msg).splitlines():
        if plain:
            log(plain)


def is_interactive() -> bool:
    return (sys.stdout.isatty() and environ.get("TERM", "").lower() not in ("dumb", "unknown")) or environ.get(
        "FORCE_INTERACTIVE", ""
    ) == "1"


def configure_level(verbosity: int, quiet: bool) -> int:
    global REDIRECT_VIA_LOGGING
    interactive = is_interactive()
    if not interactive or quiet or verbosity > 0:
        REDIRECT_VIA_LOGGING = True

    if verbosity > 1 and not quiet:
        return logging.DEBUG
    elif (verbosity == 1 or not interactive) and not quiet:
        return logging.INFO
    else:
        return logging.ERROR


def configure_logging(verbosity: int, quiet: bool) -> None:
    level = configure_level(verbosity, quiet)
    handlers: list[logging.Handler] | None = None
    logformat: str = "%(asctime)s %(name)-16s %(levelname)-5s %(message)s"

    if is_interactive():
        logformat = "%(message)s"
        handlers = [
            RichHandler(
                markup=True,
                rich_tracebacks=verbosity > 1,
                tracebacks_suppress=[
                    "click",
                ],
                tracebacks_show_locals=True,
            )
        ]

    logging.basicConfig(
        level=logging.ERROR,
        format=logformat,
        datefmt="[%Y-%m-%d %H:%M:%S]",
        handlers=handlers,
    )
    logger.setLevel(level)
    logger.debug("Running in debug mode.")
