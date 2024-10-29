"""Tools to process canonical MusicBrainz data."""

from __future__ import annotations

import shutil
import tarfile
from typing import TYPE_CHECKING

import pandas as pd
import zstandard as zstd
from loguru import logger

from musicbrainz2notion.canonical_data_download import download_and_validate_canonical_data
from musicbrainz2notion.musicbrainz_utils import MBID, CanonicalDataHeader

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


CANONICAL_DUMP_GLOB = "musicbrainz-canonical-dump-*/"
CANONICAL_RELEASE_FILE_NAME = "preprocessed_release_redirect.csv"


# === Preprocessing === #
def decompress_canonical_dump(tar_zst_path: Path, to_dir: Path) -> Path:
    """
    Decompress the canonical data dump and return the path to the extracted data.

    Args:
        tar_zst_path (Path): Path to the compressed canonical dump.
        to_dir (Path): Directory where the canonical data should be extracted.
        delete_compressed (bool): Whether to delete the compressed
            `.tar.zst` file after decompression. Defaults to True.
    """
    logger.info(f"Decompressing and extracting canonical data dump in {to_dir}")

    # Decompress the .zst file to a .tar file
    decompressed_tar_path = tar_zst_path.parent / tar_zst_path.stem
    logger.info(f"Decompressing {tar_zst_path}")

    with (
        tar_zst_path.open("rb") as compressed_file,
        decompressed_tar_path.open("wb") as decompressed_file,
    ):
        dctx = zstd.ZstdDecompressor()
        _ = dctx.copy_stream(compressed_file, decompressed_file)

    logger.info(f"Decompression complete: {decompressed_tar_path}")

    # Extract the .tar file
    logger.info(f"Extracting {decompressed_tar_path}")

    with tarfile.open(decompressed_tar_path, "r") as tar:
        tar.extractall(path=to_dir, filter="data")

    extracted_data_dir = to_dir / tar_zst_path.name.replace(".tar.zst", "")
    logger.info(f"Extraction complete: {extracted_data_dir}")

    # Clean up
    decompressed_tar_path.unlink()
    logger.info(f"Temporary file deleted")

    return extracted_data_dir


def preprocess_csv(
    file_path: Path,
    save_path: Path,
    keep_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """
    Preprocess a canonical data csv file.

    Args:
        file_path (Path): The path to the canonical data csv file.
        save_path (Path): The path to save the preprocessed data.
        keep_columns (Sequence[str] | None): The columns to keep in the
            preprocessed data. If None, all columns are kept.

    Returns:
        pd.DataFrame: The preprocessed data.
    """
    logger.info(f"Preprocessing canonical data from {file_path}...")

    if keep_columns is not None:
        keep_columns = list(keep_columns)

    df = pd.read_csv(
        file_path,
        dtype="string",
        usecols=keep_columns,
    )

    df.drop_duplicates(inplace=True)

    df.to_csv(save_path, index=False)

    logger.info(f"Saved preprocessed data to {save_path}.")

    return df


def preprocess_canonical_release_data(file_path: Path, save_path: Path) -> pd.DataFrame:
    """
    Preprocess the canonical release data csv file.

    Args:
        file_path (Path): The path to the canonical release data csv file.
        save_path (Path): The path to save the preprocessed data.

    Returns:
        pd.DataFrame: The preprocessed canonical release data.
    """
    keep_columns = [
        CanonicalDataHeader.RELEASE_GROUP_MBID,
        CanonicalDataHeader.CANONICAL_RELEASE_MBID,
    ]

    return preprocess_csv(
        file_path=file_path,
        save_path=save_path,
        keep_columns=keep_columns,
    )


# Note: Not used anymore
def preprocess_canonical_recording_data(file_path: Path, save_path: Path) -> pd.DataFrame:
    """
    Preprocess the canonical recording data csv file.

    Args:
        file_path (Path): The path to the canonical recording data csv file.
        save_path (Path): The path to save the preprocessed data.

    Returns:
        pd.DataFrame: The preprocessed canonical recording data.
    """
    keep_columns = [
        CanonicalDataHeader.CANONICAL_RELEASE_MBID,
        CanonicalDataHeader.CANONICAL_RECORDING_MBID,
    ]

    return preprocess_csv(
        file_path=file_path,
        save_path=save_path,
        keep_columns=keep_columns,
    )


def download_and_preprocess_canonical_data(
    data_dir: Path, keep_original: bool = False
) -> pd.DataFrame:
    """TODO."""
    # Download and decompress
    temp_dir = data_dir / "temp"
    compressed_data = download_and_validate_canonical_data(temp_dir)

    extracted_data_dir = decompress_canonical_dump(compressed_data, data_dir)

    # Clean up temp directory
    shutil.rmtree(temp_dir)
    del temp_dir

    # Preprocess
    csv_dir = get_csv_dir(extracted_data_dir)
    canonical_data_paths = [
        csv_dir / "canonical_musicbrainz_data.csv",
        csv_dir / "canonical_release_redirect.csv",
        csv_dir / "canonical_recording_redirect.csv",
    ]
    canonical_release_path = canonical_data_paths[1]

    preprocessed_release_path = csv_dir / CANONICAL_RELEASE_FILE_NAME

    preprocessed_release_df = preprocess_canonical_release_data(
        canonical_release_path, preprocessed_release_path
    )

    if not keep_original:
        for path in canonical_data_paths:
            path.unlink()

    # Clean up older data
    dump_dirs_sorted = sorted(data_dir.glob(CANONICAL_DUMP_GLOB))

    for old_dump in dump_dirs_sorted[:-1]:
        shutil.rmtree(old_dump)
    logger.info(f"Deleted old canonical data dumps.")

    logger.success("Canonical data downloaded and preprocessed with success!")

    return preprocessed_release_df


def get_csv_dir(extracted_data_dir: Path) -> Path:
    """TODO."""
    return extracted_data_dir / "canonical"


def load_canonical_release_data(data_dir: Path) -> pd.DataFrame:
    """TODO."""
    last_dump_dir = max(data_dir.glob(CANONICAL_DUMP_GLOB))
    csv_dir = get_csv_dir(last_dump_dir)

    canonical_release_path = csv_dir / CANONICAL_RELEASE_FILE_NAME

    return pd.read_csv(canonical_release_path)


# === Compute mapping === #
def get_release_group_to_release_map(
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
            strict=True,
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
