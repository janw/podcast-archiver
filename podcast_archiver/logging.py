from __future__ import annotations

import logging
import logging.config
import sys
from os import environ
from typing import Any, Callable, ClassVar, Generator, Iterable

import click
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logger = logging.getLogger("podcast_archiver")


class OutputManager:
    quiet: bool = False
    verbosity: int = 0
    is_interactive: bool = False

    _redirect_via_tqdm: bool = False
    _redirect_via_logging: bool = True

    _style_header: ClassVar[dict[str, Any]] = {"bold": True, "fg": "bright_magenta"}
    _style_success: ClassVar[dict[str, Any]] = {"fg": "green"}
    _style_warning: ClassVar[dict[str, Any]] = {"fg": "yellow"}
    _style_error: ClassVar[dict[str, Any]] = {"fg": "red"}

    def info(self, msg: str, **kwargs: Any) -> None:
        return self._emit(msg, logger.info)

    def success(self, msg: str) -> None:
        return self._emit(msg, logger.info, **self._style_success)

    def warning(self, msg: str) -> None:
        return self._emit(msg, logger.warning, **self._style_warning)

    def error(self, msg: str) -> None:
        return self._emit(msg, logger.error, **self._style_error)

    def header(self, msg: str) -> None:
        return self._emit("\n" + msg + "\n", logger.info, **self._style_header)

    def _emit(self, msg: str, logfunc: Callable[[str], None], **kwargs: Any) -> None:
        if self._redirect_via_logging:
            return logfunc(msg.strip())

        if self._redirect_via_tqdm:
            return tqdm.write(msg.strip())

        click.echo(click.style(msg, **kwargs))

    def progress_bar(self, iterable: Iterable[bytes], desc: str, total: int) -> Generator[bytes, None, None]:
        if self._redirect_via_logging:
            yield from iterable
            return

        with (
            logging_redirect_tqdm(),
            tqdm(desc=desc, total=total, unit_scale=True, unit="B") as progress,
        ):
            self._redirect_via_tqdm = True
            try:
                for chunk in iterable:
                    progress.update(len(chunk))
                    yield chunk
            finally:
                self._redirect_via_tqdm = False

    def configure(self, verbosity: int, quiet: bool) -> None:
        self.verbosity = verbosity
        self.quiet = quiet
        self.is_interactive = bool(sys.stdout.isatty() and environ.get("TERM", "").lower() not in ("dumb", "unknown"))

        self._configure_redirect()
        self._set_log_level()
        self._configure_logging()

    def _configure_redirect(self) -> None:
        self._redirect_via_logging = not (self.is_interactive and not self.quiet and not self.verbosity > 0)

    def _set_log_level(self) -> None:
        if self.verbosity > 1 and not self.quiet:
            logger.setLevel(logging.DEBUG)
        elif (self.verbosity == 1 or not self.is_interactive) and not self.quiet:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.ERROR)

    def _configure_logging(self) -> None:
        handlers: list[logging.Handler] | None = None
        logformat: str = "%(asctime)s %(name)-16s %(levelname)-7s %(message)s"

        if self.is_interactive:
            from rich.logging import RichHandler

            logformat = "%(message)s"
            handlers = [
                RichHandler(
                    markup=True,
                    rich_tracebacks=self.verbosity > 2,
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


out = OutputManager()
