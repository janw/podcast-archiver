from __future__ import annotations

import logging
import logging.config
from typing import TYPE_CHECKING

from rich.logging import RichHandler

from podcast_archiver.console import console

if TYPE_CHECKING:
    import click

logger = logging.getLogger("podcast_archiver")


def configure_logging(ctx: click.Context, param: click.Parameter, value: int | None) -> int | None:
    if value is None or ctx.resilient_parsing:
        return None

    if value > 2:
        level = logging.DEBUG
    elif value == 2:
        level = logging.INFO
    elif value == 1:
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
                rich_tracebacks=console.is_terminal,
                tracebacks_suppress=[
                    "click",
                ],
                tracebacks_show_locals=True,
            )
        ],
    )
    logger.debug("Running in debug mode.")
    return value
