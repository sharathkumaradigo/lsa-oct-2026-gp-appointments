
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "appointments_regional.csv"
)


def main():
    print("Loading regional appointments dataset...")

    df = pd.read_csv(
        FILE_PATH,
        encoding="utf-8-sig",
        low_memory=False,
    )

    df.columns = df.columns.str.strip()

    # Count exact duplicate rows, excluding the first occurrence.
    duplicate_mask = df.duplicated(keep="first")
    duplicate_count = int(duplicate_mask.sum())

    # Include every row belonging to a duplicate group.
    all_duplicate_mask = df.duplicated(keep=False)
    duplicate_groups = (
        df.loc[all_duplicate_mask]
        .groupby(list(df.columns), dropna=False)
        .size()
        .reset_index(name="occurrences")
        .sort_values("occurrences", ascending=False)
    )

    print("\n--- Duplicate verification ---")
    print(f"Total rows: {len(df):,}")
    print(f"Exact duplicate occurrences: {duplicate_count:,}")
    print(
        "Rows belonging to duplicate groups: "
        f"{int(all_duplicate_mask.sum()):,}"
    )
    print(f"Number of repeated row groups: {len(duplicate_groups):,}")

    print("\n--- First 10 repeated row groups ---")

    if duplicate_groups.empty:
        print("No repeated row groups found.")
    else:
        print(duplicate_groups.head(10).to_string(index=False))

    print("\n--- Dataset columns ---")
    print(df.columns.tolist())

    print("\nInspection complete. No source data was changed.")


if __name__ == "__main__":
    main()
