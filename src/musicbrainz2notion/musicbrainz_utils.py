"""Utils for Musicbrainz API."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, NotRequired, TypedDict

# %% === Types === #
type MBID = str


class AreaDict(TypedDict):
    """Structure of an area dictionary in MusicBrainz data."""

    name: str


class LifeSpanDict(TypedDict):
    """Structure of a life span dictionary in MusicBrainz data."""

    begin: str


class TrackDict(TypedDict):
    """Structure of a track dictionary in MusicBrainz data."""

    id: MBID
    position: str
    number: str
    length: str
    recording: RecordingDict
    track_or_recording_length: str


"""Structure of a medium dictionary in MusicBrainz data."""
MediumDict = TypedDict(
    "MediumDict",
    {
        "position": str,
        "format": str,
        "track-list": list[TrackDict],
    },
)


class TagDict(TypedDict):
    """Structure of a tag dictionary in MusicBrainz data."""

    count: str
    name: str


class AliasDict(TypedDict):
    """Structure of an alias dictionary in MusicBrainz data."""

    alias: str


class LanguageDict(TypedDict):
    """Structure of a language dictionary in MusicBrainz data."""

    language: str


"""Structure of a rating dictionary in MusicBrainz data."""
RatingDict = TypedDict(
    "RatingDict",
    {
        "vote-count": str,
        "rating": str,
    },
)

# TODO: Separate Artist data dict, release data dict, etc
"""Structure of MusicBrainz data."""
MBDataDict = TypedDict(
    "MBDataDict",
    {
        "id": str,
        "name": str,
        "type": str,
        "area": NotRequired[AreaDict],
        "life-span": NotRequired[LifeSpanDict],
        "rating": NotRequired[RatingDict],
        "text-representation": NotRequired[LanguageDict],
        "tag-list": NotRequired[list[TagDict]],
        "alias-list": NotRequired[list[AliasDict]],
        # Release group/release
        "title": str,
        "medium-list": list[MediumDict],
        "artist-credit": list[dict[str, Any] | str],
        "first-release-date": NotRequired[str],
        # Recording
        "length": NotRequired[str],
        "release-list": NotRequired[list[dict[str, Any]]],
    },
)

"""Structure of a recording dictionary in MusicBrainz data."""
RecordingDict = TypedDict(
    "RecordingDict",
    {
        "id": MBID,
        "title": str,
        "length": str,
        "tag-list": NotRequired[list[TagDict]],
    },
)


# === Enums === #
class EntityType(StrEnum):
    """
    Entity types available in the MusicBrainz API.

    This enum is not used with musicbrainzngs.
    """

    # Core resources
    ARTIST = "artist"
    RELEASE = "release"
    RECORDING = "recording"
    RELEASE_GROUP = "release-group"
    LABEL = "label"
    WORK = "work"
    AREA = "area"
    PLACE = "place"
    INSTRUMENT = "instrument"
    EVENT = "event"
    URL = "url"
    GENRE = "genre"
    SERIES = "series"


class IncludeOption(StrEnum):
    """
    Options for including additional information in MusicBrainz API responses.

    These options are used with various API calls to retrieve more detailed or
    related data about the main entity being queried. Note that this list may be
    incomplete and can be expanded based on the API's capabilities.
    """

    ALIASES = "aliases"
    ANNOTATION = "annotation"
    TAGS = "tags"
    USER_TAGS = "user-tags"
    RATINGS = "ratings"
    USER_RATINGS = "user-ratings"
    GENRES = "genres"
    USER_GENRES = "user-genres"
    RELS = "rels"
    RECORDINGS = "recordings"
    RELEASES = "releases"
    RELEASE_GROUPS = "release-groups"
    LABELS = "labels"
    WORKS = "works"
    ARTIST_CREDITS = "artist-credits"
    AREA_RELS = "area-rels"
    ARTIST_RELS = "artist-rels"
    LABEL_RELS = "label-rels"
    RECORDING_RELS = "recording-rels"
    RELEASE_RELS = "release-rels"
    RELEASE_GROUP_RELS = "release-group-rels"
    WORK_RELS = "work-rels"
    SERIES_RELS = "series-rels"
    URL_RELS = "url-rels"
    INSTRUMENT_RELS = "instrument-rels"
    PLACE_RELS = "place-rels"
    EVENT_RELS = "event-rels"


class MBDataField(StrEnum):
    """Keys of the dictionaries returned by the MusicBrainz API."""

    RATING = "rating"
    TAG = "tag"
    COLLECTION = "collection"
    NAME = "name"
    TITLE = "title"
    ARTIST = "artist"
    ARTIST_CREDIT = "artist-credit"
    MBID = "id"
    TYPE = "type"
    FIRST_RELEASE_DATE = "first-release-date"
    AREA = "area"
    LIFE_SPAN = "life-span"
    BEGIN = "begin"
    TAG_LIST = "tag-list"
    ALIAS_LIST = "alias-list"
    ALIAS = "alias"
    COUNT = "count"
    TEXT_REPRESENTATION = "text-representation"
    LANGUAGE = "language"
    SECONDARY_TYPES = "secondary-type-list"


class CanonicalDataHeader(StrEnum):
    """Headers of the MusicBrainz canonical dumps."""

    RELEASE_GROUP_MBID = "release_group_mbid"
    CANONICAL_RELEASE_MBID = "canonical_release_mbid"
    CANONICAL_RECORDING_MBID = "canonical_recording_mbid"


class ArtistType(StrEnum):
    """Artist types in MusicBrainz database."""

    PERSON = "Person"
    GROUP = "Group"
    ORCHESTRA = "Orchestra"
    CHOIR = "Choir"
    CHARACTER = "Character"
    OTHER = "Other"


class ReleaseType(StrEnum):
    """
    Release types in MusicBrainz database.

    This enum helps filter release entities in the API by their type (e.g.,
    albums, singles, live performances).
    """

    ALBUM = "album"
    SINGLE = "single"
    EP = "ep"
    BROADCAST = "broadcast"
    COMPILATION = "compilation"
    LIVE = "live"
    OTHER = "other"
    SOUNDTRACK = "soundtrack"
    SPOKENWORD = "spokenword"
    INTERVIEW = "interview"
    AUDIOBOOK = "audiobook"
    REMIX = "remix"
    DJ_MIX = "dj-mix"
    MIXTAPE_STREET = "mixtape/street"
    NAT = "nat"


class ReleaseStatus(StrEnum):
    """
    Release status in MusicBrainz database.

    This enum is used to filter and categorize releases based on their
    publication status.
    """

    OFFICIAL = "official"
    PROMOTION = "promotion"
    BOOTLEG = "bootleg"
    PSEUDO_RELEASE = "pseudo-release"
