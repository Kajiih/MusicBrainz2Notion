"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""
from musicbrainz2notion.musicbrainz_utils import ReleaseStatus, ReleaseType

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
