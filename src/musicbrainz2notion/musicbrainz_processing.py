"""Module for fetching and processing MusicBrainz data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import musicbrainzngs
from loguru import logger

from musicbrainz2notion.musicbrainz_utils import (
    MBID,
    CanonicalDataHeader,
    EntityType,
    IncludeOption,
    MBDataDict,
    MBDataField,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd


def fetch_MB_entity_data(
    entity_type: EntityType,
    mbid: str,
    includes: list[IncludeOption],
    release_type: Sequence[str] | None = None,
    release_status: Sequence[str] | None = None,
) -> MBDataDict | None:
    """
    Fetch entity data from MusicBrainz for a given entity MBID.

    Args:
        entity_type (EntityType): The type of entity (artist, release, recording).
        mbid (str): The MusicBrainz ID (mbid) of the entity.
        includes (list[IncludeOption]): List of includes to fetch specific details.
        release_type (list[str] | None): List of release types to include in the
            response. Defaults to None (no filtering).
        release_status (list[str] | None): List of release statuses to include i
            n the response. Defaults to None (no filtering).

    Returns:
        MBDataDict | None: The dictionary of entity data from MusicBrainz. None if there was an error.
    """
    logger.info(f"Fetching {entity_type} data for mbid {mbid}")

    if release_type is None:
        release_type = []
    if release_status is None:
        release_status = []

    # Determine the correct API call based on the entity type
    match entity_type:
        case EntityType.ARTIST:
            get_func = musicbrainzngs.get_artist_by_id
        case EntityType.RELEASE:
            get_func = musicbrainzngs.get_release_by_id
        case EntityType.RECORDING:
            get_func = musicbrainzngs.get_recording_by_id
        case _:
            logger.error(f"Unsupported entity type: {entity_type}")
            return None

    try:
        result = get_func(
            mbid,
            includes=includes,
            release_type=release_type,
            release_status=release_status,
        )
    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching {entity_type.value} data from MusicBrainz for {mbid}: {exc}")
        return None
    else:
        entity_data: MBDataDict = result[entity_type]
        entity_name = entity_data.get(
            "name", entity_data.get("title", f"!! name_ not_found !! (no 'name' or 'title' key??)")
        )

        logger.info(f"Fetched {entity_type} data for {entity_name} (mbid {mbid})")

        return entity_data


def fetch_artist_data(mbid: str, release_type: Sequence[str] | None = None) -> MBDataDict | None:
    """Fetch artist data from MusicBrainz for the given artist mbid."""
    return fetch_MB_entity_data(
        entity_type=EntityType.ARTIST,
        mbid=mbid,
        includes=[
            IncludeOption.ALIASES,
            IncludeOption.TAGS,
            IncludeOption.RATINGS,
        ],
        release_type=release_type,
    )


def fetch_release_data(
    mbid: str,
    release_type: Sequence[str] | None = None,
    release_status: Sequence[str] | None = None,
) -> MBDataDict | None:
    """Fetch release data from MusicBrainz for a given release MBID."""
    return fetch_MB_entity_data(
        entity_type=EntityType.RELEASE,
        mbid=mbid,
        includes=[
            IncludeOption.TAGS,
            IncludeOption.RECORDINGS,
            IncludeOption.ARTIST_CREDITS,
        ],
        release_type=release_type,
        release_status=release_status,
    )


def fetch_recordings_data(mbid: str) -> MBDataDict | None:
    """Fetch recording data from MusicBrainz for a given recording MBID."""
    return fetch_MB_entity_data(
        entity_type=EntityType.RECORDING,
        mbid=mbid,
        includes=[
            IncludeOption.ARTIST_CREDITS,
            IncludeOption.TAGS,
            IncludeOption.RATINGS,
        ],
    )


# TODO: Add artist name for better logging?
def browse_release_groups_by_artist(
    artist_mbid: str,
    release_type: Sequence[str] | None = None,
    secondary_type_exclude: Sequence[str] | None = None,
    browse_limit: int = 100,
) -> list[MBDataDict] | None:
    """
    Browse and return a list of all release groups by an artist from MusicBrainz.

    Args:
        artist_mbid (str): The MusicBrainz ID (mbid) of the artist.
        release_type (list[str] | None): List of release types to filter.
            Defaults to None (no filtering).
        secondary_type_exclude (list[str] | None): List of secondary types to
            exclude.
        browse_limit (int): Maximum number of release groups to retrieve per
            request (max is 100).

    Returns:
        list[MBDataDict] | None: A list of release groups from MusicBrainz. None
            if there was an error while fetching the data.
    """
    logger.info(f"Browsing artist's release groups for mbid {artist_mbid}")

    if release_type is None:
        release_type = []
    if secondary_type_exclude is None:
        secondary_type_exclude = []
    offset = 0
    page = 1
    release_groups = []
    nb_results = browse_limit

    # TODO: Reimplement with try except else inside the loop
    # Continue browsing until we fetch all release groups
    while nb_results >= browse_limit:
        logger.info(f"Fetching page number {page}")

        try:
            result = musicbrainzngs.browse_release_groups(
                artist=artist_mbid,
                includes=[IncludeOption.RATINGS],
                release_type=release_type,
                limit=browse_limit,
                offset=offset,
            )
        except musicbrainzngs.WebServiceError as exc:
            logger.error(
                f"Error fetching release groups from MusicBrainz for mbid {artist_mbid}: {exc}"
            )
            return None
        else:
            page_release_groups: list[MBDataDict] = result.get("release-group-list", [])

            filtered_release_groups = [
                release_group
                for release_group in page_release_groups
                if not any(
                    secondary_type.lower() in secondary_type_exclude
                    for secondary_type in release_group.get(MBDataField.SECONDARY_TYPES, [])
                )
            ]
            release_groups.extend(filtered_release_groups)

            nb_results = len(page_release_groups)
            offset += browse_limit
            page += 1

    return release_groups


def get_release_group_to_canonical_release_map(
    release_group_mbids: Sequence[str], canonical_release_df: pd.DataFrame
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


def get_canonical_release_to_canonical_recording_map(
    canonical_release_mbids: Sequence[str], canonical_recording_df: pd.DataFrame
) -> dict[MBID, list[MBID]]:
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


# === Data extraction functions ===
def get_rating(entity_data: MBDataDict) -> int | None:
    """
    Extract the rating from a MusicBrainz entity data dictionary.

    Args:
        entity_data (MBDataDict): A MusicBrainz entity data dictionary.

    Returns:
        int | None: The rating of the entity, or None if not available.
    """
    rating_dict = entity_data.get("rating")

    return int(rating_dict["rating"]) if rating_dict else None


def get_start_year(entity_data: MBDataDict) -> int | None:
    """TODO."""
    life_span_dict = entity_data.get("life-span")

    return int(life_span_dict["begin"]) if life_span_dict else None
