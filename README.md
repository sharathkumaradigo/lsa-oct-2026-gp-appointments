# NHS GP Appointments ETL Project

## Project Overview
This project explores NHS GP appointments data and prepares it for a data engineering pipeline. The work includes source data extraction, profiling, validation, and documentation.

## Project Structure

```text
lsa-oct-2026-gp-appointments/
├── data/
│   ├── raw/                         # Original source files
│   └── processed/
│       ├── regional/                # Monthly-partitioned Parquet
│       ├── national_categories/     # Monthly-partitioned Parquet
│       └── duration/                # Monthly-partitioned Parquet
├── docs/
│   ├── data_profile.md              # Data profiling findings
│   └── decision_log.md              # Transformation decisions
├── src/
│   ├── data_profile.py              # Profiles source datasets
│   └── transform.py                 # Cleans, validates and writes Parquet
├── tests/
│   └── test_transform.py            # Automated transformation tests
├── .gitignore
├── requirements.txt
└── README.md
```

## Run the Pipeline

Run commands from the project root.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the transformation pipeline:

```bash
python src/transform.py
```

Run the automated tests:

```bash
python -m pytest
```

The transformation script reads the three source datasets, applies the configured cleaning and validation rules, and writes month-partitioned Parquet outputs under `data/processed/`.

## Transformation and Validation

- Explicit PySpark schemas are used for the source datasets.
- Regional records sharing the six descriptive columns are aggregated by summing `count_of_appointments`.
- Selected text fields are standardised by trimming whitespace and replacing repeated whitespace with a single space.
- Inconsistent practice staff labels are standardised.
- National categories dates are parsed using `dd/MM/yyyy`.
- The duration source is read from the `actual_duration` worksheet in the Excel workbook.
- Processed datasets are written as Parquet partitioned by month.
- Row counts and appointment totals are checked to detect unintended changes during transformation.

### Latest Validation Results

| Dataset | Raw rows | Output rows | Appointment total |
|---|---:|---:|---:|
| Regional appointments | 596,821 | 295,692 | 742,804,525 |
| National categories | 817,394 | 817,394 | 296,046,770 |
| Appointment duration | 137,793 | 137,793 | 167,980,692 |

The pipeline completed successfully, and all three current automated tests passed.

## Current Status

- Source extraction and data profiling completed.
- Transformation logic implemented for all three datasets.
- Validation checks and monthly Parquet outputs implemented.
- Three automated transformation tests passing.
- Further test coverage, output-size comparisons, wait-band ordering and downstream data modelling remain to be completed.


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

## Storage Size Comparison

| Dataset / Folder | Size (MB) |
|---|---:|
| Raw source data (`data/raw`) | 162.04 |
| Cleaned regional Parquet | 1.44 |
| Cleaned national categories Parquet | 2.54 |
| Cleaned duration Parquet | 0.48 |
| **Total cleaned Parquet outputs** | **4.46** |

The cleaned datasets are stored as Parquet files partitioned by month. Folder sizes are measured from the files currently present in each directory; the raw folder size includes all files stored under `data/raw`.
