from __future__ import annotations

import logging
import logging.config

from rich import get_console
from rich.logging import RichHandler

logger = logging.getLogger("podcast_archiver")


def configure_logging(verbosity: int) -> None:
    if verbosity > 2:
        level = logging.DEBUG
    elif verbosity == 2:
        level = logging.INFO
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
    logger.debug("Running in debug mode.")
