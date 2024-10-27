"""Utils for musicbrainz2notion library."""

import inspect
import logging
from enum import StrEnum

from loguru import logger


class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_API_KEY = "MB2NT_API_KEY"
    ARTIST_DB_ID = "MB2NT_ARTIST_DB_ID"
    RELEASE_DB_ID = "MB2NT_RELEASE_DB_ID"
    TRACK_DB_ID = "MB2NT_TRACK_DB_ID"
    FANART_API_KEY = "MB2NT_FANART_API_KEY"


# %% === Misc === #
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
