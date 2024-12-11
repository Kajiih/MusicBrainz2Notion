"""Utils for musicbrainz2notion library."""

from enum import StrEnum


class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_API_KEY = "MB2NT_NOTION_API_KEY"
    ARTIST_DB_ID = "MB2NT_ARTIST_DB_ID"
    RELEASE_DB_ID = "MB2NT_RELEASE_DB_ID"
    TRACK_DB_ID = "MB2NT_TRACK_DB_ID"
    FANART_API_KEY = "MB2NT_FANART_API_KEY"
