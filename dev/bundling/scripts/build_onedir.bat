:: Define variables for distribution path and application name
set "SPEC_PATH=dev\bundling"
set "DIST_PATH=dist"
set "APP_NAME=musicbrainz2notion"
set "DEST_DIR=%DIST_PATH%\%APP_NAME%"

:: Build the executable with PyInstaller
pyinstaller src\musicbrainz2notion\main.py ^
    --icon "media\musicbrainz_black_and_white.png" ^
    --specpath "%SPEC_PATH%" ^
    --distpath "%DIST_PATH%" ^
    --name "%APP_NAME%" ^
	--onedir ^
    --noconfirm
:: --windowed

:: Ensure DEST_DIR exists
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

:: Copy necessary files to the distribution folder
copy settings.toml "%DEST_DIR%"
copy .env.example "%DEST_DIR%\.env"

:: Create a zip archive of the distribution folder
cd "%DIST_PATH%" || exit /b
powershell -command "Compress-Archive -Path '%APP_NAME%' -DestinationPath '%APP_NAME%.zip'"
cd ..

echo Zipped %DEST_DIR% to %DIST_PATH%\%APP_NAME%.zip
