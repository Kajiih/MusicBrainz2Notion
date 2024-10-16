"""Module for MusicBrainz2Notion database entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypedDict

from loguru import logger

from musicbrainz2notion.__about__ import __app_name__, __email__, __version__
from musicbrainz2notion.musicbrainz_utils import (
    MBID,
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
    format_relation,
    format_rich_text,
    format_select,
    format_text,
    format_title,
    format_url,
)
from musicbrainz2notion.utils import BASE_MUSICBRAINZ_URL

if TYPE_CHECKING:
    from notion_client import Client

# === Temp config === #
ARTIST_THUMBNAIL_PROVIDER = "Wikipedia"  # "fanart.tv" # TODO: Create enum
ADD_TRACK_COVER = True

TEST_URL = "https://images.fanart.tv/fanart/superbus-50576f8295220.jpeg"
# TODO: Implement thumbnails and cover fetching


# %% === Enums === #
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
    MB_URL = "MusicBrainz URL"


class ReleaseDBProperty(StrEnum):
    """Release/release group database property keys in Notion."""

    NAME = "Name"  # Database key  # MB_NAME (ARTIST)
    MBID = "mbid"
    ARTIST = "Artist"
    THUMBNAIL = "Thumbnail"
    TYPE = "Type"
    FIRST_RELEASE_YEAR = "First release year"
    # GENRES = "Genre(s)"
    TAGS = "Tags"
    LANGUAGE = "Language"  # Taken from iso 639-3
    RATING = "Rating"
    MB_URL = "MusicBrainz URL"


class TrackDBProperty(StrEnum):
    """Track/Recording database property keys in Notion."""

    TITLE = "Title"  # Database key  # MB_NAME (RELEASE)
    MBID = "mbid"
    RELEASE = "Release"
    THUMBNAIL = "Thumbnail"
    TRACK_NUMBER = "Track number"
    LENGTH = "Length"
    FIRST_RELEASE_YEAR = "First release year"
    # GENRES = "Genre(s)"
    TAGS = "Tags"
    RATING = "Rating"
    TRACK_ARTIST = "Track artist(s)"
    MB_URL = "MusicBrainz URL"


type NotionBDProperty = ArtistDBProperty | ReleaseDBProperty | TrackDBProperty


# %% === Database Entities === #
@dataclass(frozen=True)
class MusicBrainzEntity(ABC):
    """Base class for MusicBrainz2Notion entities, representing a page in a Notion database."""

    mbid: MBID
    name: str
    thumbnail: str

    entity_type: ClassVar[EntityType]

    @property
    def mb_url(self) -> str:
        """MusicBrainz URL of the entity."""
        return str(BASE_MUSICBRAINZ_URL / self.entity_type.value / self.mbid)

    @abstractmethod
    def to_page_properties(
        self, mbid_to_page_id_map: dict[str, str]
    ) -> dict[NotionBDProperty, dict[PagePropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[NotionBDProperty, Any]): The formatted
                properties dictionary for Notion API.
        """

    def update_notion_page(
        self,
        notion_api: Client,
        database_id: str,
        mbid_to_page_id_map: dict[str, str],
        icon_emoji: str,
    ) -> None:
        """
        Update the entity's page in the Notion database.

        Args:
            notion_api (Client): Notion API client.
            database_id (str): Notion database ID.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.
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
                    properties=self.to_page_properties(mbid_to_page_id_map),
                    icon=format_emoji(icon_emoji),
                )

            else:
                logger.info(f"{self} not found, creating new page.")

                notion_api.pages.create(
                    parent={"database_id": database_id},
                    properties=self.to_page_properties(mbid_to_page_id_map),
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

    aliases: list[str]
    type: str
    area: str
    start_year: int
    tags: list[str]
    rating: int

    # == Class variables == #
    entity_type = EntityType.ARTIST

    def to_page_properties(
        self,
        mbid_to_page_id_map: dict[str, str],  # noqa: ARG002
    ) -> dict[NotionBDProperty, dict[PagePropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[NotionBDProperty, Any]): The formatted
                properties dictionary for Notion API.
        """
        return {
            ArtistDBProperty.NAME: format_title([format_text(self.name)]),
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
            ArtistDBProperty.MB_URL: format_url(self.mb_url),
            ArtistDBProperty.TO_UPDATE: format_checkbox(False),
        }  # type: ignore  # TODO? Use TypedDict to avoid this ignore

    @classmethod
    def from_musicbrainz_data(cls, artist_data: dict[str, Any], min_nb_tags: int) -> Artist:
        """
        Create an Artist instance from MusicBrainz data.

        Args:
            artist_data (dict[str, Any]): The dictionary of artist data from MusicBrainz.
            min_nb_tags (int): Minimum number of tags to select. There might
                be more tags selected if there are multiple tags with the
                same vote count.

        Returns:
            Artist: The Artist instance created from the MusicBrainz data.
        """
        tag_list = artist_data.get(MBDataField.TAG_LIST, [])

        return cls(
            mbid=artist_data[MBDataField.MBID],
            name=artist_data[MBDataField.NAME],
            aliases=[
                alias_info[MBDataField.ALIAS]
                for alias_info in artist_data.get(MBDataField.ALIAS_LIST) or []
            ],
            type=artist_data[MBDataField.TYPE],
            area=artist_data[EntityType.AREA][MBDataField.NAME]
            if artist_data[EntityType.AREA]
            else "",
            start_year=int(artist_data[MBDataField.LIFE_SPAN][MBDataField.BEGIN])
            if artist_data[MBDataField.LIFE_SPAN]
            else 0,
            tags=cls.select_tags(tag_list, min_nb_tags),
            thumbnail=TEST_URL,  # TODO: Fetch thumbnail from Wikipedia/fanart.tv
            rating=int(artist_data[MBDataField.RATING][MBDataField.RATING]),
        )

    def __str__(self) -> str:
        return super().__str__()


@dataclass(frozen=True)
class Release(MusicBrainzEntity):
    """Release dataclass representing a page in the Release database in Notion."""

    artist_mbids: list[MBID]
    type: str
    first_release_year: int
    tags: list[str]
    language: str
    rating: int

    # == Class variables == #
    entity_type = EntityType.RELEASE

    def to_page_properties(
        self,
        mbid_to_page_id_map: dict[str, str],
    ) -> dict[NotionBDProperty, dict[PagePropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[NotionBDProperty, Any]): The formatted
                properties dictionary for Notion API.
        """
        artist_pages_ids = [mbid_to_page_id_map[mbid] for mbid in self.artist_mbids]
        return {
            ReleaseDBProperty.NAME: format_title([format_text(self.name)]),
            ReleaseDBProperty.ARTIST: format_relation(artist_pages_ids),
            ReleaseDBProperty.TYPE: format_select(self.type),
            ReleaseDBProperty.FIRST_RELEASE_YEAR: format_number(self.first_release_year),
            ReleaseDBProperty.TAGS: format_multi_select(self.tags),
            ReleaseDBProperty.LANGUAGE: format_select(self.language),
            ReleaseDBProperty.THUMBNAIL: format_file([
                format_external_file(f"{self.name} cover", self.thumbnail)
            ]),
            ReleaseDBProperty.RATING: format_number(self.rating),
            ReleaseDBProperty.MB_URL: format_url(self.mb_url),
        }  # type: ignore  # TODO? Use TypedDict to avoid this ignore

    @classmethod
    def from_musicbrainz_data(cls, release_data: dict[str, Any], min_nb_tags: int) -> Release:
        """
        Create a Release instance from MusicBrainz data.

        Args:
            release_data (dict[str, Any]): The dictionary of release data from
                MusicBrainz. Ratings, type and first release year data of the
                release group have to be added to this dictionary.
            min_nb_tags (int): Minimum number of tags to select. There might
                be more tags selected if there are multiple tags with the
                same vote count.

        Returns:
            Release: The Release instance created from the MusicBrainz data.
        """
        tag_list = release_data.get(MBDataField.TAG_LIST, [])
        first_release_year = (
            int(release_data[MBDataField.FIRST_RELEASE_DATE].split("-")[0])
            if release_data[MBDataField.FIRST_RELEASE_DATE]
            else 0
        )

        return cls(
            mbid=release_data[MBDataField.MBID],
            artist_mbids=[
                artist_data[MBDataField.ARTIST][MBDataField.MBID]
                for artist_data in release_data[MBDataField.ARTIST_CREDIT]
                if isinstance(artist_data, dict)
            ],
            name=release_data[MBDataField.TITLE],
            type=release_data[MBDataField.TYPE],
            first_release_year=first_release_year,
            tags=cls.select_tags(tag_list, min_nb_tags),
            language=release_data[MBDataField.TEXT_REPRESENTATION][MBDataField.LANGUAGE],
            thumbnail=TEST_URL,  # TODO: Fetch cover from MusicBrainz
            rating=int(release_data[MBDataField.RATING][MBDataField.RATING]),
        )


# TODO: Add ratings to release data
