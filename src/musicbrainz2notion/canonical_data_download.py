"""Tools to download canonical MusicBrainz data."""

from __future__ import annotations

import asyncio
import hashlib
import re
from pathlib import Path

import httpx
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm.auto import tqdm

BASE_URL = "https://data.metabrainz.org/pub/musicbrainz/canonical_data/"
TIMEOUT = 10

COMPRESSED_FILE_GLOB = "musicbrainz-canonical-dump-*.tar.zst"
DUMP_DIR_NAME_REGEX = r"^musicbrainz-canonical-dump-\d{8}-\d{6}/$"
DUMP_FILE_NAME_REGEX = r"^musicbrainz-canonical-dump-\d{8}-\d{6}\.tar\.zst(\.md5|\.sha256)?$"
SUCCESS_STATUS_CODE = 200


# %% === URL parsing and download === #
class NoDumpDirectoriesFoundError(Exception):
    """Exception raised when no dump directories are found in the index page."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        super().__init__(f"No dump directories found at URL: {base_url}")


class FetchDumpDirectoryFailError(Exception):
    """Exception raised when the request to fetch the canonical data dump index page fails."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        super().__init__(f"Failed to fetch dump directory from URL: {base_url}")


class FailedToFetchDumpFileError(Exception):
    """Exception raised when the request to fetch the dump file list from the dump directory fails."""

    def __init__(self, dump_url: str) -> None:
        self.dump_url = dump_url
        super().__init__(f"Failed to fetch dump files from URL: {dump_url}")


class WrongDumpFileNumberError(Exception):
    """Exception raised when the number of expected files in the dump directory is incorrect."""

    def __init__(self, dump_url: str, file_links: list[str]) -> None:
        self.dump_url = dump_url
        self.file_links = file_links
        expected_files = 3  # Should be .tar.zst, .md5, and .sha256
        super().__init__(
            f"Expected {expected_files} files (compressed dump and checksums) in {dump_url}, but found {len(file_links)}: {file_links}"
        )


class FailedToDownloadDumpFileError(Exception):
    """Currently unused."""


def parse_most_recent_dump_url(base_url: str) -> str:
    """
    Parse the URL of the most recent canonical data dump from the index page.

    Args:
        base_url (str): The URL of the MusicBrainz canonical data index.

    Returns:
        str: The URL of the most recent dump directory.
    """
    logger.info(f"Fetching the most recent canonical data dump directory URL in: {base_url}")

    response = requests.get(base_url, timeout=TIMEOUT)
    if response.status_code != SUCCESS_STATUS_CODE:
        raise FetchDumpDirectoryFailError(base_url)

    soup = BeautifulSoup(response.text, "html.parser")
    # Find all directory links
    pattern = re.compile(DUMP_DIR_NAME_REGEX)

    dump_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        # if "musicbrainz-canonical-dump-" in a["href"]
        if re.match(pattern, a["href"])
    ]
    if not dump_links:
        raise NoDumpDirectoriesFoundError(base_url)

    # Sort the dump directories by date (the directory names contain dates)
    dump_links = sorted(dump_links, reverse=True)
    last_dump_url = base_url + dump_links[0]

    logger.info(f"Most recent canonical data dump directory found: {last_dump_url}")

    return last_dump_url


def parse_files_in_dump(dump_url: str) -> list[str]:
    """
    Parse the list of files (compressed dump and checksums) from the dump directory.

    Args:
        dump_url (str): The URL of the most recent dump directory.

    Returns:
        list[str]: List of URLs to the compressed dump and checksum files.
    """
    logger.info(f"Fetching the list of files in the dump directory")

    response = requests.get(dump_url, timeout=TIMEOUT)
    if response.status_code != SUCCESS_STATUS_CODE:
        raise FailedToFetchDumpFileError(dump_url)

    soup = BeautifulSoup(response.text, "html.parser")
    # Get all relevant files (.tar.zst and its checksums)
    pattern = re.compile(DUMP_FILE_NAME_REGEX)
    file_links = [a["href"] for a in soup.find_all("a", href=True) if re.match(pattern, a["href"])]

    if len(file_links) != 3:  # noqa: PLR2004
        raise WrongDumpFileNumberError(dump_url, file_links)

    logger.info(f"Found {len(file_links)} files in the dump directory")

    # Return the full URLs of the files
    return [dump_url + file_link for file_link in file_links]


# Old version
def download_file_old(url: str, dest: Path) -> None:
    """
    Download a file from a given URL to a destination path.

    Args:
        url (str): The URL of the file to download.
        dest (Path): The destination path where the file should be saved.
    """
    logger.info(f"Downloading {url} to {dest}")

    response = requests.get(url, stream=True, timeout=TIMEOUT)
    if response.status_code != SUCCESS_STATUS_CODE:
        raise FailedToDownloadDumpFileError(url)

    with dest.open("wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    logger.info(f"Download of {url} to {dest} completed")


async def download_file(url: str, dest: Path) -> None:
    """
    Asynchronously download a file from the specified URL and save it to the destination path.

    Based on: https://pub.aimind.so/download-large-file-in-python-with-beautiful-progress-bar-f4f86b394ad7

    Args:
        url (str): The URL of the file to download.
        dest (Path): The destination path where the downloaded file will be saved.
    """
    async with httpx.AsyncClient() as client, client.stream("GET", url) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))

        tqdm_params = {
            "desc": f"Downloading {dest.name}",
            "total": total,
            "miniters": 1,
            "unit": "B",
            "unit_scale": True,
            "unit_divisor": 1024,
        }
        downloaded = 0  # Initialize bytes downloaded
        with tqdm(**tqdm_params) as pb, dest.open("wb") as f:  # type: ignore
            async for chunk in r.aiter_bytes():
                f.write(chunk)
                downloaded += len(chunk)
                pb.update(len(chunk))


async def download_canonical_data(to_dir: Path) -> None:
    """
    Download the most recent canonical data dump (compressed dump and checksums) to the specified directory.

    Args:
        to_dir (Path): The directory where the dump files should be downloaded.
    """
    logger.info(f"Downloading the most recent canonical data dump to {to_dir}")

    # Get the most recent dump URL
    dump_url = parse_most_recent_dump_url(BASE_URL)

    # Get the file URLs in the dump directory
    file_urls = parse_files_in_dump(dump_url)

    # Download each file to the specified directory
    to_dir.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_running_loop()
    urls_and_names = [(url, to_dir / url.split("/")[-1]) for url in file_urls]

    tasks = [loop.create_task(download_file(url, name)) for url, name in urls_and_names]

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"Download completed")


# %% === Checksum === #
class ChecksumMismatchError(Exception):
    """Exception raised when the checksum of the file does not match the expected value from the checksum file."""

    def __init__(self, file_path: Path, checksum_path: Path, checksum_type: str) -> None:
        super().__init__(
            f"{checksum_type.upper()} checksum mismatch for {file_path} "
            f"(expected checksum from {checksum_path})"
        )


class CompressedCanonicalDumpNotFoundError(Exception):
    """Exception raised when no compressed canonical dump (.tar.zst) file is found in the given directory."""

    def __init__(self, dumps_dir: Path) -> None:
        super().__init__(f"No compressed canonical dump found in {dumps_dir}")


class TooManyCompressedCanonicalDumpsError(Exception):
    """Exception raised when there are multiple compressed canonical dump (.tar.zst) files in the given directory, which is not allowed."""

    def __init__(self, dumps_dir: Path) -> None:
        super().__init__(
            f"Too many compressed canonical dumps found in {dumps_dir}. Pleas keep only one compressed data dump."
        )


def calculate_hash(file_path: Path, hash_type: str) -> str:
    """
    Calculate the hash of a given file using the specified hash algorithm.

    Args:
        file_path (Path): The path to the file whose hash needs to be calculated.
        hash_type (str): The hash type to use (e.g., 'md5', 'sha256').

    Returns:
        str: The calculated hash value in hexadecimal format.
    """
    hash_func = hashlib.new(hash_type)
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def is_checksum_valid(file_path: Path, checksum_file: Path, hash_type: str) -> bool:
    """
    Validate the checksum of a file by comparing its hash to the value in a checksum file.

    Args:
        file_path (Path): The path to the file whose checksum is being validated.
        checksum_file (Path): The path to the file containing the expected checksum.
        hash_type (str): The hash type to use for the validation (e.g., 'md5', 'sha256').

    Returns:
        bool: True if the computed checksum matches the expected checksum, otherwise False.
    """
    with checksum_file.open("r") as f:
        expected_checksum = (
            f.read().strip().split()[0]
        )  # Assume checksum file contains the checksum at the start

    computed_checksum = calculate_hash(file_path, hash_type)

    return computed_checksum == expected_checksum


def find_data_dump_files(dumps_dir: Path) -> tuple[Path, Path, Path]:
    """TODO."""
    # Identify the .tar.zst file
    tar_zst_files = list(dumps_dir.glob(COMPRESSED_FILE_GLOB))
    if not tar_zst_files:
        raise CompressedCanonicalDumpNotFoundError(dumps_dir)
    if len(tar_zst_files) > 1:
        raise TooManyCompressedCanonicalDumpsError(dumps_dir)

    tar_zst_path = tar_zst_files[0]

    # Identify corresponding .md5 and .sha256 files
    md5_path = Path(f"{tar_zst_path}.md5")
    sha256_path = Path(f"{tar_zst_path}.sha256")

    return tar_zst_path, md5_path, sha256_path


def validate_canonical_data_download(tar_zst_path: Path, md5_path: Path, sha256_path: Path) -> None:
    """TODO."""
    logger.info(f"Validating MD5 and SHA256 checksum for {tar_zst_path}")

    if not is_checksum_valid(tar_zst_path, md5_path, "md5"):
        raise ChecksumMismatchError(tar_zst_path, md5_path, "md5")

    logger.info(f"MD5 checksum valid for {tar_zst_path}")

    if not is_checksum_valid(tar_zst_path, sha256_path, "sha256"):
        raise ChecksumMismatchError(tar_zst_path, sha256_path, "sha256")

    logger.info(f"SHA256 checksum valid for {tar_zst_path}")


def download_and_validate_canonical_data(to_dir: Path) -> Path:
    """
    Download and validate the most recent canonical data dump (compressed dump and checksums).

    Args:
        to_dir (Path): The directory where the dump files should be downloaded.
    """
    asyncio.run(download_canonical_data(to_dir))

    tar_zst_path, md5_path, sha256_path = find_data_dump_files(to_dir)

    validate_canonical_data_download(tar_zst_path, md5_path, sha256_path)

    logger.success(f"Canonical data downloaded and validated. Perfect!")

    return tar_zst_path


# %% Example usage
if __name__ == "__main__":
    # Example: Run this async function
    dumps_dir = Path("data/new_data")
    # asyncio.run(download_canonical_data(dumps_dir))
