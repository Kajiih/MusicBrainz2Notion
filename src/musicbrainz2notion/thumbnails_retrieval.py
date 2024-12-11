"""Tools to fetch thumbnails for database entities."""

from __future__ import annotations

import operator
import os
import urllib.parse

import dotenv
import requests
from loguru import logger

from musicbrainz2notion.config import global_settings
from musicbrainz2notion.environment import EnvironmentVar
from musicbrainz2notion.musicbrainz_utils import MBID, CoverSize, EntityType, MBDataDict

dotenv.load_dotenv()
FANART_API_KEY = os.getenv(EnvironmentVar.FANART_API_KEY)

WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
MB_COVER_ART_ARCHIVE_URL = "https://coverartarchive.org/"
WIKIDATA_BASE_IMAGE_URL = "https://commons.wikimedia.org/wiki/Special:FilePath"
BASE_FANART_URL = "https://webservice.fanart.tv/v3/music"


def get_release_group_cover_url(release_group_mbid: MBID, size: CoverSize) -> str | None:
    """
    Retrieve the direct URL for the front cover art of a release group from the Cover Art Archive.

    Args:
        release_group_mbid (MBID): The MusicBrainz ID (MBID) of the release group.
        size (CoverSize): The size of the cover image in pixel.

    Returns:
        str | None: The final direct URL to the cover image, or None if the request fails.
    """
    redirect_url = (
        f"{MB_COVER_ART_ARCHIVE_URL}/{EntityType.RELEASE_GROUP}/{release_group_mbid}/front-{size}"
    )

    # Get the final url
    try:
        response = requests.head(
            redirect_url, allow_redirects=True, timeout=global_settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not get cover art for release group {release_group_mbid}: {e}")
        return None

    return response.url


def extract_wikidata_id(entity_data: MBDataDict) -> str | None:
    """
    Extract the Wikidata ID from the entity's URL relations in the MusicBrainz data.

    Args:
        entity_data (MBDataDict): The MusicBrainz data dictionary containing URL
            relations.

    Returns:
        str | None: The Wikidata ID if found, otherwise None.
    """
    url_relations = entity_data.get("url-relation-list", [])

    # Loop through the URL relations and find the one that corresponds to Wikidata
    for relation in url_relations:
        if relation["type"] == "wikidata":
            wikidata_url = relation["target"]
            return wikidata_url.split("/")[-1]  # Extract the ID (e.g., Q12345)

    return None  # Return None if no Wikidata relation is found


def fetch_wikidata_image_url(wikidata_id: str) -> str | None:
    """
    Fetch the image URL for an entity from Wikidata, using the entity's Wikidata ID.

    Args:
        wikidata_id (str): The Wikidata ID of the entity.

    Returns:
        str | None: The URL of the image associated with the entity, or None if no image is found.
    """
    # Set up the parameters for the Wikidata API query
    params = {
        "action": "wbgetentities",
        "ids": wikidata_id,
        "format": "json",
    }

    try:
        response = requests.get(
            WIKIDATA_API_URL, params=params, timeout=global_settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching Wikidata image for Wikidata ID {wikidata_id}: {e}")
        return None

    data = response.json()

    # Check if there is an image (P18) in the entity claims
    claims = data["entities"][wikidata_id]["claims"]
    if not "P18" in claims:
        logger.info(f"No image found for Wikidata ID {wikidata_id}")
        return None

    # Extract the file name of the image
    image_filename = claims["P18"][0]["mainsnak"]["datavalue"]["value"]

    # Construct the URL for the image
    encoded_filename = urllib.parse.quote(image_filename.replace(" ", "_"))
    image_url = f"{WIKIDATA_BASE_IMAGE_URL}/{encoded_filename}"

    logger.debug(f"Fetched image URL: {image_url}")

    return image_url


def fetch_fanart_tv_artist_thumbnail(mbid: str, fanart_api_key: str) -> str | None:
    """
    Fetch the thumbnail URL for an artist from Fanart.tv using their MusicBrainz ID (MBID).

    This function attempts to retrieve various types of artist images in the following order:
    - 'artistthumb': A thumbnail image of the artist.
    - 'artistbackground': A background image.

    Args:
        mbid (str): The MusicBrainz ID of the artist.
        fanart_api_key (str): The API key for Fanart.tv.

    Returns:
        str | None: The URL of the artist's thumbnail or image if found, otherwise None.
    """
    url = f"{BASE_FANART_URL}/{mbid}"
    headers = {
        "api-key": fanart_api_key,
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=global_settings.REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching artist image from Fanart.tv: {e}")
        return None

    data = response.json()

    # Define a list of image categories to check for, in order of preference
    image_categories = ["artistthumb", "artistbackground"]

    # Loop through the categories and return the first image found
    for category in image_categories:
        images = data.get(category)
        if images is not None:
            # Find the image with the most likes
            most_liked_image = max(images, key=operator.itemgetter("likes"))
            return most_liked_image["url"]

    # No image found in any of the categories
    return None


def fetch_artist_thumbnail(
    artist_data: MBDataDict, fanart_api_key: str | None = None
) -> str | None:
    """
    Fetch the artist thumbnail image URL by first trying Fanart.tv, then falling back to Wikidata.

    Args:
        artist_data (MBDataDict): The dictionary containing artist data from
            MusicBrainz.
        fanart_api_key (str | None): The API key for Fanart.tv. If None, only
            Wikidata will be used.

    Returns:
        str | None: The URL of the artist's thumbnail if found, otherwise None.
    """
    # Get the artist MBID from the MusicBrainz data
    artist_mbid = artist_data["id"]

    # Try to fetch the thumbnail from Fanart.tv
    if fanart_api_key is not None:
        fanart_thumbnail = fetch_fanart_tv_artist_thumbnail(artist_mbid, fanart_api_key)
        if fanart_thumbnail is not None:
            return fanart_thumbnail

    # If no thumbnail found on Fanart.tv, try to fetch it from Wikidata
    wikidata_id = extract_wikidata_id(artist_data)
    if wikidata_id is not None:
        wikidata_thumbnail = fetch_wikidata_image_url(wikidata_id)
        if wikidata_thumbnail is not None:
            return wikidata_thumbnail

    # No thumbnail found on either Fanart.tv or Wikidata
    logger.warning(f"No thumbnail found for artist {artist_mbid}")
    return None
