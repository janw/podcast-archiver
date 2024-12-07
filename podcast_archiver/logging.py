from __future__ import annotations

import logging
import logging.config
import sys
from os import environ
from typing import TYPE_CHECKING, Any

from rich.logging import RichHandler
from rich.text import Text

from podcast_archiver.console import console

if TYPE_CHECKING:
    from rich.console import RenderableType

logger = logging.getLogger("podcast_archiver")


REDIRECT_VIA_LOGGING: bool = False


def rprint(*msg: RenderableType, **kwargs: Any) -> None:
    if not REDIRECT_VIA_LOGGING:
        console.print(*msg, **kwargs)
        return

    for m in msg:
        if isinstance(m, Text):
            logger.info(m.plain.strip())


def is_interactive() -> bool:
    return sys.stdout.isatty() and environ.get("TERM", "").lower() not in ("dumb", "unknown")


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
