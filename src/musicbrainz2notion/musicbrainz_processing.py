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


def fetch_artist_data(mbid: str, release_type: Sequence[str] | None = None) -> MBDataDict | None:
    """
    Fetch artist data from MusicBrainz for the given artist mbid.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the artist.
        release_type (list[str] | None): List of release types to include in the
            response.
            Defaults to None (no filtering).

    Returns:
        MBDataDict | None: The dictionary of artist data from MusicBrainz. None if
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
    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching artist data from MusicBrainz for {mbid}: {exc}")
        return None

    else:
        artist_data: MBDataDict = result[EntityType.ARTIST]
        logger.info(f"Fetched artist data for {artist_data["name"]} (mbid {mbid})")

        return artist_data


# TODO: Check if we need to get the individual release group data with result[EntityType.RELEASE_GROUP]
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

    try:
        # Continue browsing until we fetch all release groups
        while nb_results >= browse_limit:
            logger.info(f"Fetching page number {page}")

            result = musicbrainzngs.browse_release_groups(
                artist=artist_mbid,
                includes=[IncludeOption.RATINGS],
                release_type=release_type,
                limit=browse_limit,
                offset=offset,
            )
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

        logger.info(f"Fetched {len(release_groups)} release groups for mbid {artist_mbid}")
    except musicbrainzngs.WebServiceError as exc:
        logger.error(
            f"Error fetching release groups from MusicBrainz for mbid {artist_mbid}: {exc}"
        )

        release_groups = None

    return release_groups


def fetch_release_data(
    mbid: str,
    release_type: Sequence[str] | None = None,
    release_status: Sequence[str] | None = None,
) -> MBDataDict | None:
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
        MBDataDict | None: The release data from MusicBrainz. Returns None if
            there was an error while fetching the data.
    """
    logger.info(f"Fetching release data for mbid {mbid}")

    if release_type is None:
        release_type = []
    if release_status is None:
        release_status = []

    try:
        result = musicbrainzngs.get_release_by_id(
            mbid,
            includes=[
                IncludeOption.TAGS,
                IncludeOption.RECORDINGS,
                IncludeOption.ARTIST_CREDITS,
            ],
            release_type=release_type,
            release_status=release_status,
        )
    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching release data from MusicBrainz for {mbid}: {exc}")
        return None

    else:
        release_data: MBDataDict = result[EntityType.RELEASE]
        logger.info(f"Fetched release data for {release_data["title"]} (mbid {mbid})")

    return release_data


def fetch_recordings_data(mbid: str) -> MBDataDict | None:
    """
    Fetch recording data from MusicBrainz for a given recording MBID.

    The function retrieves additional information about the recording, such as
    artist credits, tags, and rating.

    Args:
        mbid (str): The MusicBrainz ID (mbid) of the recording.

    Returns:
        MBDataDict | None: The recording data from MusicBrainz. Returns None if
            there was an error while fetching the data.
    """
    logger.info(f"Fetching recording data for mbid {mbid}")

    try:
        result = musicbrainzngs.get_recording_by_id(
            mbid,
            includes=[
                IncludeOption.ARTIST_CREDITS,
                IncludeOption.TAGS,
                IncludeOption.RATINGS,
            ],
        )
        recording_data: MBDataDict = result[EntityType.RECORDING]

        logger.info(f"Fetched recording data for {recording_data[MBDataField.TITLE]} (mbid {mbid})")

    except musicbrainzngs.WebServiceError as exc:
        logger.error(f"Error fetching recording data from MusicBrainz for {mbid}: {exc}")
        recording_data = None

    return recording_data


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
