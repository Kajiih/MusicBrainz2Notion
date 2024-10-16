"""
Utils for Notion API.

Most of the enums are AI generated and need to be double checked.
Not all format functions have been tested.
"""

from enum import StrEnum
from typing import Any, Literal

from yarl import URL

from musicbrainz2notion.main import PageId


# === Enums for Notion API ===
class PagePropertyType(StrEnum):
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
    annotations: dict | None = None,
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
    annotations: dict | None = None,
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
    annotations: dict | None = None,
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
) -> dict[Literal[PagePropertyType.RICH_TEXT], list[dict[PropertyField, Any]]]:
    """
    Format a title property for Notion API.

    Args:
        rich_text_list (list[dict[RichTextField, Any]]): A list of rich text
            objects as content of the rich text property.

    Returns:
        dict: A properly formatted dictionary for a title property in Notion API.
    """
    return {PagePropertyType.RICH_TEXT: rich_text_list}


def format_title(
    rich_text_list: list[dict[PropertyField, Any]],
) -> dict[Literal[PagePropertyType.TITLE], list[dict[PropertyField, Any]]]:
    """
    Format a title property for Notion API.

    Args:
        rich_text_list (list[dict[RichTextField, Any]]): A list of rich text
            objects as content of the title.

    Returns:
        dict: A properly formatted dictionary for a title property in Notion API.
    """
    return {
        PagePropertyType.TITLE: rich_text_list,
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
) -> dict[Literal[PagePropertyType.FILES], list[dict[PropertyField, Any]]]:
    """
    Format a files property for Notion API.

    Args:
        file_list (list[dict[PropertyField, Any]]): A list of file objects
            as content of the files property.

    Returns:
        dict: A properly formatted dictionary for a files property in Notion API.
    """
    return {PagePropertyType.FILES: file_list}


# %% === Page property formatting functions === #
def format_select(
    value: str,
) -> dict[Literal[PagePropertyType.SELECT], dict[Literal[PropertyField.NAME], str]]:
    """
    Format a select property for Notion API.

    Args:
        value (str): The name of the option to select.

    Returns:
        dict: A properly formatted dictionary for a select property in
            Notion API.
    """
    return {PagePropertyType.SELECT: {PropertyField.NAME: value}}


def format_multi_select(
    value: list[str],
) -> dict[Literal[PagePropertyType.MULTI_SELECT], list[dict[Literal[PropertyField.NAME], str]]]:
    """
    Format a multi-select property for Notion API.

    Args:
        value (list[str]): List of items for the multi-select property.

    Returns:
        dict: A properly formatted dictionary for a multi-select property in
            Notion API.
    """
    return {PagePropertyType.MULTI_SELECT: [{PropertyField.NAME: item} for item in value]}


def format_checkbox(
    value: bool,
) -> dict[Literal[PagePropertyType.CHECKBOX], bool]:
    """
    Format a checkbox property for Notion API.

    Args:
        value (bool): True if the checkbox is checked, False otherwise.

    Returns:
        dict: A properly formatted dictionary for a checkbox property in
            Notion API.
    """
    return {PagePropertyType.CHECKBOX: value}


def format_created_by(
    user_id: str,
) -> dict[Literal[PagePropertyType.CREATED_BY], dict[Literal[PropertyField.ID], str]]:
    """
    Format a created_by property for Notion API.

    Args:
        user_id (str): The ID of the user who created the page.

    Returns:
        dict: A properly formatted dictionary for a created_by property in
            Notion API.
    """
    return {PagePropertyType.CREATED_BY: {PropertyField.ID: user_id}}


def format_created_time(
    value: str,
) -> dict[Literal[PagePropertyType.CREATED_TIME], str]:
    """
    Format a created_time property for Notion API.

    Args:
        value (str): The date and time the page was created in ISO 8601 format.

    Returns:
        dict: A properly formatted dictionary for a created_time property in
            Notion API.
    """
    return {PagePropertyType.CREATED_TIME: value}


# TODO: Check if it works
def format_date(
    start: str, end: str | None = None
) -> dict[Literal[PagePropertyType.DATE], dict[str, str | None]]:
    """
    Format a date property for Notion API.

    Args:
        start (str): The start date in ISO 8601 format.
        end (str | None): The end date in ISO 8601 format, or None if not a
            range.

    Returns:
        dict: A properly formatted dictionary for a date property in Notion API.
    """
    return {PagePropertyType.DATE: {PropertyField.START: start, PropertyField.END: end}}


def format_email(
    email: str,
) -> dict[Literal[PagePropertyType.EMAIL], str]:
    """
    Format an email property for Notion API.

    Args:
        email (str): A string describing an email address.

    Returns:
        dict: A properly formatted dictionary for an email property in
            Notion API.
    """
    return {PagePropertyType.EMAIL: email}


def format_number(
    value: int | float,
) -> dict[Literal[PagePropertyType.NUMBER], int | float]:
    """
    Format a number property for Notion API.

    Args:
        value (int | float): A number representing some value.

    Returns:
        dict: A properly formatted dictionary for a number property in
            Notion API.
    """
    return {PagePropertyType.NUMBER: value}


def format_url(url: str) -> dict[Literal[PagePropertyType.URL], str]:
    """
    Format an email property for Notion API.

    Args:
        url (str): A string describing the url.

    Returns:
        dict: A properly formatted dictionary for aa url property in Notion API.
    """
    return {PagePropertyType.URL: url}


def format_relation(
    page_ids: list[str],
) -> dict[Literal[PagePropertyType.RELATION], list[dict[Literal[PropertyField.ID], PageId]]]:
    """
    Format a relation property for Notion API.

    Args:
        page_ids (list[str]): List of page IDs to create a relation property.

    Returns:
        dict: A properly formatted relation property for Notion API.
    """
    return {PagePropertyType.RELATION: [{PropertyField.ID: page_id} for page_id in page_ids]}


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
