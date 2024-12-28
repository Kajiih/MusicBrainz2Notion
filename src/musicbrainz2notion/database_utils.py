"""Tools for interacting with MusicBrainz2Notion entities databases in Notion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from musicbrainz2notion.__about__ import (
    PROJECT_ROOT,
    __repo_url__,
)
from musicbrainz2notion.canonical_data_processing import (
    get_release_group_to_release_map,
    load_canonical_release_data,
    update_canonical_data,
)
from musicbrainz2notion.database_entities import (
    ArtistDBProperty,
    ReleaseDBProperty,
    TrackDBProperty,
)
from musicbrainz2notion.notion_utils import (
    PageId,
    PropertyField,
    PropertyType,
    extract_plain_text,
    get_checkbox_value,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd
    from notion_client import Client

    from musicbrainz2notion.musicbrainz_utils import MBID, EntityType

DATA_DIR = PROJECT_ROOT / "data"


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


def get_page_name(page_result: dict[str, Any]) -> str:
    """
    Extract the name of a notion page from the result of the API request.

    Args:
        page_result (dict[str, Any]): The Notion page result.

    Returns:
        str: The name of the page.
    """
    return extract_plain_text(
        page_result["properties"][ArtistDBProperty.NAME][PropertyType.RICH_TEXT]
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


# TODO: use iterate_paginated_api instead of handle pagination manually
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

    mbid_to_page_id_map: dict[MBID, PageId] = {}
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


# TODO: use iterate_paginated_api instead of handle pagination manually
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

    to_update_mbids: list[MBID] = []
    mbid_to_page_id_map: dict[MBID, PageId] = {}

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


def move_to_trash_outdated_entity_pages(
    notion_api: Client,
    database_id: str,
    entity_type: EntityType,
    updated_entity_page_ids: set[MBID],
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
        updated_entity_page_ids (set[MBID]): Set of page IDs of the updated
            entities.
        artist_page_ids (set[PageId]): Set of artist page IDs to filter by.
        artist_property (ReleaseDBProperty | TrackDBProperty): The name of the artist relation property in the
            database (e.g., 'Artist').
    """
    if not artist_page_ids:  # The filter doesn't work if there is no updated artist
        return

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
        page_id = get_page_id(page)
        if page_id not in updated_entity_page_ids:
            logger.info(f"Moving {entity_type} {page_id} to trash.")
            notion_api.pages.update(page_id=page_id, archived=True)

    has_more = True
    start_cursor = None

    # Loop through paginated results
    while has_more:
        try:
            # Query the Notion database for the pages related to the updated artists
            pages_response: Any = notion_api.databases.query(
                database_id=database_id, filter=query_filter, start_cursor=start_cursor
            )
        except Exception as e:
            logger.warning(f"Error querying Notion database {database_id}: {e}")
            return

        # Loop through the results and move outdated pages to the trash
        for page in pages_response["results"]:
            page_id = get_page_id(page)
            if page_id not in updated_entity_page_ids:
                page_name = get_page_name(page)
                logger.info(f"Moving {entity_type} {page_name} to trash.")
                notion_api.pages.update(page_id=page_id, archived=True)

        # Check if there are more pages to retrieve
        has_more = pages_response.get("has_more", False)
        start_cursor = pages_response.get("next_cursor", None)


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

    logger.warning(
        f"Some ({nb_missing_release_mbids}) release MBIDs are missing in the MusicBrainz canonical_data, updating the canonical data."
    )

    updated_canonical_release_df = update_canonical_data(
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
        missing_mbids = set(release_group_mbids) - set(release_group_to_canonical_release_map)
        logger.error(
            f"Some ({nb_missing_release_mbids}) release MBIDs are still missing in the MusicBrainz canonical data, they won't be updated. Pleas file an issue on the project repository: {__repo_url__}."
        )
        logger.debug(f"Missing mbids: {missing_mbids}")
    else:
        logger.info("Canonical data updated successfully.")

    return release_group_to_canonical_release_map
