# NHS GP Appointments - Data Profiling Report

## Overview

This report summarises the structure and basic quality of the supplied appointment datasets.

## appointments_regional.csv

- **Rows:** 596,821
- **Columns:** 7
- **Missing values:** 0

### Likely row-level grain

Appointment counts grouped by ICB, appointment month, appointment status, healthcare professional type, appointment mode, and time-between-booking-and-appointment category.

### Column profile

| Column | Data type | Missing values | Distinct values |
|---|---|---:|---:|
| icb_ons_code | object | 0 | 42 |
| appointment_month | object | 0 | 30 |
| appointment_status | object | 0 | 3 |
| hcp_type | object | 0 | 3 |
| appointment_mode | object | 0 | 5 |
| time_between_book_and_appointment | object | 0 | 8 |
| count_of_appointments | int64 | 0 | 22,807 |

### Date ranges

No columns with 'date' in their name were identified.

## national_categories.csv

- **Rows:** 817,394
- **Columns:** 8
- **Missing values:** 0

### Likely row-level grain

Appointment counts grouped by appointment date, ICB, sub-ICB location name, service setting, context type, national category, and appointment month.

### Column profile

| Column | Data type | Missing values | Distinct values |
|---|---|---:|---:|
| appointment_date | object | 0 | 334 |
| icb_ons_code | object | 0 | 42 |
| sub_icb_location_name | object | 0 | 106 |
| service_setting | object | 0 | 5 |
| context_type | object | 0 | 3 |
| national_category | object | 0 | 18 |
| count_of_appointments | int64 | 0 | 9,957 |
| appointment_month | object | 0 | 11 |

### Date ranges

- **appointment_date:** 2021-08-01 to 2022-06-30

## actual_duration.csv

- **Rows:** 137,793
- **Columns:** 8
- **Missing values:** 0

### Likely row-level grain

One row represents appointment counts for a sub-ICB location, appointment day, service setting, and national category combination. The dataset also includes ICB code, context type, and appointment month.

### Column profile

| Column | Data type | Missing values | Distinct values |
|---|---|---:|---:|
| sub_icb_location_code | object | 0 | 106 |
| sub_icb_location_ons_code | object | 0 | 106 |
| sub_icb_location_name | object | 0 | 106 |
| icb_ons_code | object | 0 | 42 |
| region_ons_code | object | 0 | 7 |
| appointment_date | object | 0 | 212 |
| actual_duration | object | 0 | 7 |
| count_of_appointments | int64 | 0 | 7,611 |

### Date ranges

- **appointment_month:** January 2020 to June 2022 (30 months), as specified in the ETL Plan and Installation Guide.

## Initial data-quality observations

- Check date formats and confirm that dates were interpreted correctly before transformations.
- Check category labels for inconsistent capitalisation, spacing, and spelling.
- Confirm the intended grain of each dataset before joining tables or aggregating appointment counts.
- Check whether any duplicate-looking rows are legitimate records at the dataset's intended level of detail.
- Review the metadata file to confirm field definitions and the meaning of appointment counts.
- A zero missing-value count does not guarantee that a dataset is free from other data-quality issues.

## Limitations

- Distinct counts are calculated from non-null values converted to strings.
- Data types are inferred by pandas and may need explicit conversion during transformation.
- Date ranges are exploratory and should be validated against the source data and metadata.
- The row-level grain descriptions are provisional and should be confirmed against the source metadata.

## Five Data Quality Traps

### 1. Excel file disguised as CSV
The file `actual_duration.csv.xlsx` is an Excel workbook, despite its filename containing `.csv`. During extraction, pandas converts the workbook into a genuine CSV file at `data/raw/actual_duration.csv`. The original workbook remains unchanged.

### 2. Byte-order mark (BOM)
The `national_categories.csv` file contains a hidden byte-order mark (BOM) at the beginning of its first column name. This can cause the column to load as `\ufeffappointment_date` instead of `appointment_date`. The BOM must be removed from column names during transformation.

### 3. Day-first date format
Dates in `national_categories.csv` use the day-first format `dd/MM/yyyy`. For example, `02/08/2021` means 2 August 2021. The date format must be specified explicitly during transformation to avoid incorrect date interpretation.

### 4. Legitimate repeated rows in the regional dataset
The regional dataset contains 21,604 exact duplicate occurrences. According to the ETL Plan and Installation Guide, these are legitimate records caused by the removal of sub-ICB columns from the supplied dataset. Different sub-ICB locations within the same ICB can therefore produce identical remaining rows. These records must not be dropped. In Week 2, records will be grouped by all descriptive columns and their `count_of_appointments` values summed.

Expected transformed regional row count: 295,692.

Expected regional appointment total: 742,804,525.

### 5. Inconsistent labels and sorting
The datasets contain inconsistent text labels, including double spaces in booking-wait bands and `Other Practice staff` instead of `Other Practice Staff`. Alphabetical sorting also places booking-wait bands in an unsuitable order, such as `1 Day` before `Same Day`. Labels must be standardised and booking-wait bands assigned an explicit sort order during transformation.

## Dataset Grain

- **Regional dataset:** One row represents an ICB, month, appointment status, healthcare professional type, appointment mode and booking-wait band combination.
- **National categories dataset:** One row represents a sub-ICB location, appointment day, service setting and national category combination.
- **Actual duration dataset:** One row represents a sub-ICB location, appointment day and consultation-duration band combination.

## Data Quality Notes

- The three datasets cover different reporting periods.
- The regional dataset contains repeated rows that must be aggregated rather than deleted.
- Date parsing, BOM removal and label standardisation will be implemented during the transformation stage.
- The original raw files must remain unchanged.

## Source

NHS England, Appointments in General Practice statistics. Dataset definitions and data-quality notes are documented in the supplied metadata_nhs.txt and the October 2026 ETL Plan and Installation Guide.