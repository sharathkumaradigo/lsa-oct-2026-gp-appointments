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

## Data Warehouse Design

### Architecture

The pipeline separates source data, transformation, and downstream analytical modelling.

```text
data/raw/
    |
    v
src/extract.py
    |
    v
src/transform.py
    |
    v
data/processed/
    |-- regional/
    |-- national_categories/
    |-- duration/
    |
    v
Downstream star schema and KPI analysis
```

`run_pipeline.py` runs the extraction and transformation stages in sequence. The cleaned datasets are stored as Parquet files partitioned by month. Raw source files are retained separately from the transformed outputs.

### Star Schema Design

The warehouse design uses three fact tables because the datasets have different levels of detail. They should not be joined row by row; doing so could multiply appointment counts. Shared dimensions should be conformed where the underlying fields represent the same concepts.

#### 1. `fact_appointments_monthly`

**Grain:** One row per ICB, month, appointment status, staff type, appointment mode and booking-wait category.

**Purpose:** Supports KPIs 1–8 using monthly appointment counts and the relevant categorical breakdowns.

#### 2. `fact_appointments_by_category`

**Grain:** One row per Sub-ICB location, day, service setting and national category.

**Purpose:** Supports KPIs 9, 10 and 12 using appointment counts by category and service setting.

#### 3. `fact_appointments_by_duration`

**Grain:** One row per Sub-ICB location, day and appointment-duration band.

**Purpose:** Supports KPIs 11 and 12 using appointment counts by duration band.

### Dimensions

- **Geography dimension:** Sub-ICB location, ICB and region, with valid geographic relationships.
- **Date dimension:** Calendar date, month and weekday attributes, shared across facts where compatible.
- **Booking-wait dimension:** Booking-wait categories and their numeric sort order.
- **Duration dimension:** Duration bands and their numeric sort order.
- **National category dimension:** National category labels and context type.

Dimensions should use consistent labels and sorting attributes so that reports can compare categories correctly. Each fact table should retain the keys appropriate to its own grain.

### KPI Calculation and Denominators

Fact tables store appointment counts at their defined grains. Rates and percentages should be calculated at reporting time from the relevant numerator and denominator, rather than by summing pre-calculated percentages.

The denominator must match the KPI definition and its applicable population, geography and time period. The specific denominator for each KPI must be documented against the supplied KPI definitions before implementation; it should not be assumed to be the same for every KPI.

### Data Integrity

The transformation pipeline validates source and cleaned appointment totals. Regional rows are aggregated where their identifying dimensions match, while preserving the overall appointment total. Automated tests cover aggregation, label standardisation, date parsing, positive counts, unique regional keys and monthly partition values.