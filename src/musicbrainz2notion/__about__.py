"""About MusicBrainz2Notion."""

import tomllib
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
print(f"{_PROJECT_ROOT = }")

# Construct the path to pyproject.toml relative to the project root
_PYPROJECT_PATH = _PROJECT_ROOT / "pyproject.toml"

with _PYPROJECT_PATH.open("rb") as fp:
    _PYPROJECT_DATA = tomllib.load(fp)

__version__ = "0.1.0"
__app_name__ = _PYPROJECT_DATA["project"]["name"]
__author__ = _PYPROJECT_DATA["project"]["authors"][0]["name"]
__email__ = _PYPROJECT_DATA["project"]["authors"][0]["email"]
__repo_url__ = _PYPROJECT_DATA["project"]["urls"]["Repository"]
