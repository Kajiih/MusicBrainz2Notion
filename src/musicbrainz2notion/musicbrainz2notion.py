"""Main module."""

import logging
import os
from enum import StrEnum

import musicbrainzngs
from dotenv import load_dotenv
from loguru import logger

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.utils import InterceptHandler


# === Enums === #
class EnvVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_TOKEN = "NOTION_TOKEN"  # noqa: S105
    ARTIST_DB_ID = "ARTIST_DB_ID"
    RELEASE_DB_ID = "RELEASE_DB_ID"
    RECORDING_DB_ID = "RECORDING_DB_ID"


# === Constants === #
load_dotenv()
# TODO: Add CLI for setting environment variables

ARTIST_DB_ID = os.getenv(EnvVar.ARTIST_DB_ID)
RELEASE_DB_ID = os.getenv(EnvVar.RELEASE_DB_ID)
RECORDING_DB_ID = os.getenv(EnvVar.RECORDING_DB_ID)

MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

NOTION_TOKEN = os.getenv(EnvVar.NOTION_TOKEN)

# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")
