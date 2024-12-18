"""
Utils for Notion API.

Most of the enums are AI generated and need to be double checked.
Not all format functions have been tested.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import notion_client
from loguru import logger
from notion_client import Client

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

# === Types === #
type PageId = str
type DatabaseId = PageId
type BlockId = PageId
type NotionResponse = dict[str, Any]


class BlockDict(TypedDict):
    """The dictionary of a json response containing the content of a block."""

    has_children: bool
    type: BlockType
    id: BlockId


class DatabaseDict(TypedDict):
    """The dictionary of a json response containing the content of a database."""

    id: DatabaseId
    title: list[dict[str, Any]]  # Rich Text
    properties: dict[PropertyType, dict[PropertyField, Any]]


# === Enums for Notion API ===
class BlockType(StrEnum):
    """Types of block in a Notion API response."""

    CHILD_DATABASE = "child_database"


class PropertyType(StrEnum):
    """Types of properties in a Notion page."""

    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    CREATED_TIME = "created_time"
    LAST_EDITED_TIME = "last_edited_time"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_BY = "created_by"
    LAST_EDITED_BY = "last_edited_by"
    STATUS = "status"


class PropertyField(StrEnum):
    """Fields of properties in a Notion page."""

    NAME = "name"
    ID = "id"
    START = "start"
    END = "end"
    TYPE = "type"
    URL = "url"
    EMOJI = "emoji"
    # == Rich text == #
    TEXT = "text"
    CONTENT = "content"
    LINK = "link"
    ANNOTATIONS = "annotations"
    PLAIN_TEXT = "plain_text"
    HREF = "href"
    MENTION = "mention"
    EQUATION = "equation"
    EXPRESSION = "expression"
    USER = "user"
    DATE = "date"
    PAGE = "page"
    DATABASE = "database"
    TEMPLATE_MENTION = "template_mention"
    CHECKBOX = "checkbox"
    # == File == #
    EXTERNAL = "external"
    FILE = "file"
    EXPIRY_TIME = "expiry_time"


class NotionObjectType(StrEnum):
    """Types of objects available in Notion."""

    PAGE = "page"
    DATABASE = "database"
    BLOCK = "block"
    USER = "user"
    COMMENT = "comment"
    LIST = "list"


class FilterCondition(StrEnum):
    """Common conditions for filtering database queries."""

    EQUALS = "equals"
    DOES_NOT_EQUAL = "does_not_equal"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal_to"
    LESS_THAN_OR_EQUAL = "less_than_or_equal_to"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SortDirection(StrEnum):
    """Sort directions for sorting database queries."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class NotionDatabaseType(StrEnum):
    """Type of database in Notion."""

    DATABASE = "database_id"
    PARENT = "parent"


# %% === Rich text === #
class RichTextType(StrEnum):
    """Type of rich text in Notion API."""

    TEXT = "text"
    MENTION = "mention"
    EQUATION = "equation"


class AnnotationType(StrEnum):
    """Types of rich text annotations."""

    BOLD = "bold"
    ITALIC = "italic"
    STRIKETHROUGH = "strikethrough"
    UNDERLINE = "underline"
    CODE = "code"
    COLOR = "color"


class RichTextColor(StrEnum):
    """Colors of rich text in a rich text annotation."""

    DEFAULT = "default"
    GRAY = "gray"
    BROWN = "brown"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    RED = "red"
    GRAY_BACKGROUND = "gray_background"
    BROWN_BACKGROUND = "brown_background"
    ORANGE_BACKGROUND = "orange_background"
    YELLOW_BACKGROUND = "yellow_background"
    GREEN_BACKGROUND = "green_background"
    BLUE_BACKGROUND = "blue_background"
    PURPLE_BACKGROUND = "purple_background"
    PINK_BACKGROUND = "pink_background"
    RED_BACKGROUND = "red_background"


class MentionType(StrEnum):
    """Mention types in a mention rich text."""

    USER = "user"
    DATE = "date"
    PAGE = "page"
    DATABASE = "database"
    TEMPLATE_MENTION = "template_mention"


def format_annotations(
    bold: bool = False,
    italic: bool = False,
    strikethrough: bool = False,
    underline: bool = False,
    code: bool = False,
    color: RichTextColor = RichTextColor.DEFAULT,
) -> dict[AnnotationType, Any]:
    """
    Format the annotation object for a rich text entry.

    Args:
        bold (bool): Whether the text is bold.
        italic (bool): Whether the text is italicized.
        strikethrough (bool): Whether the text has strikethrough.
        underline (bool): Whether the text is underlined.
        code (bool): Whether the text is in code format.
        color (RichTextColor): The color of the text.

    Returns:
        dict: A properly formatted annotations dictionary for rich text in
            Notion API.
    """
    return {
        AnnotationType.BOLD: bold,
        AnnotationType.ITALIC: italic,
        AnnotationType.STRIKETHROUGH: strikethrough,
        AnnotationType.UNDERLINE: underline,
        AnnotationType.CODE: code,
        AnnotationType.COLOR: color,
    }


def format_text(
    content: str,
    annotations: dict[str, Any] | None = None,
    link: str | None = None,
) -> dict[PropertyField, Any]:
    """
    Format a text-type rich text object for Notion API.

    Args:
        content (str): The text content.
        annotations (dict | None): Annotations for styling the text (bold,
            italic, etc.).
        link (str | None): The URL for a hyperlink (if any).

    Returns:
        dict: A properly formatted rich text object for text type in Notion API.
    """
    return {
        PropertyField.TYPE: RichTextType.TEXT,
        PropertyField.TEXT: {
            PropertyField.CONTENT: content,
            PropertyField.LINK: {PropertyField.URL: link} if link else None,
        },
        PropertyField.ANNOTATIONS: annotations or format_annotations(),
        PropertyField.PLAIN_TEXT: content,
        PropertyField.HREF: link,
    }


def format_mention(
    mention_type: MentionType,
    mention_value: dict[str, str],
    annotations: dict[str, Any] | None = None,
    plain_text: str | None = None,
    link: str | None = None,
) -> dict[PropertyField, Any]:
    """
    Format a mention-type rich text object for Notion API.

    Args:
        mention_type (MentionType): The type of mention (user, date, page, etc.).
        mention_value (dict[str, str]): The value related to the mention (user ID,
            date, page ID, etc.).
        annotations (dict | None): Annotations for styling the text (bold,
            italic, etc.).
        plain_text (str | None): The plain text representation of the mention (if
            any).
        link (str | None): The URL for a hyperlink (if any).

    Returns:
        dict: A properly formatted rich text object for mentions in Notion API.
    """
    return {
        PropertyField.TYPE: RichTextType.MENTION,
        PropertyField.MENTION: {
            PropertyField.TYPE: mention_type.value,
            mention_type.value: mention_value,
        },
        PropertyField.ANNOTATIONS: annotations or format_annotations(),
        PropertyField.PLAIN_TEXT: plain_text or "",
        PropertyField.HREF: link,
    }


def format_equation(
    expression: str,
    annotations: dict[str, Any] | None = None,
    plain_text: str | None = None,
    link: str | None = None,
) -> dict[PropertyField, Any]:
    """
    Format an equation-type rich text object for Notion API.

    Args:
        expression (str): The LaTeX string representing the inline equation.
        annotations (dict | None): Annotations for styling the text (bold,
            italic, etc.).
        plain_text (str | None): The plain text representation of the equation
            (if any).
        link (str | None): The URL for a hyperlink (if any).

    Returns:
        dict: A properly formatted rich text object for equations in Notion API.
    """
    return {
        PropertyField.TYPE: RichTextType.EQUATION,
        PropertyField.EQUATION: {PropertyField.EXPRESSION: expression},
        PropertyField.ANNOTATIONS: annotations or format_annotations(),
        PropertyField.PLAIN_TEXT: plain_text or expression,
        PropertyField.HREF: link,
    }


def format_rich_text(
    rich_text_list: list[dict[PropertyField, Any]],
) -> dict[Literal[PropertyType.RICH_TEXT], list[dict[PropertyField, Any]]]:
    """
    Format a title property for Notion API.

    Args:
        rich_text_list (list[dict[RichTextField, Any]]): A list of rich text
            objects as content of the rich text property.

    Returns:
        dict: A properly formatted dictionary for a title property in Notion API.
    """
    return {PropertyType.RICH_TEXT: rich_text_list}


def format_title(
    rich_text_list: list[dict[PropertyField, Any]],
) -> dict[Literal[PropertyType.TITLE], list[dict[PropertyField, Any]]]:
    """
    Format a title property for Notion API.

    Args:
        rich_text_list (list[dict[RichTextField, Any]]): A list of rich text
            objects as content of the title.

    Returns:
        dict: A properly formatted dictionary for a title property in Notion API.
    """
    return {
        PropertyType.TITLE: rich_text_list,
        # TODO: Check if we need to add "id" and "type" to the title property
        # PropertyField.ID: PagePropertyType.TITLE,
        # PropertyField.TYPE: PagePropertyType.TITLE,
    }


# %% === Files === #
def format_external_file(
    name: str,
    url: str,
) -> dict[PropertyField, Any]:
    """
    Format an external file property for Notion API.

    Args:
        name (str): The name of the external file.
        url (str): The URL of the external file.

    Returns:
        dict: A properly formatted external file object for Notion API.
    """
    return {
        PropertyField.NAME: name,
        PropertyField.TYPE: PropertyField.EXTERNAL,
        PropertyField.EXTERNAL: {PropertyField.URL: url},
    }


def format_notion_file(
    name: str,
    url: str,
    expiry_time: str,
) -> dict[PropertyField, Any]:
    """
    Format a Notion-hosted file property for Notion API.

    Args:
        name (str): The name of the file.
        url (str): The authenticated S3 URL of the file.
        expiry_time (str): The expiration time of the file link (ISO 8601 format).

    Returns:
        dict: A properly formatted Notion-hosted file object for Notion API.
    """
    return {
        PropertyField.NAME: name,
        PropertyField.TYPE: PropertyField.FILE,
        PropertyField.FILE: {PropertyField.URL: url, PropertyField.EXPIRY_TIME: expiry_time},
    }


def format_file(
    file_list: list[dict[PropertyField, Any]],
) -> dict[Literal[PropertyType.FILES], list[dict[PropertyField, Any]]]:
    """
    Format a files property for Notion API.

    Args:
        file_list (list[dict[PropertyField, Any]]): A list of file objects
            as content of the files property.

    Returns:
        dict: A properly formatted dictionary for a files property in Notion API.
    """
    return {PropertyType.FILES: file_list}


# %% === Page property formatting === #
class SelectDict(TypedDict):
    """Structure of the content of a select property in Notion."""

    name: str


class SelectProperty(TypedDict):
    """Structure of a select property in Notion."""

    select: SelectDict


def format_select(
    value: str,
) -> SelectProperty:
    """
    Format a select property for Notion API.

    Args:
        value (str): The name of the option to select.

    Returns:
        SelectProperty: A properly formatted dictionary for a select property in
            Notion API.
    """
    return {"select": {"name": value}}


class MultiSelectProperty(TypedDict):
    """Structure of a multi-select property in Notion."""

    multi_select: list[SelectDict]


def format_multi_select(
    values: Sequence[str],
) -> MultiSelectProperty:
    """
    Format a multi-select property for Notion API.

    Args:
        values (Sequence[str]): List of items for the multi-select property.

    Returns:
        MultiSelectDict: A properly formatted dictionary for a multi-select
            property in Notion API.
    """
    multi_select_list: list[SelectDict] = [{"name": item} for item in values]

    return {"multi_select": multi_select_list}


def format_checkbox(
    value: bool,
) -> dict[Literal[PropertyField.CHECKBOX], bool]:
    """
    Format a checkbox property for Notion API.

    Args:
        value (bool): True if the checkbox is checked, False otherwise.

    Returns:
        dict: A properly formatted dictionary for a checkbox property in
            Notion API.
    """
    return {PropertyField.CHECKBOX: value}


def format_created_by(
    user_id: str,
) -> dict[Literal[PropertyType.CREATED_BY], dict[Literal[PropertyField.ID], str]]:
    """
    Format a created_by property for Notion API.

    Args:
        user_id (str): The ID of the user who created the page.

    Returns:
        dict: A properly formatted dictionary for a created_by property in
            Notion API.
    """
    return {PropertyType.CREATED_BY: {PropertyField.ID: user_id}}


def format_created_time(
    value: str,
) -> dict[Literal[PropertyType.CREATED_TIME], str]:
    """
    Format a created_time property for Notion API.

    Args:
        value (str): The date and time the page was created in ISO 8601 format.

    Returns:
        dict: A properly formatted dictionary for a created_time property in
            Notion API.
    """
    return {PropertyType.CREATED_TIME: value}


# TODO: Check if it works
def format_date(
    start: str, end: str | None = None
) -> dict[Literal[PropertyType.DATE], dict[str, str | None]]:
    """
    Format a date property for Notion API.

    Args:
        start (str): The start date in ISO 8601 format.
        end (str | None): The end date in ISO 8601 format, or None if not a
            range.

    Returns:
        dict: A properly formatted dictionary for a date property in Notion API.
    """
    return {PropertyType.DATE: {PropertyField.START: start, PropertyField.END: end}}


def format_email(
    email: str,
) -> dict[Literal[PropertyType.EMAIL], str]:
    """
    Format an email property for Notion API.

    Args:
        email (str): A string describing an email address.

    Returns:
        dict: A properly formatted dictionary for an email property in
            Notion API.
    """
    return {PropertyType.EMAIL: email}


def format_number[T: int | float | None](
    value: T,
) -> dict[Literal[PropertyType.NUMBER], T]:
    """
    Format a number property for Notion API.

    Args:
        value (int | float | None): A number representing some value.

    Returns:
        dict: A properly formatted dictionary for a number property in
            Notion API.
    """
    return {PropertyType.NUMBER: value}


def format_url(url: str) -> dict[Literal[PropertyType.URL], str]:
    """
    Format an email property for Notion API.

    Args:
        url (str): A string describing the url.

    Returns:
        dict: A properly formatted dictionary for aa url property in Notion API.
    """
    return {PropertyType.URL: url}


def format_relation(
    page_ids: list[str],
) -> dict[Literal[PropertyType.RELATION], list[dict[Literal[PropertyField.ID], PageId]]]:
    """
    Format a relation property for Notion API.

    Args:
        page_ids (list[str]): List of page IDs to create a relation property.

    Returns:
        dict: A properly formatted relation property for Notion API.
    """
    return {PropertyType.RELATION: [{PropertyField.ID: page_id} for page_id in page_ids]}


def format_emoji(
    emoji: str,
) -> dict[Literal[PropertyField.TYPE, PropertyField.EMOJI], str]:
    """
    Format a page emoji for Notion API.

    Args:
        emoji (str): The emoji to be used as the page's icon.

    Returns:
        dict: A properly formatted dictionary for a page emoji in Notion API.
    """
    return {
        PropertyField.TYPE: PropertyField.EMOJI,
        PropertyField.EMOJI: emoji,
    }


# %% === Page property extraction === #
# TODO: Check if we pass the whole dictionary instead of just the list
def extract_plain_text(rich_text_property: list[dict[str, Any]]) -> str:
    """
    Extract the plain text from a rich text property.

    Args:
        rich_text_property (list[dict[str, Any]]): A list of rich text objects
            from a Notion property.

    Returns:
        str: The concatenated plain text from the rich text property.
    """
    full_text = "".join([
        text_object[PropertyField.PLAIN_TEXT] for text_object in rich_text_property
    ])
    return full_text


def get_checkbox_value(checkbox_property: dict[str, Any]) -> bool:
    """
    Extract the boolean value from a checkbox property.

    Args:
        checkbox_property (dict[str, Any]): A dictionary representing the
            checkbox property from a Notion page.

    Returns:
        bool: The boolean value of the checkbox (True if checked, False otherwise).
    """
    return checkbox_property[PropertyField.CHECKBOX]


# === Block reading utils ===
def extract_id_from_url(url: str, link_1_or_2: Literal[1, 2] = 1) -> str:
    """Extract the object id from the url to the object."""
    # Find all 32-character hex sequences, ignoring case
    ids = re.findall(r"[0-9a-f]{32}", url, flags=re.IGNORECASE)
    return ids[link_1_or_2 - 1]


def find_databases_with_properties(
    client: Client, prop_names: Sequence[Iterable[str]], block_id: BlockId
) -> list[list[DatabaseId]]:
    """
    Recursively search all databases with the given properties in the block and its children.

    Args:
        client: Notion client with access to the block.
        prop_names: List of tuple of property names that the databases should
            have.
        block_id: ID of the block to start the search in.

    Returns:
        The list of list of database IDs of the database found for each tuple of
            properties.
    """
    database_ids: list[list[DatabaseId]] = [[] for _ in range(len(prop_names))]

    def find_databases_with_properties_acc(
        block_id: BlockId, database_ids_accumulator: list[list[DatabaseId]]
    ) -> None:
        children: list[BlockDict] = client.blocks.children.list(block_id=block_id)["results"]  # pyright: ignore[reportIndexIssue]
        for child in children:
            if child["type"] == BlockType.CHILD_DATABASE:
                for props, database_list in zip(prop_names, database_ids_accumulator, strict=True):
                    database_id = child["id"]
                    database: DatabaseDict = client.databases.retrieve(database_id)  # pyright: ignore[reportAssignmentType]
                    if has_properties_database(props=props, database=database):
                        database_list.append(database_id)
            elif child["has_children"]:
                find_databases_with_properties_acc(
                    block_id=child["id"], database_ids_accumulator=database_ids_accumulator
                )

    find_databases_with_properties_acc(block_id=block_id, database_ids_accumulator=database_ids)

    return database_ids


def has_properties_database(props: Iterable[str], database: DatabaseDict) -> bool:
    """Return if the database has all properties."""
    return all(prop in database["properties"] for prop in props)


# === Validators ===
class InvalidNotionAPIKeyError(ValueError):
    """The Notion API key is invalid."""

    def __init__(self, key: str) -> None:
        super().__init__(f"{key} is not a valid Notion API key.")


NOTION_API_KEY_REGEX = r"^(secret_|ntn_)[A-Za-z0-9]{43}$"

NOTION_API_KEY_PATTERN = re.compile(NOTION_API_KEY_REGEX)


def is_valid_notion_key(key: str) -> bool:
    """
    Check if the given key is a valid Notion API key.

    Args:
        key: The key to validate.

    Returns:
        True if the key is a valid Notion API key, else False.
    """
    if NOTION_API_KEY_PATTERN.fullmatch(key) is None:
        logger.warning(f"{key} does not match valid format `{NOTION_API_KEY_REGEX}`")
        return False

    client = Client(auth=key)
    try:
        client.users.me()
    except notion_client.errors.APIResponseError:
        logger.warning(f"Test request failed.")
        return False

    return True


class InvalidNotionDatabaseIdError(ValueError):
    """The Notion database ID is invalid."""

    def __init__(self, db_id: str) -> None:
        super().__init__(f"{db_id} is not a valide Notion database ID.")


DATABASE_ID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{32}$"
)


def is_valid_database_id(client: Client, db_id: str) -> bool:
    """
    Check if the given key is a valid database ID.

    Args:
        client: Notion client with access to the database.
        db_id: The ID to validate.

    Returns:
        True if the ID is a valid Notion database ID, else False.
    """
    try:
        client.databases.retrieve(db_id)
    except notion_client.errors.APIResponseError:
        logger.warning("Test request failed.")
        return False

    return True


class InvalidNotionPageIdError(ValueError):
    """The Notion page ID is invalid."""

    def __init__(self, page_id: str) -> None:
        super().__init__(f"{page_id} is not a valide Notion Page ID.")


def is_valid_page_id(client: Client, page_id: str) -> bool:
    """
    Check if the given key is a valid page ID.

    Args:
        client: Notion client with access to the page.
        page_id: The ID to validate.

    Returns:
        True if the ID is a valid Notion page ID, else False.
    """
    try:
        client.pages.retrieve(page_id)
    except notion_client.errors.APIResponseError:
        logger.warning("Test request failed.")
        return False

    return True
