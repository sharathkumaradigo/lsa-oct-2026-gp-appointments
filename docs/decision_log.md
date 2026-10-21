
# Data Transformation Decision Log

## Project
GP Appointments KPI Data Engineering Project

## Purpose
This document records the data-cleaning, transformation and validation
decisions made while preparing the GP appointments datasets for analysis.

## Decision 1: Regional duplicate-looking records

**Decision:** Aggregate records that share the six descriptive columns
and sum `count_of_appointments`.

**Reason:** The regional source contains duplicate-looking records that
must be combined rather than discarded.

**Validation:** The raw dataset contains 596,821 rows. The aggregated
dataset contains 295,692 rows. The appointment total remains 742,804,525.

## Decision 2: Explicit data schemas

**Decision:** Define explicit PySpark schemas for the source datasets.

**Reason:** Explicit schemas make expected data types clear and reduce
reliance on automatic type inference.

## Decision 3: National categories date parsing

**Decision:** Parse `appointment_date` using the day-first format
`dd/MM/yyyy`.

**Reason:** The source dates use the day/month/year convention.

**Validation:** The expected row count is 817,394 and the expected
appointment total is 296,046,770.

## Decision 4: National categories header

**Decision:** Supply an explicit schema when reading the CSV.

**Reason:** The source header may contain a UTF-8 byte order mark (BOM),
which can affect the first column name if not handled correctly.

## Decision 5: Appointment duration source format

**Decision:** Read `actual_duration.csv.xlsx` as an Excel workbook,
using the `actual_duration` worksheet.

**Reason:** The file extension includes `.csv`, but inspection confirms
that the source is an Excel workbook.

**Validation:** The expected row count is 137,793 and the expected
appointment total is 167,980,692.

## Decision 6: Text standardisation

**Decision:** Trim leading and trailing whitespace and replace repeated
whitespace with a single space in selected text fields.

**Reason:** Inconsistent spacing can affect grouping, comparisons and
reporting.

## Decision 7: Monthly Parquet partitioning

**Decision:** Add a month column and partition each Parquet output by month.

**Reason:** Monthly partitioning supports time-based filtering and
organises the processed data for downstream analysis.

## Decision 8: Raw source preservation

**Decision:** Keep raw source files unchanged and write transformed
data to separate processed output folders.

**Reason:** Preserving raw inputs supports reproducibility and allows
transformation results to be checked against the original data.

## Decision 9: Validation

**Decision:** Check expected row counts and appointment totals before
writing transformed outputs.

**Reason:** These checks help detect unintended row loss or changes
to appointment counts.

## Decision 10: Standardise practice staff labels

**Decision:** Convert case variations of `Other Practice staff` to `Other Practice Staff` in the `hcp_type` field.

**Reason:** Consistent labels reduce unnecessary category variations in reporting and analysis.

**Validation:** An automated test checks that inconsistent staff labels are standardised while unrelated labels such as `GP` remain unchanged.

## Decision 11: Shared whitespace-cleaning helper

**Decision:** Use a reusable `standardise_whitespace()` function to trim leading and trailing whitespace and replace repeated whitespace with a single space in selected text columns.

**Reason:** A shared function keeps whitespace-cleaning behaviour consistent across the regional, national categories and duration transformations.

**Validation:** An automated test verifies that a value containing leading, trailing and repeated whitespace is cleaned correctly.

## Decision 12: Automated transformation tests

**Decision:** Use pytest to test regional aggregation, whitespace standardisation and staff-label standardisation.

**Reason:** Automated tests provide repeatable checks of important transformation rules.

**Validation:** All three tests passed when run with `python -m pytest`.

## Decision 13: Parquet output validation

**Decision:** Validate expected row counts and appointment totals before writing the transformed datasets to month-partitioned Parquet folders.

**Reason:** These checks help identify unintended row loss or changes to appointment counts.

**Validation:** The pipeline completed successfully with the following results:

| Dataset | Raw rows | Output rows | Appointment total |
|---|---:|---:|---:|
| Regional appointments | 596,821 | 295,692 | 742,804,525 |
| National categories | 817,394 | 817,394 | 296,046,770 |
| Appointment duration | 137,793 | 137,793 | 167,980,692 |

## Outstanding items

- Add automated tests for additional required transformation rules, including date handling, row counts, appointment totals and partitioning.
- Verify explicit wait-band sort order.
- Record raw-to-Parquet size comparisons for all datasets.
- Review the final README and pipeline configuration.
- Develop and test the downstream data model and fact tables.

## Decision: Separate fact tables by grain

**Decision:** Model monthly appointments, appointments by national category, and appointments by duration as three separate fact tables.

**Reason:** The source datasets have different levels of detail. Joining them row by row could multiply appointment counts and produce incorrect KPI results.

**Impact:** Each fact table retains its own grain and applicable dimensions. Shared date and geography dimensions are conformed where their meanings and granularity are compatible.

## Decision: Calculate KPI rates at query time

**Decision:** Store appointment counts in the fact tables and calculate rates or percentages at reporting time.

**Reason:** Pre-calculated percentages cannot safely be summed across groups. The denominator must correspond to the relevant KPI definition, population, geography and reporting period.

**Impact:** The denominator for each KPI must be verified against the supplied KPI definitions before that KPI is implemented.

## Decision: Use a shared dimensional model

**Decision:** Define geography, date, booking-wait, duration and national-category dimensions for the relevant fact tables.

**Reason:** Consistent dimensions support comparable reporting, category sorting and analysis across compatible datasets.

**Impact:** Each fact table uses only the dimensions appropriate to its defined grain. Fact tables are not joined directly at row level for KPI calculations.
