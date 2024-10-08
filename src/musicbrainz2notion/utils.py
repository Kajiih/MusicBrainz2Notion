"""Utils for musicbrainz2notion library."""

import inspect
import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    A logging handler that intercepts logs from the standard logging module and forwards them to Loguru.

    Snippet from https://github.com/Delgan/loguru/tree/master
    """

    def emit(self, record: logging.LogRecord) -> None:  # noqa: PLR6301
        """Forward log records from the standard logging system to Loguru."""
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame = inspect.currentframe()
        depth = 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())