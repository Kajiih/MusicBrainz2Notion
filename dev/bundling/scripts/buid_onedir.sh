#!/bin/bash

# Define variables for distribution path and application name
SPEC_PATH="dev/bundling"
DIST_PATH="dist"
APP_NAME="musicbrainz2notion"
DEST_DIR="$DIST_PATH/$APP_NAME"

# Build the executable with PyInstaller
pyinstaller src/musicbrainz2notion/main.py \
    --icon "media/musicbrainz_black_and_white.png" \
    --specpath "$SPEC_PATH" \
    --distpath "$DIST_PATH" \
    --name "$APP_NAME" \
    --onedir \
    --noconfirm #--windowed

# Copy necessary files to the distribution folder
cp settings.toml "$DEST_DIR"
cp .env.example "$DEST_DIR/.env"

# Create a zip archive of the distribution folder
cd "$DIST_PATH" || exit
zip -r "${APP_NAME}.zip" "$APP_NAME"
cd - || exit

echo "Zipped $DEST_DIR to ${DIST_PATH}/${APP_NAME}.zip"
