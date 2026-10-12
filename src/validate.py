
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

FILES = [
    "appointments_regional.csv",
    "national_categories.csv",
    "actual_duration.csv",
]


def validate_csv(filename):
    file_path = RAW_DATA_DIR / filename

    print(f"\n{'=' * 60}")
    print(f"Dataset: {filename}")
    print(f"{'=' * 60}")

    total_rows = 0
    duplicate_rows = 0

    # Keep only hashes of rows already seen, rather than loading
    # the entire dataset into memory.
    seen_hashes = set()

    for chunk in pd.read_csv(
        file_path,
        chunksize=50_000,
        encoding="utf-8-sig",
        low_memory=False,
    ):
        chunk.columns = chunk.columns.str.strip()
        total_rows += len(chunk)

        row_hashes = pd.util.hash_pandas_object(
            chunk,
            index=False,
        )

        # Count repeated rows within and across chunks.
        for row_hash in row_hashes:
            value = int(row_hash)

            if value in seen_hashes:
                duplicate_rows += 1
            else:
                seen_hashes.add(value)

    print(f"Total rows: {total_rows:,}")
    print(f"Exact duplicate rows detected: {duplicate_rows:,}")


def main():
    for filename in FILES:
        file_path = RAW_DATA_DIR / filename

        if not file_path.exists():
            print(f"\nWARNING: File not found: {filename}")
            continue

        validate_csv(filename)

    print("\nValidation check complete.")


if __name__ == "__main__":
    main()
