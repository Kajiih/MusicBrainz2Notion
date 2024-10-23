"""Main module."""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, Any

import frosch
import musicbrainzngs
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client
from toolz import dicttoolz

from musicbrainz2notion.__about__ import __app_name__, __email__, __repo_url__, __version__
from musicbrainz2notion.canonical_data_processing import (
    download_and_preprocess_canonical_data,
    get_release_group_to_release_map,
    load_canonical_release_data,
)
from musicbrainz2notion.config import (
    ARTIST_UPDATE_MBIDS,
    DATA_DIR,
    FORCE_UPDATE_CANONICAL_DATA,
    MB_API_RATE_LIMIT_INTERVAL,
    MB_API_REQUEST_PER_INTERVAL,
    MIN_NB_TAGS,
    RELEASE_SECONDARY_TYPE_EXCLUDE,
    RELEASE_TYPE_FILTER,
)
from musicbrainz2notion.database_entities import (
    Artist,
    ArtistDBProperty,
    NotionBDProperty,
    Recording,
    Release,
    ReleaseDBProperty,
    TrackDBProperty,
)
from musicbrainz2notion.musicbrainz_data_retrieval import (
    browse_release_groups_by_artist,
    extract_recording_mbids_and_track_number,
    fetch_artist_data,
    fetch_recording_data,
    fetch_release_data,
)
from musicbrainz2notion.musicbrainz_utils import MBID, EntityType, MBDataDict
from musicbrainz2notion.notion_utils import (
    PageId,
    PropertyField,
    PropertyType,
    extract_plain_text,
    format_checkbox,
    get_checkbox_value,
)
from musicbrainz2notion.utils import EnvironmentVar, InterceptHandler

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd

frosch.hook()  # enable frosch for easier debugging


# %% === Processing Notion data == #
def is_page_marked_for_update(page_result: dict[str, Any]) -> bool:
    """
    Check if the page has the 'To update' property set to True.

    Args:
        page_result (dict[str, Any]): The Notion page result.

    Returns:
        bool: True if the 'To update' checkbox is set, False otherwise.
    """
    return get_checkbox_value(page_result["properties"][ArtistDBProperty.TO_UPDATE])


def get_page_mbid(page_result: dict[str, Any]) -> MBID:
    """
    Extract the MBID (MusicBrainz ID) from the Notion page result.

    Args:
        page_result (dict[str, Any]): The Notion page result.

    Returns:
        MBID: The MBID from the page.
    """
    return extract_plain_text(
        page_result["properties"][ArtistDBProperty.MBID][PropertyType.RICH_TEXT]
    )


def get_page_id(page_result: dict[str, Any]) -> PageId:
    """
    Extract the unique Notion page ID.

    Args:
        page_result (dict[str, Any]): The Notion page result.

    Returns:
        PageId: The unique page ID from the page result.
    """
    return page_result[PropertyField.ID]


def compute_mbid_to_page_id_map(notion_api: Client, database_id: str) -> dict[MBID, PageId]:
    """
    Compute the mapping of MBIDs to Notion page IDs for a given database.

    Args:
        notion_api (Client): Notion API client.
        database_id (str): The ID of the database in Notion.

    Returns:
        dict[MBID, PageId]: Mapping of MBIDs to their Notion page IDs.
    """
    logger.info(f"Computing MBID to page ID mapping for database {database_id}")

    mbid_to_page_id_map = {}
    has_more = True
    start_cursor = None

    # Process paginated results
    while has_more:
        logger.debug(f"Querying database {database_id} with start_cursor={start_cursor}")
        try:
            query: Any = notion_api.databases.query(
                database_id=database_id, start_cursor=start_cursor
            )
        except Exception:
            logger.exception(
                f"Error querying database {database_id} to compute MBID to page ID mapping."
            )
            raise

        new_id_maps = {
            get_page_mbid(page_result): get_page_id(page_result) for page_result in query["results"]
        }
        mbid_to_page_id_map.update(new_id_maps)

        # Pagination control
        has_more = query["has_more"]
        start_cursor = query["next_cursor"]

    logger.info(f"Computed mapping for {len(mbid_to_page_id_map)} entries.")

    return mbid_to_page_id_map


def fetch_artists_to_update(
    notion_api: Client, artist_db_id: str
) -> tuple[list[MBID], dict[MBID, PageId]]:
    """
    Retrieve the list of artists to update in the Notion database.

    Also returns a mapping of artist MBIDs to their Notion page IDs.

    Args:
        notion_api (Client): Notion API client.
        artist_db_id (str): The ID of the artist database in Notion.

    Returns:
        list[MBID]: List of artist MBIDs to update.
        dict[MBID, PageId]: Mapping of artist MBIDs to their Notion page IDs.
    """
    logger.info(f"Fetching artists to update from database {artist_db_id}")

    to_update_mbids = []
    mbid_to_page_id_map = {}

    has_more = True
    start_cursor = None

    while has_more:
        logger.debug(f"Querying artist database {artist_db_id} with start_cursor={start_cursor}")

        try:
            query: Any = notion_api.databases.query(
                database_id=artist_db_id, start_cursor=start_cursor
            )
        except Exception:
            logger.exception(f"Error fetching artist data from database {artist_db_id}")
            raise

        for artist_result in query["results"]:
            mbid = get_page_mbid(artist_result)
            mbid_to_page_id_map[mbid] = get_page_id(artist_result)

            if is_page_marked_for_update(artist_result):
                to_update_mbids.append(mbid)

        # Pagination control
        has_more = query["has_more"]
        start_cursor = query["next_cursor"]

    logger.info(
        f"Found {len(to_update_mbids)} artists to update and computed mapping for {len(mbid_to_page_id_map)} entries."
    )

    return to_update_mbids, mbid_to_page_id_map


def move_outdated_entity_pages_to_trash(
    notion_api: Client,
    database_id: str,
    entity_type: EntityType,
    updated_entity_mbids: set[MBID],
    artist_page_ids: set[PageId],
    artist_property: ReleaseDBProperty | TrackDBProperty,
) -> None:
    """
    Move outdated pages (release or recording) associated with artists to trash.

    Args:
        notion_api (Client): The Notion API client.
        database_id (str): The Notion database ID (for either releases or
            recordings).
        entity_type (EntityType): The type of entity (Release or Recording).
        updated_entity_mbids (set[MBID]): Set of updated MBIDs for either releases or
            recordings.
        artist_page_ids (set[PageId]): Set of artist page IDs to filter by.
        artist_property (ReleaseDBProperty | TrackDBProperty): The name of the artist relation property in the
            database (e.g., 'Artist').
    """
    logger.info(f"Moving out of date {entity_type}s to trash.")

    # Construct the filter to query for pages related to the updated artists
    query_filter = {
        "or": [
            {"property": artist_property, "relation": {"contains": artist_page_id}}
            for artist_page_id in artist_page_ids
        ]
    }

    # Query the Notion database for the pages related to the updated artists
    pages: Any = notion_api.databases.query(database_id=database_id, filter=query_filter)

    # Loop through the results and move outdated pages to the trash
    for page in pages["results"]:
        page_mbid = get_page_mbid(page)
        if page_mbid not in updated_entity_mbids:
            logger.info(f"Moving {entity_type} {page_mbid} to trash.")
            page_id = get_page_id(page)
            notion_api.pages.update(page_id=page_id, archived=True)


def get_release_map_with_auto_update(
    release_group_mbids: list[MBID],
    data_dir: Path,
    canonical_release_df: pd.DataFrame | None = None,
) -> dict[MBID, MBID]:
    """TODO."""
    if canonical_release_df is None:
        canonical_release_df = load_canonical_release_data(DATA_DIR)

    release_group_to_canonical_release_map = get_release_group_to_release_map(
        release_group_mbids, canonical_release_df
    )

    nb_missing_release_mbids = len(release_group_mbids) - len(
        release_group_to_canonical_release_map
    )

    if not nb_missing_release_mbids:
        return release_group_to_canonical_release_map

    logger.info(
        f"Some ({nb_missing_release_mbids}) release MBIDs are missing in the MusicBrainz canonical_data, updating the canonical data."
    )

    updated_canonical_release_df = download_and_preprocess_canonical_data(
        data_dir=data_dir,
        keep_original=False,
    )

    release_group_to_canonical_release_map = get_release_group_to_release_map(
        release_group_mbids, updated_canonical_release_df
    )
    nb_missing_release_mbids = len(release_group_mbids) - len(
        release_group_to_canonical_release_map
    )

    if nb_missing_release_mbids:
        logger.error(
            f"Some ({nb_missing_release_mbids}) release MBIDs are still missing in the MusicBrainz canonical_data, they won't be updated. Pleas file an issue on the project repository: {__repo_url__}."
        )
    else:
        logger.info("Canonical data updated successfully.")

    return release_group_to_canonical_release_map


# %% === Main script === #
load_dotenv()
# TODO: Add CLI for setting environment variables

NOTION_TOKEN = os.getenv(EnvironmentVar.NOTION_TOKEN, "")

# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)

# Remove default logging to stderr
logger.remove()

logger.add(
    "logs/app.log",  # Log to a file
    level="DEBUG",  # Minimum logging level
    # format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="1 week",  # Rotate logs weekly
    compression="zip",  # Compress rotated logs
)

logger.add(
    sys.stdout,  # Log to the console
    level="INFO",  # Minimum logging level for the console
    # format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
)

# Initialize the MusicBrainz client
musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")


# Initialize the Notion client
notion_client = Client(
    auth=NOTION_TOKEN,
    # logger=logger,  # TODO: Test later
    # log_level=logging.DEBUG,
)


if __name__ == "__main__":
    # Initialize environment variables and the Notion API client
    load_dotenv()

    ARTIST_DB_ID = os.getenv(EnvironmentVar.ARTIST_DB_ID, "")
    RELEASE_DB_ID = os.getenv(EnvironmentVar.RELEASE_DB_ID, "")
    RECORDING_DB_ID = os.getenv(EnvironmentVar.RECORDING_DB_ID, "")
    database_ids = {
        EntityType.ARTIST: ARTIST_DB_ID,
        EntityType.RELEASE: RELEASE_DB_ID,
        EntityType.RECORDING: RECORDING_DB_ID,
    }

    # Loading canonical data
    if FORCE_UPDATE_CANONICAL_DATA:
        canonical_release_df = download_and_preprocess_canonical_data(
            data_dir=DATA_DIR,
            keep_original=False,
        )
    else:
        canonical_release_df = load_canonical_release_data(DATA_DIR)

    notion_api = Client(auth=NOTION_TOKEN)

    # === Retrieve artists to update and compute mbid to page id map === #
    to_update_artist_mbids, artist_mbid_to_page_id_map = fetch_artists_to_update(
        notion_api, ARTIST_DB_ID
    )
    to_update_artist_mbids += ARTIST_UPDATE_MBIDS
    logger.info(f"Updating {len(to_update_artist_mbids)} artists.")

    release_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_api, RELEASE_DB_ID)
    recording_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_api, RECORDING_DB_ID)

    mbid_to_page_id_map = dicttoolz.merge(
        artist_mbid_to_page_id_map, release_mbid_to_page_id_map, recording_mbid_to_page_id_map
    )

    # === Fetch and update each artists data and retrieve their release groups === #
    all_release_groups_data: list[MBDataDict] = []
    for artist_mbid in to_update_artist_mbids:
        artist_data = fetch_artist_data(artist_mbid)
        if artist_data is None:
            continue

        artist = Artist.from_musicbrainz_data(artist_data=artist_data, min_nb_tags=MIN_NB_TAGS)
        artist.synchronize_notion_page(
            notion_api=notion_api,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
        )

        release_groups_data = browse_release_groups_by_artist(
            artist_mbid=artist_mbid,
            release_type=RELEASE_TYPE_FILTER,
            secondary_type_exclude=RELEASE_SECONDARY_TYPE_EXCLUDE,
        )
        release_groups_data = release_groups_data or []

        all_release_groups_data += release_groups_data

    # === Fetch and update each canonical release data === #
    release_group_mbids = [release_group["id"] for release_group in all_release_groups_data]

    release_group_to_release_map = get_release_map_with_auto_update(
        release_group_mbids=release_group_mbids,
        data_dir=DATA_DIR,
        canonical_release_df=canonical_release_df,
    )
    del canonical_release_df

    updated_recording_mbids = set()
    for release_group_data in all_release_groups_data:
        release_group_mbid = release_group_data["id"]
        release_mbid = release_group_to_release_map[release_group_mbid]

        release_data = fetch_release_data(release_mbid)
        if release_data is None:
            continue

        release = Release.from_musicbrainz_data(
            release_data=release_data,
            release_group_data=release_group_data,
            min_nb_tags=MIN_NB_TAGS,
        )
        release.synchronize_notion_page(
            notion_api=notion_api,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
        )

        # === Fetch and update each recording data === #
        for recording_mbid, track_number in extract_recording_mbids_and_track_number(release_data):
            updated_recording_mbids.add(recording_mbid)

            recording_data = fetch_recording_data(recording_mbid)
            if recording_data is None:
                continue

            recording = Recording.from_musicbrainz_data(
                recording_data=recording_data,
                formatted_track_number=track_number,
                release=release,
                min_nb_tags=MIN_NB_TAGS,
            )
            recording.synchronize_notion_page(
                notion_api=notion_api,
                database_ids=database_ids,
                mbid_to_page_id_map=mbid_to_page_id_map,
            )

    # === Check for old releases and recordings to delete === #
    updated_artist_page_ids = {
        artist_mbid_to_page_id_map[artist_mbid] for artist_mbid in to_update_artist_mbids
    }
    updated_release_mbids = set(release_group_to_release_map.values())

    move_outdated_entity_pages_to_trash(
        notion_api=notion_api,
        database_id=database_ids[EntityType.RELEASE],
        entity_type=EntityType.RELEASE,
        updated_entity_mbids=updated_release_mbids,
        artist_page_ids=updated_artist_page_ids,
        artist_property=ReleaseDBProperty.ARTIST,
    )

    move_outdated_entity_pages_to_trash(
        notion_api=notion_api,
        database_id=database_ids[EntityType.RECORDING],
        entity_type=EntityType.RECORDING,
        updated_entity_mbids=updated_recording_mbids,
        artist_page_ids=updated_artist_page_ids,
        artist_property=TrackDBProperty.TRACK_ARTIST,
    )

    # === Update "To update" property of artists === #
    for artist_mbid in to_update_artist_mbids:
        page_id = artist_mbid_to_page_id_map[artist_mbid]
        notion_api.pages.update(
            page_id=page_id,
            properties={ArtistDBProperty.TO_UPDATE: format_checkbox(False)},
        )
