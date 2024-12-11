"""
Build the executable using PyInstaller.

Among others, create the app depending on the OS and zip the distribution.
"""

from __future__ import annotations

import os
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Annotated, Literal

import PyInstaller.__main__
from cyclopts import App, Parameter
from kajihs_utils.loguru import setup_logging
from loguru import logger

from musicbrainz2notion.__about__ import PROJECT_ROOT  # noqa: PLC2701

# Define variables for distribution paths and application name
SPEC_PATH = Path("dev/bundling")
DIST_PATH = Path("dist/pyinstaller")
APP_NAME = "musicbrainz2notion"
DEST_DIR = DIST_PATH / APP_NAME
# SCRIPT_PATH = Path(__file__).resolve().parent
MEDIA_PATH = PROJECT_ROOT / "media"
ICON_PATH = MEDIA_PATH / "musicbrainz_black_and_white.png"

OTHER_COPIED_DATA = [
    "README.md",
    "README.fr.md",
    "LICENSE",
    "settings.toml",
]

setup_logging(file_name="build")


def build_executable(build_mode: Literal["onedir", "onefile"], windowed: bool) -> None:
    """Build the executable using PyInstaller based on the specified build mode and windowed option."""
    # Determine build mode and set options
    if build_mode == "onedir":
        build_mode_option = "--onedir"
        dist_option = DIST_PATH
    elif build_mode == "onefile":
        build_mode_option = "--onefile"
        dist_option = DEST_DIR

    # Set PyInstaller arguments
    pyinstaller_args = [
        "src/musicbrainz2notion/main.py",
        "--icon",
        str(ICON_PATH),
        "--specpath",
        str(SPEC_PATH),
        "--distpath",
        str(dist_option),
        "--name",
        APP_NAME,
        "--noconfirm",
        build_mode_option,
    ]
    if windowed:
        pyinstaller_args.append("--windowed")
        logger.info("Running in windowed mode")

    # Run PyInstaller
    logger.info(f"Running PyInstaller with args: {pyinstaller_args}")
    PyInstaller.__main__.run(pyinstaller_args)

    # Ensure DEST_DIR exists for copying files
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Destination directory ensured: {DEST_DIR}")

    # Copy necessary files to the distribution folder
    for file in OTHER_COPIED_DATA:
        shutil.copy(file, DEST_DIR)
    shutil.copy(".env.example", DEST_DIR / ".env")
    logger.info("Copied data to distribution folder")

    # Determine the OS suffix for the zip filename
    os_suffix = ""
    if platform.system() == "Darwin":
        os_suffix = "_macos"
    elif platform.system() == "Windows":
        os_suffix = "_windows"

    # Create a zip archive of the distribution folder
    zip_path = DIST_PATH / f"{APP_NAME}{os_suffix}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(DEST_DIR):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, os.path.relpath(file_path, DIST_PATH))

    logger.info(f"Zipped {DEST_DIR} to {zip_path}")


# Setup Cyclopts application
app = App()


@app.default
def main(
    build_mode: Annotated[
        Literal["onedir", "onefile"],
        Parameter(["--build-mode", "-b"]),
    ] = "onedir",
    windowed: Annotated[
        bool,
        Parameter(["--windowed", "-w"]),
    ] = False,
) -> None:
    """
    Build script for musicbrainz2notion.

    Args:
        build_mode: Specify the build mode.
            !! Configuration with settings.toml and .env doesn't work with onefile.
        windowed: Run in windowed mode.
            !! Not tested; probably doesn't work.
    """
    logger.info(f"Build mode: {build_mode}, Windowed: {windowed}")
    build_executable(build_mode, windowed)


if __name__ == "__main__":
    app()
