"""Main module."""

from __future__ import annotations

import logging
import os
from enum import StrEnum
from typing import Any

import musicbrainzngs
import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.database_entities import Artist, Release
from musicbrainz2notion.musicbrainz_utils import (
    MBID,
    CanonicalDataHeader,
    EntityType,
    IncludeOption,
    MBDataField,
    ReleaseStatus,
    ReleaseType,
)
from musicbrainz2notion.utils import InterceptHandler

# === Config === #
MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

RELEASE_TYPE_FILTER = [ReleaseType.ALBUM, ReleaseType.EP]
RELEASE_STATUS_FILTER = [ReleaseStatus.OFFICIAL]

MIN_NB_TAGS = 3

ARTIST_PAGE_ICON = "🧑‍🎤"
RELEASE_PAGE_ICON = "💽"
RECORDING_PAGE_ICON = "🎼"


class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_TOKEN = "NOTION_TOKEN"  # noqa: S105
    ARTIST_DB_ID = "ARTIST_DB_ID"
    RELEASE_DB_ID = "RELEASE_DB_ID"
    RECORDING_DB_ID = "RECORDING_DB_ID"


# %% === Data fetching functions === #
def fetch_artist_data(mbid: str, release_type: list[str] | None = None) -> dict | None:
    """
    Fetch artist data from MusicBrainz for the given artist mbid.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the artist.
        release_type (list[str] | None): List of release types to include in the
            response.
            Defaults to None (no filtering).

    Returns:
        dict | None: The dictionary of artist data from MusicBrainz. None if
            there was an error while fetching the data.
    """
    logger.info(f"Fetching artist data for mbid {mbid}")

    if release_type is None:
        release_type = []

    try:
        result = musicbrainzngs.get_artist_by_id(
            mbid,
            includes=[
                IncludeOption.ALIASES,
                IncludeOption.TAGS,
                IncludeOption.RATINGS,
                # IncludeOption.USER_RATINGS,
            ],
            release_type=release_type,
        )
        artist_data = result[EntityType.ARTIST]

        # logger.info(f"Fetched artist data for {artist_data[MBDataField.NAME]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching artist data from MusicBrainz for {mbid}: {exc}")

        artist_data = None

    return artist_data


def browse_release_groups_by_artist(
    artist_mbid: str,
    release_type: list[str] | None = None,
    browse_limit: int = 100,
) -> list[dict] | None:
    """
    Browse and return a list of all release groups by an artist from MusicBrainz.

    Args:
        artist_mbid (str): The MusicBrainz ID (mbid) of the artist.
        release_type (list[str] | None): List of release types to filter.
            Defaults to None (no filtering).
        browse_limit (int): Maximum number of release groups to retrieve per
            request (max is 100).

    Returns:
        list[dict] | None: A list of release groups from MusicBrainz. None if
            there was an error while fetching the data.
    """
    logger.info(f"Browsing artist's release groups for mbid {artist_mbid}")

    if release_type is None:
        release_type = []
    offset = 0
    page = 1
    release_groups = []
    page_release_groups = []

    try:
        # Continue browsing until we fetch all release groups
        while len(page_release_groups) < browse_limit:
            logger.info(f"Fetching page number {page}")
            result = musicbrainzngs.browse_release_groups(
                artist=artist_mbid,
                includes=[IncludeOption.RATINGS],
                release_type=release_type,
                limit=browse_limit,
                offset=offset,
            )
            page_release_groups = result.get("release-group-list", [])
            release_groups.extend(release_groups)
            offset += browse_limit
            page += 1

        logger.info(f"Fetched {len(release_groups)} release groups for mbid {artist_mbid}")
    except musicbrainzngs.WebServiceError as exc:
        logger.error(
            f"Error fetching release groups from MusicBrainz for mbid {artist_mbid}: {exc}"
        )

        release_groups = None

    return release_groups


def fetch_release_data(
    mbid: str,
    release_type: list[str] | None = None,
    release_status: list[str] | None = None,
) -> dict | None:
    """
    Fetch release data from MusicBrainz for a given release MBID, including recordings.

    The function retrieves additional information about the release, such as
    tags, artist credits, and recordings associated with the release.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the release.
        release_type (list[str] | None): A list of release types to filter.
            Defaults to None (no filtering).
        release_status (list[str] | None): A list of release statuses to filter.
            Defaults to None (no filtering).

    Returns:
        dict | None: The release data from MusicBrainz. Returns None if there
            was an error while fetching the data.
    """
    logger.info(f"Fetching release data for mbid {mbid}")

    if release_type is None:
        release_type = []
    if release_status is None:
        release_status = []

    try:
        release_data = musicbrainzngs.get_release_by_id(
            mbid,
            includes=[
                IncludeOption.TAGS,
                IncludeOption.RECORDINGS,
                IncludeOption.ARTIST_CREDITS,
            ],
            release_type=release_type,
            release_status=release_status,
        )

        logger.info(f"Fetched release data for {release_data[MBDataField.NAME]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching release data from MusicBrainz for {mbid}: {exc}")

        release_data = None

    return release_data


def fetch_recordings_data(mbid: str) -> dict | None:
    """
    Fetch recording data from MusicBrainz for a given recording MBID.

    The function retrieves additional information about the recording, such as
    artist credits, tags, and rating.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the recording.

    Returns:
        dict | None: The recording data from MusicBrainz. Returns None if there
            was an error while fetching the data.
    """
    logger.info(f"Fetching recording data for mbid {mbid}")

    try:
        recording_data = musicbrainzngs.get_recording_by_id(
            mbid,
            includes=[
                IncludeOption.ARTIST_CREDITS,
                IncludeOption.TAGS,
                IncludeOption.RATINGS,
            ],
        )

        logger.info(f"Fetched recording data for {recording_data[MBDataField.TITLE]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching recording data from MusicBrainz for {mbid}: {exc}")
        recording_data = None

    return recording_data


def get_canonical_releases_map(
    release_group_mbids: set[str], canonical_release_df: pd.DataFrame
) -> dict[MBID, MBID]:
    """
    Return a map of release group MBIDs to their canonical release MBIDs.

    Args:
        release_group_mbids (set[str]): A set of release group MBIDs to map.
        canonical_release_df (pd.DataFrame): The DataFrame containing the
            canonical release mappings.

    Returns:
        dict[MBID, MBID]: A dictionary mapping release group MBIDs to their
            canonical release MBIDs.
    """
    # Filter rows to keep only the necessary release group mbids
    filtered_df = canonical_release_df[
        canonical_release_df[CanonicalDataHeader.RELEASE_GP_MBID].isin(release_group_mbids)
    ]

    # Convert to a dictionary
    canonical_release_mapping = dict(
        zip(
            filtered_df[CanonicalDataHeader.RELEASE_GP_MBID],
            filtered_df[CanonicalDataHeader.CANONICAL_RELEASE_MBID],
            strict=False,
        )
    )

    return canonical_release_mapping


def get_canonical_recordings(
    canonical_release_mbids: list[str], canonical_recording_df: pd.DataFrame
) -> dict[MBID, pd.Series[MBID]]:
    """
    Return a dictionary mapping the canonical release MBIDs to the list of their canonical recording MBIDs.

    Args:
        canonical_release_mbids (set[str]): A set of canonical release MBIDs to
            map.
        canonical_recording_df (pd.DataFrame): The DataFrame containing the
            canonical recording mappings.

    Returns:
        dict[MBID, list[MBID]]: A dictionary mapping release group MBIDs to the
            list of their canonical recording MBIDs.
    """
    # Filter rows to keep only the necessary canonical release mbids
    filtered_df = canonical_recording_df[
        canonical_recording_df[CanonicalDataHeader.CANONICAL_RELEASE_MBID].isin(
            canonical_release_mbids
        )
    ]

    # Group the DataFrame by canonical_release_mbid
    grouped = filtered_df.groupby(CanonicalDataHeader.CANONICAL_RELEASE_MBID)[
        CanonicalDataHeader.CANONICAL_RECORDING_MBID
    ].apply(list)

    canonical_recordings = grouped.to_dict()

    return canonical_recordings


# %% === Main script === #
load_dotenv()
# TODO: Add CLI for setting environment variables

NOTION_TOKEN = os.getenv(EnvironmentVar.NOTION_TOKEN, "")

# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")


# Initialize the Notion client
notion_client = Client(
    auth=NOTION_TOKEN,
    # logger=logger,  # TODO: Test later
    # log_level=logging.DEBUG,
)


def query_notion_for_updates() -> list[dict]:
    """Query the Notion artist database and return the list of pages where the "To update" property is checked."""
    query = {"filter": {"property": "To update", "checkbox": {"equals": True}}}

    try:
        response: Any = notion_client.databases.query(database_id=ARTIST_DB_ID, **query)
        return response.get("results", [])
    except Exception as e:
        logger.error(f"Error querying Notion: {e}")
        return []


#  %% === Functions === #
def update_artist_and_releases(
    artist_mbid: str,
    artist_db_id: str,
    release_db_id: str,
    canonical_release_df: pd.DataFrame,
    notion_api: Client,
    mbid_to_page_id_map: dict[str, str],
    min_nb_tags: int,
) -> None:
    """
    Update the Notion database with an artist's data and all their canonical releases.

    Args:
        artist_mbid (str): The MusicBrainz ID of the artist.
        artist_db_id (str): The Notion database ID for artists.
        release_db_id (str): The Notion database ID for releases.
        canonical_release_df (pd.DataFrame): The DataFrame containing canonical release mappings.
        notion_api (Client): Notion API client.
        mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to Notion page IDs.
        min_nb_tags (int): Minimum number of tags to add for each entity.
    """
    logger.info(f"Updating artist and releases for MBID {artist_mbid}")

    # 1. Fetch artist data from MusicBrainz
    artist_data = fetch_artist_data(artist_mbid)
    if artist_data is None:
        logger.error(f"Failed to fetch artist data for MBID {artist_mbid}")
        return

    # 2. Create an Artist entity and update the Notion database
    artist = Artist.from_musicbrainz_data(artist_data, min_nb_tags)
    artist.update_notion_page(notion_api, artist_db_id, ARTIST_PAGE_ICON)

    # 3. Fetch artist's release groups
    release_groups = browse_release_groups_by_artist(artist_mbid, RELEASE_TYPE_FILTER)
    if not release_groups:
        logger.error(f"No release groups found for artist MBID {artist_mbid}")
        return

    # 4. Get canonical releases mapping from the release groups
    release_group_mbids = {rg[MBDataField.MBID] for rg in release_groups}
    canonical_releases_map = get_canonical_releases_map(release_group_mbids, canonical_release_df)

    # 5. Fetch and update each canonical release in the Notion database
    for release_group_mbid, canonical_release_mbid in canonical_releases_map.items():
        logger.info(f"Fetching canonical release data for MBID {canonical_release_mbid}")

        # Fetch release data from MusicBrainz
        release_data = fetch_release_data(canonical_release_mbid)
        if release_data is None:
            logger.error(f"Failed to fetch release data for MBID {canonical_release_mbid}")
            continue

        # Create a Release entity and update the Notion database
        release = Release.from_musicbrainz_data(release_data, min_nb_tags)
        release.update_notion_page(notion_api, release_db_id, RELEASE_PAGE_ICON)

    logger.info(f"Finished updating artist {artist_mbid} and their releases.")


def update_all_artists_and_releases(
    artist_mbids: list[str],
    artist_db_id: str,
    release_db_id: str,
    canonical_release_df: pd.DataFrame,
    notion_api: Client,
    mbid_to_page_id_map: dict[str, str],
    min_nb_tags: int,
) -> None:
    """
    Update the Notion database with all the given artists' data and their canonical releases.

    Args:
        artist_mbids (list[str]): List of MusicBrainz artist MBIDs to update.
        artist_db_id (str): The Notion database ID for artists.
        release_db_id (str): The Notion database ID for releases.
        canonical_release_df (pd.DataFrame): The DataFrame containing canonical release mappings.
        notion_api (Client): Notion API client.
        mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to Notion page IDs.
        min_nb_tags (int): Minimum number of tags to add for each entity.
    """
    for artist_mbid in artist_mbids:
        update_artist_and_releases(
            artist_mbid,
            artist_db_id,
            release_db_id,
            canonical_release_df,
            notion_api,
            mbid_to_page_id_map,
            min_nb_tags,
        )


# === Main script === #
if __name__ == "__main__":
    # Initialize environment variables and the Notion API client
    load_dotenv()

    ARTIST_DB_ID = os.getenv(EnvironmentVar.ARTIST_DB_ID, "")
    RELEASE_DB_ID = os.getenv(EnvironmentVar.RELEASE_DB_ID, "")
    RECORDING_DB_ID = os.getenv(EnvironmentVar.RECORDING_DB_ID, "")

    notion_api = Client(auth=NOTION_TOKEN)

    # Fetch the canonical release DataFrame
    canonical_release_df = pd.read_csv("canonical_releases.csv")

    # Placeholder for artist MBIDs and page mapping (fetch this data from Notion)
    artist_mbids = ["artist-mbid-1", "artist-mbid-2", "artist-mbid-3"]  # Example artist MBIDs
    mbid_to_page_id_map = {}  # This should be filled by querying the Notion API

    # Update all artists and their canonical releases
    update_all_artists_and_releases(
        artist_mbids,
        ARTIST_DB_ID,
        RELEASE_DB_ID,
        canonical_release_df,
        notion_api,
        mbid_to_page_id_map,
        MIN_NB_TAGS,
    )
