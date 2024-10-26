from __future__ import annotations

import logging
import logging.config
import sys
from os import environ
from typing import Any, Generator, Iterable

from rich import print as _print
from rich.logging import RichHandler
from rich.text import Text
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logger = logging.getLogger("podcast_archiver")


_REDIRECT_VIA_TQDM: bool = False
_REDIRECT_VIA_LOGGING: bool = False


def rprint(msg: str, **kwargs: Any) -> None:
    if not _REDIRECT_VIA_TQDM and not _REDIRECT_VIA_LOGGING:
        _print(msg, **kwargs)
        return

    text = Text.from_markup(msg.strip()).plain.strip()
    logger.info(text)


def wrapped_tqdm(iterable: Iterable[bytes], desc: str, total: int) -> Generator[bytes, None, None]:
    if _REDIRECT_VIA_LOGGING:
        yield from iterable
        return

    with (
        logging_redirect_tqdm(),
        tqdm(desc=desc, total=total, unit_scale=True, unit="B") as progress,
    ):
        global _REDIRECT_VIA_TQDM
        _REDIRECT_VIA_TQDM = True
        try:
            for chunk in iterable:
                progress.update(len(chunk))
                yield chunk
        finally:
            _REDIRECT_VIA_TQDM = False


def is_interactive() -> bool:
    return sys.stdout.isatty() and environ.get("TERM", "").lower() not in ("dumb", "unknown")


def configure_level(verbosity: int, quiet: bool) -> int:
    global _REDIRECT_VIA_LOGGING
    interactive = is_interactive()
    if not interactive or quiet or verbosity > 0:
        _REDIRECT_VIA_LOGGING = True

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
