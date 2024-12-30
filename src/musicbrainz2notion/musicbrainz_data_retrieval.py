"""Module for fetching and processing MusicBrainz data."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import dateutil.parser
import musicbrainzngs  # pyright: ignore[reportMissingTypeStubs]
from loguru import logger

from musicbrainz2notion.musicbrainz_utils import (
    MBID,
    EntityType,
    IncludeOption,
    MBDataDict,
    MBDataField,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

logger = logger.opt(colors=True)
logger.opt = partial(logger.opt, colors=True)


MB_API_RATE_LIMIT_INTERVAL = 1  # Seconds
MB_API_REQUEST_PER_INTERVAL = 10


def initialize_musicbrainz_client(
    app_name: str,
    app_version: str,
    app_contact: str,
    rate_limit_interval: int = MB_API_RATE_LIMIT_INTERVAL,
    request_per_interval: int = MB_API_REQUEST_PER_INTERVAL,
) -> None:
    """
    Initialize the MusicBrainz API.

    Args:
        app_name (str): The name of the application.
        app_version (str): The version of the application.
        app_contact (str): The contact email for the application.
        rate_limit_interval (int): The rate limit interval in seconds. Defaults
            to MB_API_RATE_LIMIT_INTERVAL.
        request_per_interval (int): The number of requests per interval. Defaults to
            MB_API_REQUEST_PER_INTERVAL.
    """
    musicbrainzngs.set_useragent(app_name, app_version, app_contact)
    musicbrainzngs.set_rate_limit(rate_limit_interval, request_per_interval)


def fetch_MB_entity_data(
    entity_type: EntityType,
    mbid: MBID,
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
    logger.debug(f"Fetching {entity_type} data for mbid {mbid}")

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
        case EntityType.RELEASE_GROUP:
            get_func = musicbrainzngs.get_release_group_by_id
        case _:
            logger.error(f"Unsupported entity type for fetching MusicBrainz data: {entity_type}")
            return None

    try:
        result = get_func(
            mbid,
            includes=includes,
            release_type=release_type,
            release_status=release_status,
        )
    except musicbrainzngs.WebServiceError:
        logger.exception(f"Error fetching {entity_type.value} data from MusicBrainz for {mbid}")
        return None

    else:
        entity_data: MBDataDict = result[entity_type]
        entity_name = entity_data.get(
            "name", entity_data.get("title", f"!! name_ not_found !! (no 'name' or 'title' key??)")
        )

        logger.debug(
            f"Fetched {entity_type} data for <green>{entity_name}</> <dim>(mbid {mbid})</>"
        )

        return entity_data


def fetch_artist_data(mbid: MBID) -> MBDataDict | None:
    """Fetch artist data from MusicBrainz for the given artist mbid."""
    return fetch_MB_entity_data(
        entity_type=EntityType.ARTIST,
        mbid=mbid,
        includes=[
            IncludeOption.ALIASES,
            IncludeOption.TAGS,
            IncludeOption.RATINGS,
            IncludeOption.URL_RELS,
        ],
    )


def fetch_release_data(
    mbid: MBID,
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
    )


def fetch_recording_data(mbid: MBID) -> MBDataDict | None:
    """Fetch recording data from MusicBrainz for a given recording MBID."""
    return fetch_MB_entity_data(
        entity_type=EntityType.RECORDING,
        mbid=mbid,
        includes=[
            IncludeOption.ARTIST_CREDITS,
            IncludeOption.TAGS,
            IncludeOption.RATINGS,
            IncludeOption.RELEASES,
        ],
    )


def fetch_release_group_data(mbid: MBID) -> MBDataDict | None:
    """Fetch recording data from MusicBrainz for a given recording MBID."""
    return fetch_MB_entity_data(
        entity_type=EntityType.RELEASE_GROUP,
        mbid=mbid,
        includes=[IncludeOption.RELEASES],
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
    logger.debug(f"Browsing artist's release groups for mbid {artist_mbid}")

    if release_type is None:
        release_type = []
    if secondary_type_exclude is None:
        secondary_type_exclude = []
    offset = 0
    page = 1
    release_groups = []
    nb_results = browse_limit

    # Continue browsing until we fetch all release groups
    while nb_results >= browse_limit:
        logger.debug(f"Fetching page number {page}")

        try:
            result = musicbrainzngs.browse_release_groups(
                artist=artist_mbid,
                includes=[IncludeOption.RATINGS],
                release_type=release_type,
                limit=browse_limit,
                offset=offset,
            )
        except musicbrainzngs.WebServiceError:
            logger.exception(
                f"Error fetching release groups from MusicBrainz for mbid {artist_mbid}"
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

    logger.debug(f"{len(release_groups)} release groups found for mbid {artist_mbid}")

    return release_groups


# === Data extraction functions ===
def get_rating(entity_data: MBDataDict) -> float | None:
    """
    Extract the rating from a MusicBrainz entity data dictionary.

    Args:
        entity_data (MBDataDict): A MusicBrainz entity data dictionary.

    Returns:
        float | None: The rating of the entity, or None if not available.
    """
    rating_dict = entity_data.get("rating")

    return float(rating_dict["rating"]) if rating_dict else None


def get_start_year(entity_data: MBDataDict) -> int | None:
    """Extract the 4-digit start year from a MusicBrainz entity data dictionary."""
    life_span_dict = entity_data.get("life-span")

    return dateutil.parser.isoparse(life_span_dict["begin"]).year if life_span_dict else None


def extract_recording_mbids_and_track_number(
    release_data: MBDataDict,
) -> Iterator[tuple[MBID, str]]:
    """
    Extract recording MBIDs and their corresponding track number from a MusicBrainz release.

    The track number of each recording within release's medium and track is
    formatted as `<medium_position>.<track_position>` with zero-padding to
    allow lexicographical sorting. If the release only contains one medium,
    the medium position is omitted.

    Args:
        release_data (MBDataDict): A release data dictionary.

    Yields:
        MBID: The MusicBrainz ID (MBID) of the recording.
        str: The formatted track number of the recording within the release.
    """
    medium_list = release_data["medium-list"]
    medium_padding = len(str(len(medium_list)))

    for medium in medium_list:
        medium_position = int(medium["position"])

        track_list = medium["track-list"]
        track_padding = len(str(len(track_list)))

        for track in medium["track-list"]:
            track_position = int(track["position"])
            recording_mbid = track["recording"]["id"]

            # Format the track number
            if len(medium_list) == 1:
                track_number = f"{track_position:0{track_padding}}"
            else:
                track_number = (
                    f"{medium_position:0{medium_padding}}.{track_position:0{track_padding}}"
                )

            yield recording_mbid, track_number
