
from pathlib import Path
import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "data_profile.md"

# Read large CSV files in manageable chunks
CHUNK_SIZE = 50_000

# Description of the likely row-level grain of each dataset.
# These descriptions are based on the columns supplied in this project.
GRAIN_DESCRIPTIONS = {
    "appointments_regional.csv": (
        "Appointment counts grouped by ICB, appointment month, "
        "appointment status, healthcare professional type, appointment "
        "mode, and time-between-booking-and-appointment category."
    ),
    "national_categories.csv": (
        "Appointment counts grouped by appointment date, ICB, "
        "sub-ICB location name, service setting, context type, "
        "national category, and appointment month."
    ),
    "actual_duration.csv": (
        "Appointment counts grouped by sub-ICB location, appointment "
        "date, and actual-duration category, with ICB and regional "
        "geography codes also provided."
    ),
}


def profile_csv(file_path):
    """Profile a CSV file without loading the whole file into memory."""

    row_count = 0
    columns = None
    null_counts = None
    distinct_values = None
    data_types = None
    date_min = {}
    date_max = {}

    for chunk in pd.read_csv(
        file_path,
        chunksize=CHUNK_SIZE,
        encoding="utf-8-sig",
        low_memory=False,
    ):
        # Standardise column names by removing accidental surrounding spaces.
        chunk.columns = chunk.columns.str.strip()

        if columns is None:
            columns = list(chunk.columns)
            null_counts = {column: 0 for column in columns}
            distinct_values = {column: set() for column in columns}
            data_types = {}

        row_count += len(chunk)

        for column in columns:
            series = chunk[column]

            null_counts[column] += int(series.isna().sum())

            # Collect distinct non-null values for each column.
            distinct_values[column].update(
                series.dropna().astype(str).unique().tolist()
            )

            # Record the dtype encountered in the CSV.
            data_types[column] = str(series.dtype)

            # Attempt date parsing only for columns whose names contain
            # "date". Keep the original data unchanged.
            if "date" in column.lower():
                parsed_dates = pd.to_datetime(
                    series,
                    errors="coerce",
                    dayfirst=True,
                )

                valid_dates = parsed_dates.dropna()

                if not valid_dates.empty:
                    chunk_min = valid_dates.min()
                    chunk_max = valid_dates.max()

                    if (
                        column not in date_min
                        or chunk_min < date_min[column]
                    ):
                        date_min[column] = chunk_min

                    if (
                        column not in date_max
                        or chunk_max > date_max[column]
                    ):
                        date_max[column] = chunk_max

    return {
        "filename": file_path.name,
        "rows": row_count,
        "columns": columns or [],
        "null_counts": null_counts or {},
        "distinct_counts": {
            column: len(values)
            for column, values in (distinct_values or {}).items()
        },
        "data_types": data_types or {},
        "date_min": date_min,
        "date_max": date_max,
    }


def build_report(profiles):
    """Build a Markdown report containing the profiling results."""

    lines = [
        "# NHS GP Appointments - Data Profiling Report",
        "",
        "## Overview",
        "",
        "This report summarises the structure and basic quality "
        "of the supplied appointment datasets.",
        "",
    ]

    for profile in profiles:
        filename = profile["filename"]

        lines.extend([
            f"## {filename}",
            "",
            f"- **Rows:** {profile['rows']:,}",
            f"- **Columns:** {len(profile['columns'])}",
            f"- **Missing values:** "
            f"{sum(profile['null_counts'].values()):,}",
            "",
            "### Likely row-level grain",
            "",
            GRAIN_DESCRIPTIONS.get(
                filename,
                "The row-level grain has not yet been documented.",
            ),
            "",
            "### Column profile",
            "",
            "| Column | Data type | Missing values | Distinct values |",
            "|---|---|---:|---:|",
        ])

        for column in profile["columns"]:
            lines.append(
                f"| {column} "
                f"| {profile['data_types'].get(column, 'unknown')} "
                f"| {profile['null_counts'].get(column, 0):,} "
                f"| {profile['distinct_counts'].get(column, 0):,} |"
            )

        lines.extend([
            "",
            "### Date ranges",
            "",
        ])

        date_columns = [
            column
            for column in profile["columns"]
            if "date" in column.lower()
        ]

        if not date_columns:
            lines.append(
                "No columns with 'date' in their name were identified."
            )
        else:
            for column in date_columns:
                if (
                    column in profile["date_min"]
                    and column in profile["date_max"]
                ):
                    lines.append(
                        f"- **{column}:** "
                        f"{profile['date_min'][column].date()} to "
                        f"{profile['date_max'][column].date()}"
                    )
                else:
                    lines.append(
                        f"- **{column}:** No valid dates were parsed."
                    )

        lines.append("")

    lines.extend([
        "## Initial data-quality observations",
        "",
        "- Check date formats and confirm that dates were interpreted "
        "correctly before transformations.",
        "- Check category labels for inconsistent capitalisation, "
        "spacing, and spelling.",
        "- Confirm the intended grain of each dataset before joining "
        "tables or aggregating appointment counts.",
        "- Check whether any duplicate-looking rows are legitimate "
        "records at the dataset's intended level of detail.",
        "- Review the metadata file to confirm field definitions and "
        "the meaning of appointment counts.",
        "- A zero missing-value count does not guarantee that a dataset "
        "is free from other data-quality issues.",
        "",
        "## Limitations",
        "",
        "- Distinct counts are calculated from non-null values converted "
        "to strings.",
        "- Data types are inferred by pandas and may need explicit "
        "conversion during transformation.",
        "- Date ranges are exploratory and should be validated against "
        "the source data and metadata.",
        "- The row-level grain descriptions are provisional and should "
        "be confirmed against the source metadata.",
        "",
    ])

    return "\n".join(lines)


def main():
    """Profile all expected CSV files and write the Markdown report."""

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    expected_files = [
        "appointments_regional.csv",
        "national_categories.csv",
        "actual_duration.csv",
    ]

    profiles = []

    for filename in expected_files:
        file_path = RAW_DATA_DIR / filename

        if not file_path.exists():
            print(f"WARNING: File not found, skipping: {file_path}")
            continue

        print(f"Profiling {filename}...")

        try:
            profile = profile_csv(file_path)
            profiles.append(profile)

            print(
                f"  Rows: {profile['rows']:,} | "
                f"Columns: {len(profile['columns'])}"
            )

        except Exception as error:
            print(f"ERROR profiling {filename}: {error}")
            raise

    if not profiles:
        raise FileNotFoundError(
            f"No expected CSV files were found in {RAW_DATA_DIR}"
        )

    report = build_report(profiles)

    OUTPUT_FILE.write_text(report + "\n", encoding="utf-8")

    print(f"\nProfiling complete.")
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
