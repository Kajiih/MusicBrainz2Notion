"""Build the executable using PyInstaller."""

from __future__ import annotations

import os
import platform
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Annotated, Literal

import PyInstaller.__main__
from cyclopts import App, Parameter
from loguru import logger

# Define variables for distribution paths and application name
SPEC_PATH = Path("dev/bundling")
DIST_PATH = Path("dist")
APP_NAME = "musicbrainz2notion"
DEST_DIR = DIST_PATH / APP_NAME
SCRIPT_PATH = Path(__file__).resolve().parent
MEDIA_PATH = SCRIPT_PATH.parent.parent / "media"
ICON_PATH = MEDIA_PATH / "musicbrainz_black_and_white.png"

logger.remove()
# Set up logging with loguru
logger.add(
    "logs/build.log",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)
logger.add(sys.stdout, level="INFO")


def build_executable(build_mode: Literal["onedir", "onefile"], windowed: bool) -> None:
    """Build the executable using PyInstaller based on the specified build mode and windowed option."""
    # Determine build mode and set options
    if build_mode == "onedir":
        build_mode_option = "--onedir"
        dist_option = DIST_PATH
    elif build_mode == "onefile":
        build_mode_option = "--onefile"
        dist_option = DEST_DIR
    else:
        logger.error(f"Invalid build mode: {build_mode}")
        sys.exit(1)

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
    shutil.copy("settings.toml", DEST_DIR)
    shutil.copy(".env.example", DEST_DIR / ".env")
    logger.info("Copied settings.toml and .env.example to distribution folder")

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


# Set up Cyclopts application
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
        windowed: Run in windowed mode.
    """
    logger.info(f"Build mode: {build_mode}, Windowed: {windowed}")
    build_executable(build_mode, windowed)


if __name__ == "__main__":
    app()
