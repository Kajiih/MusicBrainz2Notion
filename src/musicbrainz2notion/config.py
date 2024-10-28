"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""

from enum import IntEnum
from typing import Literal

import attrs
import typed_settings as ts

from musicbrainz2notion.musicbrainz_utils import MBID, ReleaseStatus, ReleaseType


class ThumbnailSize(IntEnum):
    """Thumbnail size for MusicBrainz covers."""

    p250 = 250
    p500 = 500
    p1200 = 1200


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


@attrs.define(
    kw_only=True,
    frozen=True,
    cache_hash=True,
)
class Settings:
    """
    Settings for MusicBrainz2notion.

    Attributes:
        artists_to_update: List of artist MBIDs to update, in addition to those
            marked "To update" in Notion.
        notion_api_key: Notion API key.
        fanart_api_key: Fanart.tv API key.
        artist_db_id: Artist database ID.
        release_db_id: Release database ID.
        track_db_id: Track database ID.
        release_type_filter: List of release types to include in Notion. If
            empty, all types are included.
        release_status_filter: List of release statuses to include in Notion. If
            empty, all statuses are included.
        release_secondary_type_exclude: List of release secondary types to
            exclude from Notion.
        artist_icon: Icon to use for artist pages.
        release_icon: Icon to use for release pages.
        track_icon: Icon to use for track pages.
        empty_type_placeholder: Placeholder to use when no type is found for a
            artist or release. Use " " for an un-assignable value in Notion.
        empty_area_placeholder: Placeholder to use when no area is found for an
            artist. Use " " for an un-assignable value in Notion.
        empty_language_placeholder: Placeholder to use when no language is
            found for a release. Use " " for an un-assignable value in Notion.
        min_nb_tags: Minimum number of tags to try to add to an entity, starting
            from the most voted ones. . If several tags have the same vote
            counts, they will all be added, maybe resulting in more than
            `min_nb_tags` tags.
        thumbnail_size: Size of the thumbnail to use for MusicBrainz covers.
        add_track_thumbnail: Whether to add a thumbnail to tracks.
        request_timeout: Timeout for http requests.
    """

    artists_to_update: tuple[str, ...] = ()

    # === API keys === #
    notion_api_key: str = ""
    fanart_api_key: str | None = None

    # === Database IDs === #
    artist_db_id: str = ""
    release_db_id: str = ""
    track_db_id: str = ""

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
    thumbnail_size: Literal[250, 500, 1200] = 500
    # thumbnail_size: ThumbnailSize = ThumbnailSize.p500
    add_track_thumbnail: bool = True
    force_update_canonical_data: bool = False
    request_timeout: int = 10
