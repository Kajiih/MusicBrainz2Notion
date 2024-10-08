"""Utils for Notion API."""

from enum import StrEnum

# === Enums for Notion API ===


class NotionPropertyType(StrEnum):
    """Represents the types of properties in a Notion database."""

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


class NotionObjectType(StrEnum):
    """Represents the types of objects available in Notion."""

    PAGE = "page"
    DATABASE = "database"
    BLOCK = "block"
    USER = "user"
    COMMENT = "comment"
    LIST = "list"


class NotionFilterCondition(StrEnum):
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


class NotionSortDirection(StrEnum):
    """Sort directions for sorting database queries."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class NotionColor(StrEnum):
    """Colors available in Notion for text and backgrounds."""

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


class NotionDatabaseType(StrEnum):
    """Represents the type of a Notion database."""

    DATABASE = "database_id"
    PARENT = "parent"
