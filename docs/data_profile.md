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

Appointment counts grouped by sub-ICB location, appointment date, and actual-duration category, with ICB and regional geography codes also provided.

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

- **appointment_date:** 2021-01-12 to 2022-12-06

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

