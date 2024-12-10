"""Module for MusicBrainz2Notion database entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, override

from loguru import logger

from musicbrainz2notion.__about__ import __app_name__, __author_email__, __version__
from musicbrainz2notion.config import global_settings
from musicbrainz2notion.musicbrainz_data_retrieval import (
    fetch_artist_data,
    fetch_recording_data,
    fetch_release_data,
    get_rating,
    get_start_year,
)
from musicbrainz2notion.musicbrainz_utils import (
    BASE_MUSICBRAINZ_URL,
    MBID,
    CoverSize,
    EntityType,
    MBDataDict,
    TagDict,
)
from musicbrainz2notion.notion_utils import (
    NotionResponse,
    PropertyField,
    PropertyType,
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
from musicbrainz2notion.thumbnails_retrieval import (
    fetch_artist_thumbnail,
    get_release_group_cover_url,
)

if TYPE_CHECKING:
    from notion_client import Client

logger = logger.opt(colors=True)
logger.opt = partial(logger.opt, colors=True)


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
    AUTO_ADDED = "Auto-added"
    # Other properties
    RELEASES = "Releases"
    TRACKS = "Tracks"


class ReleaseDBProperty(StrEnum):
    """Release/release group database property keys in Notion."""

    NAME = "Name"  # Database key
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
    # Other properties
    TRACKS = "Tracks"


class TrackDBProperty(StrEnum):
    """Track/Recording database property keys in Notion."""

    NAME = "Name"  # Database key
    MBID = "mbid"
    RELEASE = "Release"
    THUMBNAIL = "Thumbnail"
    TRACK_NUMBER = "Track number"
    LENGTH = "Length"
    # FIRST_RELEASE_YEAR = "First release year"
    # GENRES = "Genre(s)"
    TAGS = "Tags"
    RATING = "Rating"
    ARTIST = "Artist"  # Rollup from Release
    TRACK_ARTIST = "Track artist(s)"
    MB_URL = "MusicBrainz URL"


type NotionBDProperty = ArtistDBProperty | ReleaseDBProperty | TrackDBProperty


# %% === Database Entities === #
@dataclass(frozen=True, kw_only=True, slots=True)
class MusicBrainzEntity(ABC):
    """Base class for MusicBrainz2Notion entities, representing a page in a Notion database."""

    mbid: MBID
    name: str
    thumbnail: str | None = None

    entity_type: ClassVar[EntityType]
    icon: ClassVar[str]  # Only emoji are supported for now

    @property
    def mb_url(self) -> str:
        """MusicBrainz URL of the entity."""
        return str(BASE_MUSICBRAINZ_URL / self.entity_type.value / self.mbid)

    @abstractmethod
    def to_page_properties(
        self, mbid_to_page_id_map: dict[str, str]
    ) -> dict[NotionBDProperty, dict[PropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[NotionBDProperty, Any]): The formatted
                properties dictionary for Notion API.
        """

    def synchronize_notion_page(
        self,
        notion_api: Client,
        database_ids: dict[EntityType, str],
        mbid_to_page_id_map: dict[str, str],
        min_nb_tags: int,
        fanart_api_key: str | None,
    ) -> NotionResponse:
        """
        Update the entity's page in the Notion database.

        The entity's related pages missing from the notion database are add and
        their MBIDs and page IDs are added to the mapping.

        Args:
            notion_api (Client): Notion API client.
            database_ids (dict[EntityType, str]): Dictionary mapping entity
                types to their respective Notion database IDs.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.
            min_nb_tags (int): Minimum number of tags to be added to the
                missing related pages.
            fanart_api_key (str | None): Fanart.tv API key.
        """
        logger.debug(f"Synchronizing {self.str_colored} page in Notion.")
        database_id = database_ids[self.entity_type]

        self._add_missing_related_pages(
            notion_api=notion_api,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            min_nb_tags=min_nb_tags,
            fanart_api_key=fanart_api_key,
        )

        if self.mbid in mbid_to_page_id_map:
            # The page already exists in the database
            logger.info(f"{self.str_colored} found in Notion, updating page.")
            page_id = mbid_to_page_id_map[self.mbid]

            try:
                response: Any = notion_api.pages.update(
                    page_id=page_id,
                    properties=self.to_page_properties(mbid_to_page_id_map),
                    icon=format_emoji(self.icon),
                )
            except Exception:
                logger.exception(f"Error updating {self.str_colored}'s page in Notion")
                raise

        else:
            # Create new page in the database
            logger.info(f"{self.str_colored} not found in Notion, creating new page.")

            try:
                response = notion_api.pages.create(
                    parent={"database_id": database_id},
                    properties=self.to_page_properties(mbid_to_page_id_map),
                    icon=format_emoji(self.icon),
                )
            except Exception:
                logger.exception(f"Error creating {self.str_colored}'s page in Notion")
                raise

            else:
                mbid_to_page_id_map[self.mbid] = response[PropertyField.ID]

        return response

    # TODO: Check if we keep this as a static method
    @staticmethod
    def _add_missing_related_pages(
        notion_api: Client,
        database_ids: dict[EntityType, str],
        mbid_to_page_id_map: dict[str, str],
        min_nb_tags: int,
        fanart_api_key: str | None,
    ) -> None:
        """
        Add the related pages of the entity in the Notion database.

        By default, does nothing.

        Missing related pages MBIDs and page IDs are added to the mapping.

        Args:
            notion_api (Client): Notion API client.
            database_ids (dict[EntityType, str]): Dictionary mapping entity
                types to their respective Notion database IDs.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            fanart_api_key (str | None): Fanart.tv API key.
        """
        del notion_api, database_ids, mbid_to_page_id_map, min_nb_tags, fanart_api_key

    @staticmethod
    def _select_tags(tag_list: list[TagDict], min_nb_tags: int) -> list[str]:
        """
        Select tags to add to the entity.

        Args:
            tag_list (list[TagDict]): List of tags with their counts
                coming from MusicBrainz API.
            min_nb_tags (int): Minimum number of tags to select. There might
                be more tags selected if there are multiple tags with the
                same vote count.

        """
        # Sort the tags by count in descending order
        sorted_tags = sorted(tag_list, key=lambda tag: int(tag["count"]), reverse=True)

        pruned_tags = []
        current_vote_count = None

        for tag_info in sorted_tags:
            tag_count = int(tag_info["count"])

            if len(pruned_tags) < min_nb_tags or tag_count == current_vote_count:
                pruned_tags.append(tag_info["name"])
                current_vote_count = tag_count
            else:
                break

        return pruned_tags

    # TODO? Delete this function?
    @staticmethod
    def _add_entity_type_missing_related(
        entity_mbids: list[MBID],
        entity_cls: type[MusicBrainzEntity],
        notion_api: Client,
        database_ids: dict[EntityType, str],
        mbid_to_page_id_map: dict[str, str],
        min_nb_tags: int,
        fanart_api_key: str | None,
    ) -> None:
        """
        Add the missing related pages of a given entity type to the Notion database.

        Only adding missing artists is supported for now.

        Args:
            entity_mbids (list[MBID]): List of MBIDs for the related entities.
            entity_cls (type[MusicBrainzEntity]): Class of the related entity
                (Artist or Recording are supported).
            notion_api (Client): Notion API client.
            database_ids (dict[EntityType, str]): Dictionary mapping entity
                types to their respective Notion database IDs.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to page IDs
                in the Notion database.
            min_nb_tags (int): Minimum number of tags to select for the entity.
            fanart_api_key (str | None, optional): Fanart API key. Defaults to None.
        """
        missing_entity_mbids = set(entity_mbids) - set(mbid_to_page_id_map.keys())

        # Determine the correct API call based on the entity type
        # TODO? Replace those functions with variants specific for missing pages, with less includes
        match entity_cls.entity_type:
            case EntityType.ARTIST:
                fetch_func = fetch_artist_data
                arg_name = "artist_data"
                kwargs: dict[str, Any] = {
                    "auto_added": True,
                    "fanart_api_key": fanart_api_key,
                }
            # case EntityType.RELEASE:
            #     fetch_func = fetch_release_data.get_release_by_id
            # case EntityType.RECORDING:
            #     fetch_func = fetch_recording_data
            #     arg_name = "recording_data"
            case _:
                logger.error(
                    f"Unsupported entity type for adding missing related pages: {entity_cls.entity_type}"
                )
                return

        # Fetch missing entity data from MusicBrainz and create Notion pages for them
        for missing_entity_mbid in missing_entity_mbids:
            entity_data = fetch_func(missing_entity_mbid)
            if entity_data is None:
                continue

            # Create and upload missing entity page to Notion
            kwargs[arg_name] = entity_data
            entity_instance = entity_cls.from_musicbrainz_data(
                min_nb_tags=min_nb_tags,
                **kwargs,
            )

            _ = entity_instance.synchronize_notion_page(
                notion_api=notion_api,
                database_ids=database_ids,
                mbid_to_page_id_map=mbid_to_page_id_map,
                min_nb_tags=min_nb_tags,
                fanart_api_key=fanart_api_key,
            )

    @classmethod
    @abstractmethod
    def from_musicbrainz_data(
        cls,
        *,
        min_nb_tags: int,
        **kwargs: MBDataDict | bool | str,
    ) -> MusicBrainzEntity:
        """
        Create an instance of the entity from MusicBrainz data.

        Args:
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            **kwargs (MBDataDict | bool): Keyword arguments
                containing dictionaries of MusicBrainz data or boolean values.

        Returns:
            MusicBrainzEntity: An instance of a subclass of MusicBrainzEntity.
        """

    def _get_thumbnail_file(self) -> dict:
        """TODO."""
        if self.thumbnail is not None:
            external_files = [format_external_file(f"{self.name} thumbnail", self.thumbnail)]
        else:
            external_files = []

        return format_file(external_files)

    @override
    def __str__(self) -> str:
        return f"""{self.__class__.__name__} "{self.name}'s" (MBID {self.mbid})"""

    @property
    def str_colored(self) -> str:
        """Return the formatted string representation of the entity, with colors and bolding."""
        return f"{self.__class__.__name__} <green>{self.name}</green> <dim>(MBID {self.mbid})</dim>"


@dataclass(frozen=True, kw_only=True, slots=True)
class Artist(MusicBrainzEntity):
    """Artist dataclass representing a page in the Artist database in Notion."""

    EMPTY_TYPE_PLACEHOLDER: str = "Unknown"
    EMPTY_AREA_PLACEHOLDER: str = "Unknown"
    EMPTY_LANGUAGE_PLACEHOLDER: str = "Unknown"
    type: str | None = None
    aliases: list[str] = field(default_factory=list)
    area: str | None = None
    start_year: int | None = None
    tags: list[str] = field(default_factory=list)
    rating: float | None = None
    auto_added: bool = False

    # == Class variables == #

    entity_type = EntityType.ARTIST
    icon = global_settings.ARTIST_ICON

    @classmethod
    def from_musicbrainz_data(
        cls,
        *,
        artist_data: MBDataDict,
        min_nb_tags: int,
        auto_added: bool = False,
        fanart_api_key: str | None = None,
    ) -> Artist:
        """
        Create an Artist instance from MusicBrainz data.

        Args:
            artist_data (MBDataDict): The dictionary of artist data
                from MusicBrainz.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            auto_added (bool): Whether to toggle on the Auto-added property.
                Defaults to False.
            fanart_api_key (str | None): The API key for the Fanart.tv API.

        Returns:
            Artist: The Artist instance created from the MusicBrainz data.
        """
        tag_list = artist_data.get("tag-list", [])

        return cls(
            mbid=artist_data["id"],
            name=artist_data["name"],
            aliases=[alias_info["alias"] for alias_info in artist_data.get("alias-list", [])],
            type=artist_data.get("type"),
            area=artist_data.get("area", {}).get("name"),
            start_year=get_start_year(artist_data),
            tags=cls._select_tags(tag_list, min_nb_tags),
            thumbnail=fetch_artist_thumbnail(artist_data, fanart_api_key),
            rating=get_rating(artist_data),
            auto_added=auto_added,
        )

    def to_page_properties(
        self,
        mbid_to_page_id_map: dict[str, str],
    ) -> dict[ArtistDBProperty, dict[PropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[ArtistDBProperty, Any]): The formatted
                properties dictionary for Notion API.
        """
        del mbid_to_page_id_map  # Unused

        alias = format_rich_text([format_text(", ".join(self.aliases))])

        return {
            ArtistDBProperty.NAME: format_title([format_text(self.name)]),
            ArtistDBProperty.MBID: format_rich_text([
                format_text(self.mbid)
            ]),  # For artist added as relations
            ArtistDBProperty.ALIAS: alias,
            ArtistDBProperty.TYPE: format_select(
                self.type or global_settings.EMPTY_TYPE_PLACEHOLDER
            ),
            ArtistDBProperty.AREA: format_select(
                self.area or global_settings.EMPTY_AREA_PLACEHOLDER
            ),
            ArtistDBProperty.START_YEAR: format_number(self.start_year),
            ArtistDBProperty.TAGS: format_multi_select(self.tags),
            ArtistDBProperty.THUMBNAIL: self._get_thumbnail_file(),
            ArtistDBProperty.RATING: format_number(self.rating),
            ArtistDBProperty.MB_URL: format_url(self.mb_url),
            ArtistDBProperty.AUTO_ADDED: format_checkbox(self.auto_added),
        }  # pyright: ignore[reportReturnType]  # TODO? Use TypedDict to avoid this ignore


@dataclass(frozen=True, kw_only=True, slots=True)
class Release(MusicBrainzEntity):
    """Release dataclass representing a page in the Release database in Notion."""

    artist_mbids: list[MBID]
    type: str | None = None
    first_release_year: int | None = None
    tags: list[str] = field(default_factory=list)
    language: str | None = None
    rating: float | None = None

    # == Class variables == #
    entity_type = EntityType.RELEASE
    icon = global_settings.RELEASE_ICON

    @classmethod
    def from_musicbrainz_data(
        cls,
        *,
        release_data: MBDataDict,
        release_group_data: MBDataDict,
        min_nb_tags: int,
        cover_size: CoverSize,
    ) -> Release:
        """
        Create a Release instance from MusicBrainz data.

        Args:
            release_data (MBDataDict): The dictionary of release
                data from MusicBrainz.
            release_group_data (MBDataDict): The dictionary of
                release group data from MusicBrainz.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            cover_size (CoverSize): The size of the cover image in pixel.

        Returns:
            Release: The Release instance created from the MusicBrainz data.
        """
        tag_list = release_data.get("tag-list", [])

        artist_mbids = [
            artist_data["artist"]["id"]
            for artist_data in release_data["artist-credit"]
            if isinstance(artist_data, dict)
        ]

        first_release_year = release_group_data.get("first-release-date", "").split("-")[0]
        first_release_year = int(first_release_year) if first_release_year else None

        return cls(
            mbid=release_data["id"],
            artist_mbids=artist_mbids,
            name=release_data["title"],
            type=release_group_data.get("type"),
            first_release_year=first_release_year,
            tags=cls._select_tags(tag_list, min_nb_tags),
            language=release_data.get("text-representation", {}).get("language"),
            thumbnail=get_release_group_cover_url(release_group_data["id"], cover_size),
            rating=get_rating(release_group_data),
        )

    def to_page_properties(
        self,
        mbid_to_page_id_map: dict[str, str],
    ) -> dict[ReleaseDBProperty, dict[PropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[ReleaseDBProperty, Any]): The formatted
                properties dictionary for Notion API.
        """
        artist_pages_ids = [mbid_to_page_id_map[mbid] for mbid in self.artist_mbids]

        return {
            ReleaseDBProperty.MBID: format_rich_text([format_text(self.mbid)]),
            ReleaseDBProperty.NAME: format_title([format_text(self.name)]),
            ReleaseDBProperty.ARTIST: format_relation(artist_pages_ids),
            ReleaseDBProperty.TYPE: format_select(
                self.type or global_settings.EMPTY_TYPE_PLACEHOLDER
            ),
            ReleaseDBProperty.FIRST_RELEASE_YEAR: format_number(self.first_release_year),
            ReleaseDBProperty.TAGS: format_multi_select(self.tags),
            ReleaseDBProperty.LANGUAGE: format_select(
                self.language or global_settings.EMPTY_LANGUAGE_PLACEHOLDER
            ),
            ReleaseDBProperty.THUMBNAIL: self._get_thumbnail_file(),
            ReleaseDBProperty.RATING: format_number(self.rating),
            ReleaseDBProperty.MB_URL: format_url(self.mb_url),
        }  # pyright: ignore[reportReturnType]  # TODO? Use TypedDict to avoid this ignore

    def _add_missing_related_pages(
        self,
        notion_api: Client,
        database_ids: dict[EntityType, str],
        mbid_to_page_id_map: dict[str, str],
        min_nb_tags: int,
        fanart_api_key: str | None,
    ) -> None:
        """
        Add the missing artist pages of the release to the Notion database.

        Missing artist pages are supposed to come from release with several
        artists.

        Missing related pages MBIDs and page IDs are added to the mapping.

        Args:
            notion_api (Client): Notion API client.
            database_ids (dict[EntityType, str]): Dictionary mapping entity
                types to their respective Notion database IDs.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            fanart_api_key (str | None): Fanart API key.
        """
        self._add_entity_type_missing_related(
            entity_mbids=self.artist_mbids,
            entity_cls=Artist,
            notion_api=notion_api,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            min_nb_tags=min_nb_tags,
            fanart_api_key=fanart_api_key,
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class Recording(MusicBrainzEntity):
    """Recording dataclass representing a page in the Track database in Notion."""

    artist_mbids: list[MBID]
    release_mbids: list[MBID]
    track_number: str
    length: int | None = None  # Track length in milliseconds
    tags: list[str] = field(default_factory=list)
    rating: float | None = None

    # == Class variables == #
    entity_type = EntityType.RECORDING
    icon = global_settings.TRACK_ICON

    @classmethod
    def from_musicbrainz_data(
        cls,
        *,
        recording_data: MBDataDict,
        formatted_track_number: str,
        release: Release,
        min_nb_tags: int,
        add_thumbnail: bool,
    ) -> Recording:
        """
        Create a Recording instance from MusicBrainz data.

        Args:
            recording_data (MBDataDict): The dictionary of recording data
                from MusicBrainz.
            formatted_track_number (str): The formatted track number of the
                recording withing its release.
            release (Release): The Release instance to which the recording
                belongs.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            add_thumbnail (bool): Whether to add a thumbnail to the recording.

        Returns:
            Recording: The Recording instance created from the MusicBrainz data.
        """
        tag_list = recording_data.get("tag-list", [])

        release_mbids = [release["id"] for release in recording_data.get("release-list", [])]
        artist_mbids = [
            artist_data["artist"]["id"]
            for artist_data in recording_data["artist-credit"]
            if isinstance(artist_data, dict)
        ]

        return cls(
            mbid=recording_data["id"],
            name=recording_data["title"],
            artist_mbids=artist_mbids,
            release_mbids=release_mbids,
            track_number=formatted_track_number,
            length=int(length_str) if (length_str := recording_data.get("length")) else None,
            tags=cls._select_tags(tag_list, min_nb_tags),
            thumbnail=release.thumbnail if add_thumbnail else None,
            rating=get_rating(recording_data),
        )

    def to_page_properties(
        self,
        mbid_to_page_id_map: dict[str, str],
    ) -> dict[TrackDBProperty, dict[PropertyType, Any]]:
        """
        Convert the dataclass fields to Notion page properties format.

        Only releases already in the Notion database are added as relation.

        Args:
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.

        Returns:
            page_properties (dict[TrackDBProperty, Any]): The formatted
                properties dictionary for Notion API.
        """
        release_pages_ids = [
            page_id for mbid in self.release_mbids if (page_id := mbid_to_page_id_map.get(mbid))
        ]
        artist_pages_ids = [mbid_to_page_id_map[mbid] for mbid in self.artist_mbids]

        return {
            TrackDBProperty.MBID: format_rich_text([format_text(self.mbid)]),
            TrackDBProperty.NAME: format_title([format_text(self.name)]),
            TrackDBProperty.RELEASE: format_relation(release_pages_ids),
            TrackDBProperty.TRACK_ARTIST: format_relation(artist_pages_ids),
            TrackDBProperty.TRACK_NUMBER: format_rich_text([format_text(self.track_number)]),
            TrackDBProperty.LENGTH: format_number(self.length),
            TrackDBProperty.TAGS: format_multi_select(self.tags),
            TrackDBProperty.THUMBNAIL: self._get_thumbnail_file(),
            TrackDBProperty.RATING: format_number(self.rating),
            TrackDBProperty.MB_URL: format_url(self.mb_url),
        }  # pyright: ignore[reportReturnType]  # TODO? Use TypedDict to avoid this ignore

    def _add_missing_related_pages(
        self,
        notion_api: Client,
        database_ids: dict[EntityType, str],
        mbid_to_page_id_map: dict[str, str],
        min_nb_tags: int,
        fanart_api_key: str | None,
    ) -> None:
        """
        Add the missing artist of the recording to the Notion database.

        Missing related pages MBIDs and page IDs are added to the mapping.

        Args:
            notion_api (Client): Notion API client.
            database_ids (dict[EntityType, str]): Dictionary mapping entity
                types to their respective Notion database IDs.
            mbid_to_page_id_map (dict[str, str]): A mapping of MBIDs to
                page IDs in the Notion database.
            min_nb_tags (int): Minimum number of tags to select. If there are
                multiple tags with the same vote count, more tags may be added.
            fanart_api_key (str | None): Fanart API key.
        """
        self._add_entity_type_missing_related(
            entity_mbids=self.artist_mbids,
            entity_cls=Artist,
            notion_api=notion_api,
            database_ids=database_ids,
            mbid_to_page_id_map=mbid_to_page_id_map,
            min_nb_tags=min_nb_tags,
            fanart_api_key=fanart_api_key,
        )
