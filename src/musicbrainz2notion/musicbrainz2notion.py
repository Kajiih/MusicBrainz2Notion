"""Main module."""

import logging
import os
from enum import StrEnum

import musicbrainzngs
import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.musicbrainz_utils import (
    CanonicalDataHeader,
    EntityType,
    IncludeOption,
    MBDataKeys,
    ReleaseStatus,
    ReleaseType,
)
from musicbrainz2notion.utils import InterceptHandler

# === Types === #
type MBID = str


# === Enums === #
class EnvironmentVar(StrEnum):
    """Environment variable keys used in the application."""

    NOTION_TOKEN = "NOTION_TOKEN"  # noqa: S105
    ARTIST_DB_ID = "ARTIST_DB_ID"
    RELEASE_DB_ID = "RELEASE_DB_ID"
    RECORDING_DB_ID = "RECORDING_DB_ID"


class ArtistDBProperty(StrEnum):
    """Artist database property keys in Notion."""

    NAME = "Name"  # Database Key
    MBID = "mbid"
    TO_UPDATE = "To update"
    THUMBNAIL = "Thumbnail"
    TYPE = "Type"
    ALIAS = "Alias"
    START_DATE = "Birth/Foundation year"
    GENRES = "Genre(s)"
    AREA = "Area"
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"


class ReleaseDBProperty(StrEnum):
    """Release/release group database property keys in Notion."""

    NAME = "Name"  # Database key  # MB_NAME (ARTIST)
    MBID = "mbid"
    ARTIST = "Artist"
    COVER = "Cover"
    TYPE = "Type"
    FIRST_RELEASE_YEAR = "First release year"
    GENRES = "Genre(s)"
    AREA = "Area"
    LANGUAGE = "Language"  # Taken from iso 639-3
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"


class TrackDBProperty(StrEnum):
    """Track/Recording database property keys in Notion."""

    TITLE = "Title"  # Database key  # MB_NAME (RELEASE)
    MBID = "mbid"
    RELEASE = "Release"
    COVER = "Cover"
    TRACK_NUMBER = "Track number"
    LENGTH = "Length"
    FIRST_RELEASE_YEAR = "First release year"
    GENRES = "Genre(s)"
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"
    TRACK_ARTIST = "Track artist(s)"


# === Constants === #
## User configurable
MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10
ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True
RELEASE_TYPE_FILTER = [ReleaseType.ALBUM, ReleaseType.EP]
RELEASE_STATUS_FILTER = [ReleaseStatus.OFFICIAL]

## Environment variables
load_dotenv()
# TODO: Add CLI for setting environment variables

ARTIST_DB_ID = os.getenv(EnvironmentVar.ARTIST_DB_ID)
RELEASE_DB_ID = os.getenv(EnvironmentVar.RELEASE_DB_ID)
RECORDING_DB_ID = os.getenv(EnvironmentVar.RECORDING_DB_ID)

NOTION_TOKEN = os.getenv(EnvironmentVar.NOTION_TOKEN)

# Set up logging with Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


musicbrainzngs.set_useragent(__app_name__, __version__, __email__)
musicbrainzngs.set_rate_limit(MB_API_RATE_LIMIT_INTERVAL, MB_API_REQUEST_PER_INTERVAL)
logger.info("MusicBrainz client initialized.")


# Initialize the Notion client
notion = Client(
    auth=NOTION_TOKEN,
    # logger=logger,  # TODO: Test later
    # log_level=logging.DEBUG,
)


def fetch_artist_data(mbid: str, release_type: list[str] | None = None) -> dict | None:
    """
    Fetch artist data from MusicBrainz for the given artist mbid.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the artist.
        release_type (list[str] | None): List of release types to include in the
            response.
            Defaults to None (no filtering).

    Returns:
        artist_data (dict | None): The dictionary of artist data from
            MusicBrainz. None if there was an error while fetching the data.
    """
    logger.info(f"Fetching artist data for mbid {mbid}")

    if release_type is None:
        release_type = []

    try:
        artist_data = musicbrainzngs.get_artist_by_id(
            mbid,
            includes=[
                IncludeOption.ALIASES,
                IncludeOption.TAGS,
                IncludeOption.RATINGS,
            ],
            release_type=release_type,
        )

        logger.info(f"Fetched artist data for {artist_data[MBDataKeys.NAME]} (mbid {mbid})")

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
        release_groups (list[dict] | None): A list of release groups from
            MusicBrainz. None if there was an error while fetching the data.
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
        release_data (dict | None): The release data from MusicBrainz.
        Returns None if there was an error while fetching the data.
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

        logger.info(f"Fetched release data for {release_data[MBDataKeys.NAME]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching release data from MusicBrainz for {mbid}: {exc}")

        release_data = None

    return release_data


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
        canonical_release_mapping (dict[MBID, MBID]): A dictionary mapping release
            group MBIDs to their canonical release MBIDs.
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
        canonical_recordings(dict[MBID, list[MBID]]): A dictionary mapping
            release group MBIDs to the list of their canonical recording MBIDs.
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


def fetch_recordings_data(mbid: str) -> dict | None:
    """
    Fetch recording data from MusicBrainz for a given recording MBID.

    The function retrieves additional information about the recording, such as
    artist credits, tags, and rating.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the recording.

    Returns:
        recording_data (dict | None): The recording data from MusicBrainz.
            Returns None if there was an error while fetching the data.
    """
    logger.info(f"Fetching recording data for mbid {mbid}")

    try:
        recording_data = musicbrainzngs.get_recording_by_id(
            mbid,
            includes=[
                IncludeOption.ARTIST_CREDITS,
                IncludeOption.TAGS,
            ],
        )

        logger.info(f"Fetched recording data for {recording_data[MBDataKeys.TITLE]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching recording data from MusicBrainz for {mbid}: {exc}")
        recording_data = None

    return recording_data


def update_artist_in_notion(artist: dict):
    """
    Update artist information in the Notion database.

    Args:
        artist (dict): The artist data to be updated.
    """
    try:
        notion.pages.update(
            page_id=artist["id"],
            properties={
                ArtistDBProperty.MB_NAME: {"title": [{"text": {"content": artist["name"]}}]},
                ArtistDBProperty.ALIAS: {
                    "rich_text": [
                        {
                            "text": {
                                "content": ", ".join(
                                    alias["alias"] for alias in artist.get("alias-list", [])
                                )
                            }
                        }
                    ]
                },
                ArtistDBProperty.START_DATE: {
                    "date": {"start": artist.get("life-span", {}).get("begin")}
                },
                ArtistDBProperty.GENRES: {
                    "multi_select": [
                        {"name": genre["name"]} for genre in artist.get("genre-list", [])
                    ]
                },
                ArtistDBProperty.AREA: {"select": {"name": artist.get("area", {}).get("name", "")}},
                ArtistDBProperty.RATING: {"number": artist.get("rating", {}).get("value", 0)},
            },
        )
        logger.info(f"Updated artist {artist["name"]} in Notion.")
    except Exception as e:
        logger.error(f"Error updating artist {artist["name"]} in Notion: {e}")


def update_release_in_notion(release: dict):
    """
    Update release information in the Notion database.

    Args:
        release (dict): The release data to be updated.
    """
    try:
        notion.pages.create(
            parent={"database_id": RELEASE_DB_ID},
            properties={
                ReleaseDBProperty.TITLE: {"title": [{"text": {"content": release["title"]}}]},
                ReleaseDBProperty.MBID: {"rich_text": [{"text": {"content": release["id"]}}]},
                ReleaseDBProperty.ARTIST: {"relation": [{"id": release["artist"]["id"]}]},
                ReleaseDBProperty.TYPE: {"select": {"name": release.get("primary-type", "Other")}},
                ReleaseDBProperty.FIRST_RELEASE_YEAR: {
                    "date": {"start": release.get("first-release-date")}
                },
            },
        )
        logger.info(f"Updated release {release["title"]} in Notion.")
    except Exception as e:
        logger.error(f"Error updating release {release["title"]} in Notion: {e}")


def update_track_in_notion(track: dict, release: dict):
    """
    Update track (recording) information in the Notion database.

    Args:
        track (dict): The track data to be updated.
        release (dict): The release data associated with the track.
    """
    try:
        notion.pages.create(
            parent={"database_id": RECORDING_DB_ID},
            properties={
                TrackDBProperty.NAME: {"title": [{"text": {"content": track["title"]}}]},
                TrackDBProperty.MBID: {"rich_text": [{"text": {"content": track["id"]}}]},
                TrackDBProperty.RELEASE: {"relation": [{"id": release["id"]}]},
                TrackDBProperty.LENGTH: {
                    "number": track.get("length", 0) / 1000
                },  # Convert ms to seconds
                TrackDBProperty.RATING: {"number": track.get("rating", {}).get("value", 0)},
            },
        )
        logger.info(f"Updated track {track["title"]} in Notion.")
    except Exception as e:
        logger.error(f"Error updating track {track["title"]} in Notion: {e}")
