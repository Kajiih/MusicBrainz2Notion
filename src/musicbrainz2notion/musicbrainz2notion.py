"""Main module."""

import logging
import os

import musicbrainzngs
from loguru import logger
from utils import InterceptHandler

# === Constants === #
ARTIST_DB_ID = ""
RELEASE_DB_ID = ""
RECORDING_DB_ID = ""

APP_NAME = "MusicBrainz2Notion"
APP_VERSION = "0.0.1"
APP_CONTACT = "itskajih@gmail.com"

MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

NOTION_TOKEN = os.environ["NOTION_TOKEN"]  # API token, no token_v2 from cookie
# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


musicbrainzngs.set_useragent(APP_NAME, APP_VERSION, APP_CONTACT)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")
