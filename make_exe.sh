#!/bin/bash

# Define variables for distribution path and application name
DIST_PATH="dist"
APP_NAME="musicbrainz2notion"
DEST_DIR="$DIST_PATH/$APP_NAME"

# Build the executable with PyInstaller
pyinstaller src/musicbrainz2notion/main.py \
    --icon "media/musicbrainz_black_and_white.png" \
    --distpath "$DIST_PATH" \
    --name "$APP_NAME" \
    --noconfirm
# --onefile \
# --windowed \

# Copy pyproject.toml and config folder to the distribution folder
cp settings.toml "$DEST_DIR"
cp .env.example "$DEST_DIR/.env"
