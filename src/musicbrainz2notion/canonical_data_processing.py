"""Tools to download and process canonical MusicBrainz data."""

from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import zstandard as zstd
from loguru import logger

from musicbrainz2notion.musicbrainz_utils import MBID, CanonicalDataHeader

if TYPE_CHECKING:
    from collections.abc import Sequence


# === Preprocessing === #
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


class ChecksumMismatchError(Exception):
    """Exception raised when the checksum of the file does not match the expected value from the checksum file."""

    def __init__(self, file_path: Path, checksum_path: Path, checksum_type: str) -> None:
        super().__init__(
            f"{checksum_type.upper()} checksum mismatch for {file_path} "
            f"(expected checksum from {checksum_path})"
        )


def decompress_canonical_dump(dumps_dir: Path, delete_compressed: bool = False) -> None:
    """
    Decompress the canonical dump and validate the checksums.

    Args:
        dumps_dir (Path): The directory containing the `.tar.zst`, `.md5`, and
            `.sha256` files.
        delete_compressed (bool, optional): Whether to delete the compressed
            `.tar.zst` file and checksums after decompression. Defaults to False.

    Raises:
        CompressedCanonicalDumpNotFoundError: If no .tar.zst file is found.
        TooManyCompressedCanonicalDumpsError: If multiple .tar.zst files are found.
        ChecksumMismatchError: If the checksum validation fails.
    """
    logger.info(f"Decompressing and extracting canonical data dump in {dumps_dir}")

    # Identify the .tar.zst file
    tar_zst_files = list(dumps_dir.glob("musicbrainz-canonical-dump-*.tar.zst"))
    if not tar_zst_files:
        raise CompressedCanonicalDumpNotFoundError(dumps_dir)
    if len(tar_zst_files) > 1:
        raise TooManyCompressedCanonicalDumpsError(dumps_dir)

    tar_zst_path = tar_zst_files[0]
    logger.info(f"Found compressed dump: {tar_zst_path}")

    # Identify corresponding .md5 and .sha256 files
    md5_path = Path(f"{tar_zst_path}.md5")
    sha256_path = Path(f"{tar_zst_path}.sha256")

    # Validate checksums
    logger.info(f"Validating MD5 and SHA256 checksum for {tar_zst_path}")

    if not is_checksum_valid(tar_zst_path, md5_path, "md5"):
        raise ChecksumMismatchError(tar_zst_path, md5_path, "md5")

    logger.info(f"MD5 checksum valid for {tar_zst_path}")

    if not is_checksum_valid(tar_zst_path, sha256_path, "sha256"):
        raise ChecksumMismatchError(tar_zst_path, sha256_path, "sha256")

    logger.info(f"SHA256 checksum valid for {tar_zst_path}")

    # Decompress the .zst file to a .tar file
    decompressed_tar_path = dumps_dir / tar_zst_path.stem
    logger.info(f"Decompressing {tar_zst_path} to {decompressed_tar_path}")

    with (
        tar_zst_path.open("rb") as compressed_file,
        decompressed_tar_path.open("wb") as decompressed_file,
    ):
        dctx = zstd.ZstdDecompressor()
        dctx.copy_stream(compressed_file, decompressed_file)

    logger.info(f"Decompression complete: {decompressed_tar_path}")

    # Extract the .tar file
    logger.info(f"Extracting {decompressed_tar_path}")

    with tarfile.open(decompressed_tar_path, "r") as tar:
        tar.extractall(path=dumps_dir, filter="data")

    logger.info(f"Extraction complete for {decompressed_tar_path}")

    # Clean up
    decompressed_tar_path.unlink()
    logger.info(f"Removed decompressed .tar file: {decompressed_tar_path}")

    if delete_compressed:
        tar_zst_path.unlink()
        md5_path.unlink()
        sha256_path.unlink()

        logger.info(
            f"Deleted compressed and checksum files: {tar_zst_path}, {md5_path}, {sha256_path}"
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


def preprocess_canonical_data(
    file_path: str,
    save_path: str,
    keep_columns: Sequence[str] | None = None,
    delete_original: bool = False,
) -> pd.DataFrame:
    """
    Preprocess the canonical data and save them to a new file.

    Args:
        file_path (str): The path to the canonical data file.
        save_path (str): The path to save the preprocessed data.
        keep_columns (Sequence[str] | None): The columns to keep in the
            preprocessed data. If None, all columns are kept.
        delete_original (bool): If True, delete the original file after
            processing. Defaults to False.

    Returns:
        pd.DataFrame: The preprocessed data.
    """
    logger.info(f"Preprocessing canonical data from {file_path}...")

    if keep_columns is not None:
        keep_columns = list(keep_columns)

    df = pd.read_csv(
        filepath_or_buffer=file_path,
        dtype="string",
        usecols=keep_columns,
    )

    df.drop_duplicates(inplace=True)

    df.to_csv(save_path, index=False)

    logger.info(f"Saved preprocessed data to {save_path}.")

    if delete_original:
        Path(file_path).unlink()
        logger.info(f"Deleted original file {file_path}.")

    return df


def preprocess_canonical_release_data(
    file_path: str, save_path: str, delete_original: bool = False
) -> pd.DataFrame:
    """
    Preprocess the canonical release data and save them to a new file.

    Args:
        file_path (str): The path to the canonical release data file.
        save_path (str): The path to save the preprocessed data.
        delete_original (bool): If True, delete the original file after
            processing. Defaults to False.

    Returns:
        pd.DataFrame: The preprocessed canonical release data.
    """
    keep_columns = [
        CanonicalDataHeader.RELEASE_GROUP_MBID,
        CanonicalDataHeader.CANONICAL_RELEASE_MBID,
    ]

    return preprocess_canonical_data(
        file_path=file_path,
        save_path=save_path,
        keep_columns=keep_columns,
        delete_original=delete_original,
    )


# Note: Not used anymore
def preprocess_canonical_recording_data(
    file_path: str, save_path: str, delete_original: bool = False
) -> pd.DataFrame:
    """
    Preprocess the canonical recording data and save them to a new file.

    Args:
        file_path (str): The path to the canonical recording data file.
        save_path (str): The path to save the preprocessed data.
        delete_original (bool): If True, delete the original file after
            processing. Defaults to False.

    Returns:
        pd.DataFrame: The preprocessed canonical recording data.
    """
    keep_columns = [
        CanonicalDataHeader.CANONICAL_RELEASE_MBID,
        CanonicalDataHeader.CANONICAL_RECORDING_MBID,
    ]

    return preprocess_canonical_data(
        file_path=file_path,
        save_path=save_path,
        keep_columns=keep_columns,
        delete_original=delete_original,
    )


# === Compute mapping === #
def get_release_group_to_canonical_release_map(
    release_group_mbids: Sequence[str], canonical_release_df: pd.DataFrame
) -> dict[MBID, MBID]:
    """
    Return a map of release group MBIDs to their canonical release MBIDs.

    Args:
        release_group_mbids (set[str]): A set of release group MBIDs to map.
        canonical_release_df (pd.DataFrame): The DataFrame containing the
            canonical release mappings.

    Returns:
        dict[MBID, MBID]: A dictionary mapping release group MBIDs to their
            canonical release MBIDs.
    """
    # Filter rows to keep only the necessary release group mbids
    filtered_df = canonical_release_df[
        canonical_release_df[CanonicalDataHeader.RELEASE_GROUP_MBID].isin(release_group_mbids)
    ]

    # Convert to a dictionary
    canonical_release_mapping = dict(
        zip(
            filtered_df[CanonicalDataHeader.RELEASE_GROUP_MBID],
            filtered_df[CanonicalDataHeader.CANONICAL_RELEASE_MBID],
            strict=False,
        )
    )

    return canonical_release_mapping


# TODO: Return only a list if the mapping is not used?
# Note: Not used anymore
def get_canonical_release_to_canonical_recording_map(
    canonical_release_mbids: Sequence[str], canonical_recording_df: pd.DataFrame
) -> dict[MBID, list[MBID]]:
    """
    Return a dictionary mapping the canonical release MBIDs to the list of their canonical recording MBIDs.

    Args:
        canonical_release_mbids (set[str]): A set of canonical release MBIDs to
            map.
        canonical_recording_df (pd.DataFrame): The DataFrame containing the
            canonical recording mappings.

    Returns:
        dict[MBID, list[MBID]]: A dictionary mapping release group MBIDs to the
            list of their canonical recording MBIDs.
    """
    # Filter rows to keep only the necessary canonical release mbids
    filtered_df = canonical_recording_df[
        canonical_recording_df[CanonicalDataHeader.CANONICAL_RELEASE_MBID].isin(
            canonical_release_mbids
        )
    ]

    # Group the DataFrame by canonical_release_mbid
    grouped = filtered_df.groupby(CanonicalDataHeader.CANONICAL_RELEASE_MBID)[
        CanonicalDataHeader.CANONICAL_RECORDING_MBID
    ].apply(list)

    canonical_recordings = grouped.to_dict()

    return canonical_recordings


# %% Test
# from pathlib import Path

# from musicbrainz2notion.canonical_data_processing import decompress_canonical_dump

# dumps_dir = Path("data/new_data")
# decompress_canonical_dump(dumps_dir)
