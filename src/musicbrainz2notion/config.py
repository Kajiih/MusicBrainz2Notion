"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""

from pathlib import Path

from musicbrainz2notion.musicbrainz_utils import ReleaseStatus, ReleaseType

MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

RELEASE_TYPE_FILTER = [ReleaseType.ALBUM, ReleaseType.EP]
RELEASE_STATUS_FILTER = [ReleaseStatus.OFFICIAL]

MIN_NB_TAGS = 3

ARTIST_PAGE_ICON = "🧑‍🎤"
RELEASE_PAGE_ICON = "💽"
RECORDING_PAGE_ICON = "🎼"

CANONICAL_RELEASE_REDIRECT_PATH = Path("canonical_release_redirect.csv")

ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True

TEST_URL = "https://images.fanart.tv/fanart/superbus-50576f8295220.jpeg"
# TODO: Implement thumbnails and cover fetching
