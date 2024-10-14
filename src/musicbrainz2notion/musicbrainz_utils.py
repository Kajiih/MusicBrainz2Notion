"""Utils for Musicbrainz API."""

from enum import StrEnum


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
    # Non core resources
    RATING = "rating"
    TAG = "tag"
    COLLECTION = "collection"


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