"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""

from typing import Literal

import attrs

from musicbrainz2notion.musicbrainz_utils import MBID, ReleaseStatus, ReleaseType

REQUEST_TIMEOUT = 10

RELEASE_TYPE_FILTER = [
    ReleaseType.ALBUM,
    ReleaseType.EP,
]  # Only releases of those types will be added to Notion. Let empty to include all types.
RELEASE_SECONDARY_TYPE_EXCLUDE = [
    ReleaseType.COMPILATION,
    ReleaseType.LIVE,
]  # Secondary types to exclude from the data.
RELEASE_STATUS_FILTER = [ReleaseStatus.OFFICIAL]

MIN_NB_TAGS = 3

ARTIST_PAGE_ICON = "🧑‍🎤"
RELEASE_PAGE_ICON = "💽"
RECORDING_PAGE_ICON = "🎼"

ARTIST_UPDATE_MBIDS = []
FORCE_UPDATE_CANONICAL_DATA = False

# CANONICAL_RELEASE_REDIRECT_PATH = DATA_DIR / "canonical_release_redirect.csv"
# CANONICAL_RECORDING_REDIRECT_PATH = DATA_DIR / "canonical_recording_redirect.csv"

THUMBNAIL_SIZE = 500  # 250, 500, 1200
ADD_TRACK_THUMBNAIL = True

EMPTY_TYPE_PLACEHOLDER = "Unknown"  # Used when no type is found for a artist or release; use space " " for an un-assignable value in Notion
EMPTY_AREA_PLACEHOLDER = (
    "Unknown"  # Same as EMPTY_TYPE_PLACEHOLDER; used when no area is found for an artist
)
EMPTY_LANGUAGE_PLACEHOLDER = (
    "Unknown"  # Same as EMPTY_TYPE_PLACEHOLDER; used when no language is found for a release
)


@attrs.frozen(kw_only=True, cache_hash=True)
class Settings:
    """Settings for MusicBrainz2notion."""

    artists_to_update: tuple[MBID, ...] = ()

    # === Database IDs === #
    artist_db_id: str
    release_db_id: str
    track_db_id: str

    # === Database IDs === #
    release_type_filter: tuple[ReleaseType, ...] = (ReleaseType.ALBUM, ReleaseType.EP)
    release_status_filter: tuple[ReleaseStatus, ...] = (ReleaseStatus.OFFICIAL,)
    release_secondary_type_exclude: tuple[ReleaseType, ...] = (
        ReleaseType.COMPILATION,
        ReleaseType.LIVE,
    )

    # === Icon emojis === #
    artist_icon: str = "🧑‍🎤"
    release_icon: str = "💽"
    track_icon: str = "🎼"

    # === Placeholders === #
    empty_type_placeholder: str = "Unknown"
    empty_area_placeholder: str = "Unknown"
    empty_language_placeholder: str = "Unknown"

    # === Others === #
    min_nb_tags: int = 3
    thumbnail_size: int = 500
    # thumbnail_size: Literal[250, 500, 1200] = 500
    add_track_thumbnail: bool = True
    force_update_canonical_data: bool = False
    request_timeout: int = 10
