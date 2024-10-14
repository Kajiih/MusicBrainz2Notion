"""Main module."""

import logging
import os
from enum import StrEnum

import musicbrainzngs
from dotenv import load_dotenv
from loguru import logger

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.musicbrainz_utils import ReleaseStatus, ReleaseType
from musicbrainz2notion.utils import InterceptHandler


# === Enums === #
class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_TOKEN = "NOTION_TOKEN"  # noqa: S105
    ARTIST_DB_ID = "ARTIST_DB_ID"
    RELEASE_DB_ID = "RELEASE_DB_ID"
    RECORDING_DB_ID = "RECORDING_DB_ID"


class ArtistDBProperty(StrEnum):
    """Artist database property keys in Notion."""

    NAME = "Name"  # Database Key
    MBID = "mbid"
    TO_UPDATE = "To update"
    THUMBNAIL = "Thumbnail"
    TYPE = "Type"
    ALIAS = "Alias"
    START_DATE = "Birth/Foundation year"
    GENRES = "Genre(s)"
    AREA = "Area"
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"


class ReleaseDBProperty(StrEnum):
    """Release/release group database property keys in Notion."""

    NAME = "Name"  # Database key  # MB_NAME (ARTIST)
    MBID = "mbid"
    ARTIST = "Artist"
    COVER = "Cover"
    TYPE = "Type"
    FIRST_RELEASE_YEAR = "First release year"
    GENRES = "Genre(s)"
    AREA = "Area"
    LANGUAGE = "Language"  # Taken from iso 639-3
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"


class TrackDBProperty(StrEnum):
    """Track/Recording database property keys in Notion."""

    TITLE = "Title"  # Database key  # MB_NAME (RELEASE)
    MBID = "mbid"
    RELEASE = "Release"
    COVER = "Cover"
    TRACK_NUMBER = "Track number"
    LENGTH = "Length"
    FIRST_RELEASE_YEAR = "First release year"
    GENRES = "Genre(s)"
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"
    TRACK_ARTIST = "Track artist(s)"


# === Constants === #
## User configurable
MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10
ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True
RELEASE_TYPE_FILTER = {ReleaseType.ALBUM, ReleaseType.EP}
RELEASE_STATUS_FILTER = {ReleaseStatus.OFFICIAL}

## Environment variables
load_dotenv()
# TODO: Add CLI for setting environment variables

ARTIST_DB_ID = os.getenv(EnvironmentVar.ARTIST_DB_ID)
RELEASE_DB_ID = os.getenv(EnvironmentVar.RELEASE_DB_ID)
RECORDING_DB_ID = os.getenv(EnvironmentVar.RECORDING_DB_ID)

NOTION_TOKEN = os.getenv(EnvironmentVar.NOTION_TOKEN)

# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")
