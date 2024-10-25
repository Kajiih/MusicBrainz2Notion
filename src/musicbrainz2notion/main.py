"""Main module."""

from __future__ import annotations

import logging
import os
import sys
from typing import Annotated

import frosch
import musicbrainzngs
import typer
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client
from toolz import dicttoolz

from musicbrainz2notion.__about__ import __app_name__, __email__, __repo_url__, __version__
from musicbrainz2notion.canonical_data_processing import (
    download_and_preprocess_canonical_data,
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
    Recording,
    Release,
    ReleaseDBProperty,
    TrackDBProperty,
)
from musicbrainz2notion.database_utils import (
    compute_mbid_to_page_id_map,
    fetch_artists_to_update,
    get_release_map_with_auto_update,
    move_to_trash_outdated_entity_pages,
)
from musicbrainz2notion.musicbrainz_data_retrieval import (
    browse_release_groups_by_artist,
    extract_recording_mbids_and_track_number,
    fetch_artist_data,
    fetch_recording_data,
    fetch_release_data,
)
from musicbrainz2notion.musicbrainz_utils import EntityType, MBDataDict
from musicbrainz2notion.notion_utils import (
    format_checkbox,
)
from musicbrainz2notion.utils import EnvironmentVar, InterceptHandler

frosch.hook()  # enable frosch for easier debugging

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


def main(
    NOTION_TOKEN: Annotated[
        str, typer.Option("--notion", "-n", envvar=EnvironmentVar.NOTION_TOKEN)
    ],
    ARTIST_DB_ID: Annotated[str, typer.Option(envvar=EnvironmentVar.ARTIST_DB_ID)],
    RELEASE_DB_ID: Annotated[str, typer.Option(envvar=EnvironmentVar.RELEASE_DB_ID)],
    RECORDING_DB_ID: Annotated[str, typer.Option(envvar=EnvironmentVar.RECORDING_DB_ID)],
    FANART_API_KEY: Annotated[str, typer.Option(envvar=EnvironmentVar.FANART_API_KEY)],
) -> None:
    """TODO: Document arguments and what the function does."""
    # Initialize the Notion client
    notion_client = Client(auth=NOTION_TOKEN)

    # Initialize the MusicBrainz client
    musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
    musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
    logger.info("MusicBrainz client initialized.")

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

    # === Retrieve artists to update and compute mbid to page id map === #
    to_update_artist_mbids, artist_mbid_to_page_id_map = fetch_artists_to_update(
        notion_client, ARTIST_DB_ID
    )
    to_update_artist_mbids += ARTIST_UPDATE_MBIDS
    logger.info(f"Updating {len(to_update_artist_mbids)} artists.")

    release_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_client, RELEASE_DB_ID)
    recording_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_client, RECORDING_DB_ID)

    mbid_to_page_id_map = dicttoolz.merge(
        artist_mbid_to_page_id_map, release_mbid_to_page_id_map, recording_mbid_to_page_id_map
    )

    # === Fetch and update each artists data and retrieve their release groups === #
    all_release_groups_data: list[MBDataDict] = []
    for artist_mbid in to_update_artist_mbids:
        artist_data = fetch_artist_data(artist_mbid)
        if artist_data is None:
            continue

        artist = Artist.from_musicbrainz_data(
            artist_data=artist_data,
            auto_added=False,
            min_nb_tags=MIN_NB_TAGS,
            fanart_api_key=FANART_API_KEY,
        )
        artist.synchronize_notion_page(
            notion_api=notion_client,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            fanart_api_key=FANART_API_KEY,
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

    updated_recording_page_ids = set()
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
            notion_api=notion_client,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            fanart_api_key=FANART_API_KEY,
        )

        # === Fetch and update each recording data === #
        for recording_mbid, track_number in extract_recording_mbids_and_track_number(release_data):
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
                notion_api=notion_client,
                database_ids=database_ids,
                mbid_to_page_id_map=mbid_to_page_id_map,
                fanart_api_key=FANART_API_KEY,
            )

            updated_recording_page_ids.add(mbid_to_page_id_map[recording_mbid])

    # === Check for old releases and recordings to delete === #
    updated_artist_page_ids = {
        artist_mbid_to_page_id_map[artist_mbid] for artist_mbid in to_update_artist_mbids
    }
    updated_release_page_ids = {
        mbid_to_page_id_map[release_mbid] for release_mbid in release_group_to_release_map.values()
    }

    move_to_trash_outdated_entity_pages(
        notion_api=notion_client,
        database_id=database_ids[EntityType.RELEASE],
        entity_type=EntityType.RELEASE,
        updated_entity_page_ids=updated_release_page_ids,
        artist_page_ids=updated_artist_page_ids,
        artist_property=ReleaseDBProperty.ARTIST,
    )

    move_to_trash_outdated_entity_pages(
        notion_api=notion_client,
        database_id=database_ids[EntityType.RECORDING],
        entity_type=EntityType.RECORDING,
        updated_entity_page_ids=updated_recording_page_ids,
        artist_page_ids=updated_artist_page_ids,
        artist_property=TrackDBProperty.TRACK_ARTIST,
    )

    # === Update "To update" property of artists === #
    for artist_mbid in to_update_artist_mbids:
        page_id = artist_mbid_to_page_id_map[artist_mbid]
        notion_client.pages.update(
            page_id=page_id,
            properties={ArtistDBProperty.TO_UPDATE: format_checkbox(False)},
        )


if __name__ == "__main__":
    load_dotenv()
    typer.run(main)
