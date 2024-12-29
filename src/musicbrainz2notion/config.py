"""
Temporary config module for MusicBrainz2notion.

# TODO: Improve config handling
"""

from __future__ import annotations

import attrs
import typed_settings as ts
from notion_client import Client
from typed_settings.types import SecretStr

from musicbrainz2notion.__about__ import PROJECT_ROOT, __app_name__
from musicbrainz2notion.musicbrainz_utils import CoverSize, ReleaseType
from musicbrainz2notion.notion_utils import (
    DATABASE_ID_REGEX,
    NOTION_API_KEY_REGEX,
    InvalidNotionAPIKeyError,
    InvalidNotionDatabaseIdError,
    is_valid_database_id,
    is_valid_notion_key,
)

CONFIG_PATH = "!" / PROJECT_ROOT / "settings.toml"  # "!" Makes the path mandatory in typed_settings
GLOBAL_CONFIG_SECTION = f"{__app_name__}-global"

FANART_KEY_REGEX = DATABASE_ID_REGEX


def _notion_api_key_validator(inst: Settings, attribute: attrs.Attribute[str], value: str) -> None:
    del inst, attribute
    if not is_valid_notion_key(value):
        raise InvalidNotionAPIKeyError(key=value)


def _database_id_validator(inst: Settings, attribute: attrs.Attribute[str], value: str) -> None:
    del attribute
    client = Client(auth=inst.notion_api_key)
    if not is_valid_database_id(client=client, db_id=value):
        raise InvalidNotionDatabaseIdError(db_id=value)


# TODO: Test validators
# TODO? Add converter?
# We can't use validator yet since empty config would make it crash
@attrs.define(
    kw_only=True,
    frozen=True,
    cache_hash=True,
)
class Settings:
    """
    Settings for MusicBrainz2notion.

    Attributes:
        artists_to_update: List of artist MBIDs to update, in addition to those
            marked "To update" in Notion.
        notion_api_key: Notion API key.
        fanart_api_key: Fanart.tv API key.
        artist_db_id: Artist database ID.
        release_db_id: Release database ID.
        track_db_id: Track database ID.
        release_type_filter: List of release types to include in Notion. If
            empty, all types are included.
        release_secondary_type_exclude: List of release secondary types to
            exclude from Notion.
        min_nb_tags: Minimum number of tags to try to add to an entity, starting
            from the most voted ones. . If several tags have the same vote
            counts, they will all be added, maybe resulting in more than
            `min_nb_tags` tags.
        cover_size: Size of MusicBrainz release covers.
        add_track_thumbnail: Whether to add a thumbnail to tracks.
        force_update_artist_cover: Whether to force the update the MusicBrainz
            canonical data, effectively downloading the data again.
    """

    artists_to_update: tuple[str, ...] = ()

    # === API keys === #
    notion_api_key: SecretStr = attrs.field(
        default=SecretStr(""),
        # validator=[attrs.validators.matches_re(NOTION_KEY_REGEX), _notion_api_key_validator],
    )  # pyright: ignore[reportAssignmentType]
    fanart_api_key: SecretStr | None = attrs.field(
        default=None,
        # validator=attrs.validators.optional(attrs.validators.matches_re(FANART_KEY_REGEX)),
    )  # pyright: ignore[reportAssignmentType]

    # === Database IDs === #
    # TODO? Replace by sentinel ?
    artist_db_id: str = attrs.field(
        default="",
        # validator=[attrs.validators.matches_re(DATABASE_ID_REGEX), _database_id_validator],
    )
    release_db_id: str = attrs.field(
        default="",
        # validator=[attrs.validators.matches_re(DATABASE_ID_REGEX), _database_id_validator],
    )
    track_db_id: str = attrs.field(
        default="",
        # validator=[attrs.validators.matches_re(DATABASE_ID_REGEX), _database_id_validator],
    )

    # === Database IDs === #
    release_type_filter: tuple[ReleaseType, ...] = (ReleaseType.ALBUM, ReleaseType.EP)
    release_secondary_type_exclude: tuple[ReleaseType, ...] = (
        ReleaseType.COMPILATION,
        ReleaseType.LIVE,
    )

    # === Others === #
    min_nb_tags: int = 3
    cover_size: CoverSize = 500
    add_track_thumbnail: bool = True
    force_update_canonical_data: bool = False


@attrs.define(
    kw_only=True,
    frozen=True,
    cache_hash=True,
)
class GlobalSettings:
    """
    Global settings for MusicBrainz2notion.

    Global settings are initialized once when loading the module and used
    globally in the module.

    Attributes:
        ARTIST_ICON: Icon to use for artist pages.
        RELEASE_ICON: Icon to use for release pages.
        TRACK_ICON: Icon to use for track pages.
        EMPTY_TYPE_PLACEHOLDER: Placeholder to use when no type is found for a
            artist or release. Use " " for an un-assignable value in Notion.
        EMPTY_AREA_PLACEHOLDER: Placeholder to use when no area is found for an
            artist. Use " " for an un-assignable value in Notion.
        EMPTY_LANGUAGE_PLACEHOLDER: Placeholder to use when no language is
            found for a release. Use " " for an un-assignable value in Notion.
        REQUEST_TIMEOUT: Timeout for http requests.
    """

    # === Icon emojis === #
    ARTIST_ICON: str = "🧑‍🎤"
    RELEASE_ICON: str = "💽"
    TRACK_ICON: str = "🎼"

    # === Select Placeholders === #
    EMPTY_TYPE_PLACEHOLDER: str = "Unknown"
    EMPTY_AREA_PLACEHOLDER: str = "Unknown"
    EMPTY_LANGUAGE_PLACEHOLDER: str = "Unknown"

    # === Other === #
    REQUEST_TIMEOUT: int = 10


global_settings = ts.load(
    GlobalSettings,
    appname=__app_name__,
    config_files=[CONFIG_PATH],
    config_file_section=GLOBAL_CONFIG_SECTION,
    env_prefix=None,
)
