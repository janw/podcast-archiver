from __future__ import annotations

import logging
import logging.config
from typing import Any

from rich import get_console
from rich import print as _print
from rich.logging import RichHandler

logger = logging.getLogger("podcast_archiver")


def rprint(*objects: Any, sep: str = " ", end: str = "\n", **kwargs: Any) -> None:
    if logger.level == logging.NOTSET or logger.level >= logging.WARNING:
        _print(*objects, sep=sep, end=end, **kwargs)
        return
    logger.info(objects[0].strip(), *objects[1:])


def configure_logging(verbosity: int) -> None:
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                log_time_format="[%X]",
                markup=True,
                rich_tracebacks=get_console().is_terminal,
                tracebacks_suppress=[
                    "click",
                ],
                tracebacks_show_locals=True,
            )
        ],
    )
    logger.setLevel(level)
    logger.debug("Running in debug mode.")
