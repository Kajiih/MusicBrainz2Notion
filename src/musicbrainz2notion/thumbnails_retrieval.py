"""Tools to fetch thumbnails for database entities."""

from __future__ import annotations

from typing import Literal

import requests
from loguru import logger

from musicbrainz2notion.config import REQUEST_TIMEOUT
from musicbrainz2notion.musicbrainz_utils import MBID, EntityType

MB_COVER_ART_ARCHIVE_URL = "https://coverartarchive.org/"


def get_release_group_cover_url(
    release_group_mbid: MBID, size: Literal[250, 500, 1200]
) -> str | None:
    """
    Retrieve the direct URL for the front cover art of a release group from the Cover Art Archive.

    Args:
        release_group_mbid (MBID): The MusicBrainz ID (MBID) of the release group.
        size (Literal[250, 500, 1200]): The size of the cover image in pixel.

    Returns:
        str | None: The final direct URL to the cover image, or None if the request fails.
    """
    redirect_url = (
        f"{MB_COVER_ART_ARCHIVE_URL}/{EntityType.RELEASE_GROUP}/{release_group_mbid}/front-{size}"
    )

    # Get the final url
    try:
        response = requests.head(redirect_url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.warning(f"Could not get cover art for release group {release_group_mbid}")
        return None

    return response.url
