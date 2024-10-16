"""Main module."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import musicbrainzngs
from dotenv import load_dotenv
from loguru import logger
from notion_client import Client

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.musicbrainz_utils import (
    CanonicalDataHeader,
    EntityType,
    IncludeOption,
    MBDataField,
    ReleaseStatus,
    ReleaseType,
)
from musicbrainz2notion.notion_utils import (
    FilterCondition,
    PagePropertyType,
    PropertyField,
    format_checkbox,
    format_emoji,
    format_external_file,
    format_file,
    format_multi_select,
    format_number,
    format_rich_text,
    format_select,
    format_text,
    format_title,
)
from musicbrainz2notion.utils import InterceptHandler

if TYPE_CHECKING:
    import pandas as pd


# === Config === #
MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10

RELEASE_TYPE_FILTER = [ReleaseType.ALBUM, ReleaseType.EP]
RELEASE_STATUS_FILTER = [ReleaseStatus.OFFICIAL]

ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True

MIN_NB_TAGS = 3

ARTIST_PAGE_ICON = "🧑‍🎤"
RELEASE_PAGE_ICON = "💽"
RECORDING_PAGE_ICON = "🎼"

TEST_URL = "https://images.fanart.tv/fanart/superbus-50576f8295220.jpeg"
# TODO: Implement thumbnails and cover fetching

# === Types === #
type MBID = str


# %% === Enums === #
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
    START_YEAR = "Birth/Foundation year"
    TAGS = "Tags"
    # GENRES = "Genre(s)"
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
    # GENRES = "Genre(s)"
    TAGS = "Tags"
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
    # GENRES = "Genre(s)"
    TAGS = "Tags"
    RATING = "Rating"
    MB_NAME = "Name (Musicbrainz)"
    TRACK_ARTIST = "Track artist(s)"


type NotionBDProperty = ArtistDBProperty | ReleaseDBProperty | TrackDBProperty


# %% === Database Entities === #
@dataclass(frozen=True)
class MusicBrainzEntity(ABC):
    """Base class for MusicBrainz2Notion entities, representing a page in a Notion database."""

    mbid: MBID
    name: str

    @abstractmethod
    def to_page_properties(self) -> dict[NotionBDProperty, dict[PagePropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Returns:
            page_properties (dict[NotionBDProperty, Any]): The formatted
                properties dictionary for Notion API.
        """

    def update_notion_page(self, notion_api: Client, database_id: str, icon_emoji: str) -> None:
        """
        Update the entity's page in the Notion database.

        Args:
            notion_api (Client): Notion API client.
            database_id (str): Notion database ID.
            icon_emoji (str): Emoji to use as the icon for the page.
        """
        logger.info(f"Updating {self} page in Notion.")

        try:
            response: Any = notion_api.databases.query(
                database_id=database_id,
                filter={
                    "property": ArtistDBProperty.MBID,
                    PagePropertyType.RICH_TEXT: {FilterCondition.EQUALS: self.mbid},
                },
            )
            if response["results"]:
                logger.info(f"{self} found in Notion, updating existing page.")

                page_id = response["results"][0][PropertyField.ID]
                notion_api.pages.update(
                    page_id=page_id,
                    properties=self.to_page_properties(),
                    icon=format_emoji(icon_emoji),
                )

            else:
                logger.info(f"{self} not found, creating new page.")

                notion_api.pages.create(
                    parent={"database_id": database_id},
                    properties=self.to_page_properties(),
                    icon=format_emoji(icon_emoji),
                )

        except Exception as exc:
            logger.error(f"Error updating {self} in Notion: {exc}")
            raise  # Re-raise the exception to be caught by the caller

    @staticmethod
    def select_tags(tag_list: list[dict[str, str]], min_nb_tags: int) -> list[str]:
        """
        Select tags to add to the entity.

        Args:
            tag_list (list[dict[str, str]]): List of tags with their counts
                coming from MusicBrainz API.
            min_nb_tags (int): Minimum number of tags to select. There might
                be more tags selected if there are multiple tags with the
                same vote count.

        """
        # Sort the tags by count in descending order
        sorted_tags = sorted(tag_list, key=lambda tag: int(tag[MBDataField.COUNT]), reverse=True)

        pruned_tags = []
        current_vote_count = None

        for tag_info in sorted_tags:
            tag_count = int(tag_info[MBDataField.COUNT])

            if len(pruned_tags) < min_nb_tags or tag_count == current_vote_count:
                pruned_tags.append(tag_info[MBDataField.NAME])
                current_vote_count = tag_count
            else:
                break

        return pruned_tags

    def __str__(self) -> str:
        return f"""{self.__class__.__name__} "{self.name}'s" (MBID {self.mbid})"""


class ArtistPageProperties(TypedDict):
    """(Unused) Typed dictionary for Artist page properties."""

    name: dict[Literal[PagePropertyType.TITLE], list[dict[PropertyField, Any]]]
    mb_name: dict[Literal[PagePropertyType.RICH_TEXT], list[dict[PropertyField, Any]]]
    alias: dict[Literal[PagePropertyType.RICH_TEXT], list[dict[PropertyField, Any]]]
    type: dict[Literal[PagePropertyType.SELECT], dict[Literal[PropertyField.NAME], str]]
    area: dict[Literal[PagePropertyType.SELECT], dict[Literal[PropertyField.NAME], str]]
    start_year: dict[Literal[PagePropertyType.NUMBER], int]
    genres: dict[
        Literal[PagePropertyType.MULTI_SELECT], list[dict[Literal[PropertyField.NAME], str]]
    ]
    thumbnail: dict[PropertyField, Any]
    rating: dict[Literal[PagePropertyType.NUMBER], int]


@dataclass(frozen=True)
class Artist(MusicBrainzEntity):
    """Artist dataclass representing a page in the Artist database in Notion."""

    name: str
    mb_name: str
    aliases: list[str]
    type: str
    area: str
    start_year: int
    tags: list[str]
    thumbnail: str
    rating: int

    def to_page_properties(self) -> dict[ArtistDBProperty, dict[PagePropertyType, Any]]:
        """Format the artist data to Notion page properties format."""
        return {
            # ArtistDBProperty.NAME: format_title([format_text(self.name)]),
            ArtistDBProperty.MB_NAME: format_rich_text([format_text(self.mb_name)]),
            ArtistDBProperty.ALIAS: format_rich_text([format_text("".join(self.aliases))]),
            ArtistDBProperty.TYPE: format_select(self.type),
            ArtistDBProperty.AREA: format_select(self.area),
            ArtistDBProperty.START_YEAR: format_number(self.start_year),
            ArtistDBProperty.TAGS: format_multi_select(self.tags),
            ArtistDBProperty.THUMBNAIL: format_file([
                format_external_file(
                    f"{self.name} thumbnail (source: {ARTIST_THUMBNAIL_PROVIDER})",
                    self.thumbnail,
                )
            ]),
            ArtistDBProperty.RATING: format_number(self.rating),
            ArtistDBProperty.TO_UPDATE: format_checkbox(False),
        }  # type: ignore  # TODO? Use TypedDict to avoid this ignore

    @classmethod
    def from_musicbrainz_data(
        cls, notion_name: str, data: dict[str, Any], min_nb_tags: int
    ) -> Artist:
        """
        Create an Artist instance from MusicBrainz data.

        Args:
            notion_name (str): The name of the artist's page in Notion.
            data (dict[str, Any]): The dictionary of artist data from MusicBrainz.
            min_nb_tags (int): Minimum number of tags to select. There might
                be more tags selected if there are multiple tags with the
                same vote count.

        Returns:
            Artist: The Artist instance created from the MusicBrainz data.
        """
        tag_list = data.get(MBDataField.TAG_LIST, [])

        return cls(
            mbid=data[MBDataField.MBID],
            name=notion_name,
            mb_name=data[MBDataField.NAME],
            aliases=[
                alias_info[MBDataField.ALIAS]
                for alias_info in data.get(MBDataField.ALIAS_LIST) or []
            ],
            type=data[MBDataField.TYPE],
            area=data[EntityType.AREA][MBDataField.NAME] if data[EntityType.AREA] else "",
            start_year=int(data[MBDataField.LIFE_SPAN][MBDataField.BEGIN])
            if data[MBDataField.LIFE_SPAN]
            else 0,
            tags=cls.select_tags(tag_list, min_nb_tags),
            thumbnail=TEST_URL,  # TODO: Fetch thumbnail from MusicBrainz
            rating=int(data[EntityType.RATING][EntityType.RATING]),
        )

    def __str__(self) -> str:
        return super().__str__()


# %% === Functions === #
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

ARTIST_DB_ID = os.getenv(EnvironmentVar.ARTIST_DB_ID, "")
RELEASE_DB_ID = os.getenv(EnvironmentVar.RELEASE_DB_ID, "")
RECORDING_DB_ID = os.getenv(EnvironmentVar.RECORDING_DB_ID, "")

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


def update_artists_from_notion(notion_client: Client) -> None:
    """Query Notion for artists to update, fetch MusicBrainz data, and update Notion pages."""
    artists_to_update = query_notion_for_updates()

    if not artists_to_update:
        logger.info("No artists need to be updated.")
        return

    logger.info(f"Found {len(artists_to_update)} artists to update.")

    for artist_notion_data in artists_to_update:
        artist_page_id = artist_notion_data["id"]
        artist_page_name = artist_notion_data["properties"]["Name"]["title"][0]["text"]["content"]
        artist_properties = artist_notion_data["properties"]
        mbid = artist_properties["mbid"]["rich_text"][0]["text"]["content"]

        logger.info(f"Updating artist with MBID: {mbid}")

        # Fetch data from MusicBrainz
        artist_mb_data = fetch_artist_data(mbid)

        if artist_mb_data:
            artist = Artist.from_musicbrainz_data(
                artist_page_name, artist_mb_data, MIN_NB_TAGS
            )
            artist.update_notion_page(notion_client, ARTIST_DB_ID, ARTIST_PAGE_ICON)
            logger.success(f"Successfully updated {artist}")

        else:
            logger.error(f"Failed to update artist with MBID {mbid}")


if __name__ == "__main__":
    update_artists_from_notion(notion_client)
