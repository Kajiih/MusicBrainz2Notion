"""Utils for musicbrainz2notion library."""

import inspect
import logging
import sys
from enum import StrEnum
from typing import override

from loguru import logger


class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_API_KEY = "MB2NT_NOTION_API_KEY"
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

    @override
    def emit(self, record: logging.LogRecord) -> None:
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


def setup_logging(file_name: str = "app") -> None:
    """Set up logging."""
    # Redirect logging with Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)

    logger.remove()

    logger.add(
        f"logs/{file_name}.log",  # Log to a file
        level="DEBUG",  # Minimum logging level
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="1 week",  # Rotate logs weekly
        compression="zip",  # Compress rotated logs
    )
    logger.add(
        f"logs/{file_name}_color.log",  # Log to a file
        level="DEBUG",  # Minimum logging level
        # format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="1 week",  # Rotate logs weekly
        compression="zip",  # Compress rotated logs
        colorize=True,
    )
    logger.add(
        sys.stdout,  # Log to the console
        level="INFO",  # Minimum logging level for the console
        # format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
        format="<level>{message}</level>",
    )
