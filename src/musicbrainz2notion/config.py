"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""

from pathlib import Path

from musicbrainz2notion.__about__ import _PROJECT_ROOT
from musicbrainz2notion.musicbrainz_utils import ReleaseStatus, ReleaseType

MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

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


UPDATE_CANONICAL_DATA = False
DATA_DIR = _PROJECT_ROOT / "data"

# CANONICAL_RELEASE_REDIRECT_PATH = DATA_DIR / "canonical_release_redirect.csv"
# CANONICAL_RECORDING_REDIRECT_PATH = DATA_DIR / "canonical_recording_redirect.csv"


ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True

TEST_URL = "https://images.fanart.tv/fanart/superbus-50576f8295220.jpeg"
# TODO: Implement thumbnails and cover fetching

EMPTY_AREA_PLACEHOLDER = "Unknown"  # Used when no area is found for an artist; use space " " for an un-assignable value in Notion
EMPTY_LANGUAGE_PLACEHOLDER = (
    "Unknown"  # Same as EMPTY_AREA_PLACEHOLDER; used when no language is found for a release
)
