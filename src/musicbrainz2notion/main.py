"""Main module."""

from __future__ import annotations

import logging
import os
import sys
from typing import Annotated

import attrs
import frosch
import typed_settings as ts
from cyclopts import App, Parameter
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client

# import typer
from rich.prompt import Prompt
from toolz import dicttoolz

from musicbrainz2notion.__about__ import (
    _PROJECT_ROOT,
    __app_name__,
    __email__,
    __repo_url__,
    __version__,
)
from musicbrainz2notion.canonical_data_processing import (
    download_and_preprocess_canonical_data,
    load_canonical_release_data,
)
from musicbrainz2notion.config import (
    ARTIST_UPDATE_MBIDS,
    FORCE_UPDATE_CANONICAL_DATA,
    MIN_NB_TAGS,
    RELEASE_SECONDARY_TYPE_EXCLUDE,
    RELEASE_TYPE_FILTER,
    Settings,
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
    DATA_DIR,
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
    initialize_musicbrainz_client,
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


CONFIG_PATH = _PROJECT_ROOT / "settings.toml"
SECRETS_PATH = _PROJECT_ROOT / "secrets.toml"

loaded_settings = ts.load(
    Settings,
    appname=__app_name__,
    config_files=[CONFIG_PATH],
    env_prefix=None,
)
# settings_loader = ts.default_loaders(
#     appname=__app_name__,
#     config_files=[CONFIG_PATH],
#     env_prefix=None,
# )

app = App()


@app.default
def main(
    notion_api_key: Annotated[
        str | None,
        Parameter(["--notion", "-n"], env_var=EnvironmentVar.NOTION_API_KEY),
    ] = loaded_settings.notion_api_key or None,
    artist_db_id: Annotated[
        str | None,
        Parameter(["--artist", "-a"], env_var=EnvironmentVar.ARTIST_DB_ID),
    ] = loaded_settings.artist_db_id or None,
    release_db_id: Annotated[
        str | None,
        Parameter(["--release", "-r"], env_var=EnvironmentVar.RELEASE_DB_ID),
    ] = loaded_settings.release_db_id or None,
    track_db_id: Annotated[
        str | None,
        Parameter(["--track", "--recording", "-t"], env_var=EnvironmentVar.TRACK_DB_ID),
    ] = loaded_settings.track_db_id or None,
    fanart_api_key: Annotated[
        str | None,
        Parameter(["--fanart", "-f"], env_var=EnvironmentVar.FANART_API_KEY),
    ] = loaded_settings.fanart_api_key,
    *,
    loaded_settings: Annotated[Settings, Parameter(parse=False)] = loaded_settings,
) -> None:
    """
    Synchronize Notion's Artist, Release, and Track databases with MusicBrainz data.

    Args:
        notion_api_key: Notion API key.
        artist_db_id: Artist database ID.
        release_db_id: Release database ID.
        track_db_id: Track database ID.
        fanart_api_key: Fanart API key.
        loaded_settings: Settings loaded from the configuration file.
    """
    settings = attrs.evolve(
        loaded_settings,
        notion_api_key=notion_api_key or Prompt.ask("Notion API key"),
        artist_db_id=artist_db_id or Prompt.ask("Artist database ID"),
        release_db_id=release_db_id or Prompt.ask("Release database ID"),
        track_db_id=track_db_id or Prompt.ask("Track database ID"),
        fanart_api_key=fanart_api_key,
    )

    # Initialize the Notion client
    notion_client = Client(auth=settings.notion_api_key)

    # Initialize the MusicBrainz client
    initialize_musicbrainz_client(__app_name__, __version__, __email__)
    logger.info("MusicBrainz client initialized.")

    database_ids = {
        EntityType.ARTIST: settings.artist_db_id,
        EntityType.RELEASE: settings.release_db_id,
        EntityType.RECORDING: settings.track_db_id,
    }

    # Loading canonical data
    # Create data dir if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    if FORCE_UPDATE_CANONICAL_DATA or not os.listdir(DATA_DIR):
        canonical_release_df = download_and_preprocess_canonical_data(
            data_dir=DATA_DIR,
            keep_original=False,
        )
    else:
        canonical_release_df = load_canonical_release_data(DATA_DIR)

    # === Retrieve artists to update and compute mbid to page id map === #
    to_update_artist_mbids, artist_mbid_to_page_id_map = fetch_artists_to_update(
        notion_client, settings.artist_db_id
    )
    to_update_artist_mbids += ARTIST_UPDATE_MBIDS
    logger.info(f"Updating {len(to_update_artist_mbids)} artists.")

    release_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_client, settings.release_db_id)
    recording_mbid_to_page_id_map = compute_mbid_to_page_id_map(notion_client, settings.track_db_id)

    mbid_to_page_id_map: dict[str, str] = dicttoolz.merge(
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
            fanart_api_key=fanart_api_key,
        )
        artist.synchronize_notion_page(
            notion_api=notion_client,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            fanart_api_key=fanart_api_key,
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
            fanart_api_key=fanart_api_key,
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
                fanart_api_key=fanart_api_key,
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
    # typer.run(main)
    # main()
    app()
