
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"

# Source files
REGIONAL_FILE = RAW_DIR / "appointments_regional.csv"
NATIONAL_FILE = RAW_DIR / "national_categories.csv"
EXCEL_FILE = RAW_DIR / "actual_duration.csv.xlsx"
METADATA_FILE = RAW_DIR / "metadata_nhs.txt"

# Output created from the Excel workbook
CONVERTED_FILE = RAW_DIR / "actual_duration.csv"


def calculate_sha256(file_path):
    """Calculate a file's SHA-256 checksum."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def count_csv_rows(file_path):
    """Count CSV data rows without loading the entire file into memory."""
    total_rows = 0

    for chunk in pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        chunksize=50_000,
    ):
        total_rows += len(chunk)

    return total_rows


def record_file(file_path, row_count=None, source_filename=None):
    """Collect metadata about one file."""
    return {
        "filename": file_path.name,
        "source_filename": source_filename or file_path.name,
        "size_bytes": file_path.stat().st_size,
        "sha256": calculate_sha256(file_path),
        "row_count": row_count,
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main():
    # Check that the expected source files exist.
    required_files = [
        REGIONAL_FILE,
        NATIONAL_FILE,
        EXCEL_FILE,
        METADATA_FILE,
    ]

    missing_files = [
        str(file_path)
        for file_path in required_files
        if not file_path.is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "These required files are missing:\n"
            + "\n".join(missing_files)
        )

    print("Starting Week 1 extraction...")

    # Convert the Excel workbook to CSV, preserving the original workbook.
    print(f"Converting {EXCEL_FILE.name} to {CONVERTED_FILE.name}...")

    excel_df = pd.read_excel(EXCEL_FILE)
    excel_df.to_csv(CONVERTED_FILE, index=False)

    print(f"Excel rows converted: {len(excel_df):,}")

    # Count rows in the two original CSV datasets.
    print("Counting rows in regional dataset...")
    regional_rows = count_csv_rows(REGIONAL_FILE)

    print("Counting rows in national categories dataset...")
    national_rows = count_csv_rows(NATIONAL_FILE)

    # Build the manifest. Metadata is a text file, so its row count is null.
    manifest = {
        "project": "NHS GP Appointments ETL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": [
            record_file(REGIONAL_FILE, regional_rows),
            record_file(NATIONAL_FILE, national_rows),
            record_file(EXCEL_FILE, len(excel_df)),
            record_file(
                CONVERTED_FILE,
                len(excel_df),
                source_filename=EXCEL_FILE.name,
            ),
            record_file(METADATA_FILE, None),
        ],
    }

    with MANIFEST_PATH.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    print("\nExtraction completed.")
    print(f"Manifest saved to: {MANIFEST_PATH}")
    print(f"Regional rows: {regional_rows:,}")
    print(f"National categories rows: {national_rows:,}")
    print(f"Actual duration rows: {len(excel_df):,}")


if __name__ == "__main__":
    main()
