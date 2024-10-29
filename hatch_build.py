"""Hatch build hook."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from src.musicbrainz2notion.__about__ import (
    __author__,
    __author_email__,
    __issues_url__,
    __repo_url__,
)


class AboutMetadataHook(MetadataHookInterface):
    """Hatchling metadata hook that loads dynamic metadata for authors, and URLs from the `__about__.py` file within the project."""

    def update(self, metadata: dict[str, Any]) -> None:  # noqa: PLR6301
        """Update the metadata dictionary with values from the `__about__.py` file."""
        metadata["authors"] = [{"name": __author__, "email": __author_email__}]
        metadata["urls"] = {
            "Repository": __repo_url__,
            "Issues": __issues_url__,
        }


# class AboutMetadataHookOld(MetadataHookInterface):
#     """Hatchling metadata hook that loads dynamic metadata for authors, and URLs from the `__about__.py` file within the project."""

#     def update(self, metadata: dict[str, Any]) -> None:
#         """
#         Update the metadata dictionary with values from the `__about__.py` file.

#         Args:
#             metadata: The dictionary containing the project metadata.
#         """
#         # Dynamically load __about__.py
#         about_path = Path(self.root) / "src/musicbrainz2notion/__about__.py"
#         spec = importlib.util.spec_from_file_location("__about__", about_path)
#         if spec is None or spec.loader is None:
#             raise ImportError(f"Could not load metadata from {about_path}")

#         about = importlib.util.module_from_spec(spec)
#         sys.modules["__about__"] = about
#         spec.loader.exec_module(about)

#         # Map __about__ attributes to metadata fields
#         metadata["authors"] = [{"name": about.__author__, "email": about.__author_email__}]
#         metadata["urls"] = {"Repository": about.__repo_url__, "Issues": about.__issues_url__}