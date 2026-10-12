# NHS GP Appointments ETL Project

## Project Overview
This project explores NHS GP appointments data and prepares it for a data engineering pipeline. The work includes source data extraction, profiling, validation, and documentation.

## Project Structure
```text
lsa-oct-2026-gp-appointments/
├── data/
│   └── raw/                  # Original source files (not committed)
├── docs/
│   └── data_profile.md       # Data profiling findings
├── src/
│   ├── extract.py            # Extracts and inventories source data
│   ├── profile.py            # Profiles dataset structure
│   ├── validate.py           # Checks data and duplicate rows
│   └── inspect_duplicates.py # Inspects regional duplicate rows
├── .gitignore
├── manifest.json             # Source file inventory and checksums
├── requirements.txt
└── README.md
```

## Source Datasets
- `appointments_regional.csv`
- `national_categories.csv`
- `actual_duration.csv.xlsx` — original Excel workbook
- `actual_duration.csv` — extracted CSV version
- `metadata_nhs.txt`

Raw data files are kept locally and excluded from version control.

## Setup
Use Python 3.11 or a compatible Python version.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the Pipeline Steps
Run commands from the project root:

```bash
python src/extract.py
python src/profile.py
python src/validate.py
python src/inspect_duplicates.py
```

## Data Quality Notes
- The national categories dataset may contain a UTF-8 byte order mark (BOM) in its first column name.
- Dates must be interpreted using the day-first format where applicable.
- Exact duplicate rows in the regional dataset are expected because sub-ICB details were removed from the published data. They must not be deleted as ordinary duplicates; the data should be aggregated according to the project requirements.
- Inconsistent labels and wait-band ordering require standardisation during transformation.

## Current Status
Week 1: source extraction, data profiling, validation, and documentation.

## Data Source
NHS GP appointments data supplied for the internship project. Refer to the project guide for source details, reporting periods, and limitations.
