
from pathlib import Path
import pandas as pd

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    DateType,
)


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "appointments_regional.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "regional"
CATEGORIES_FILE = PROJECT_ROOT / "data" / "raw" / "national_categories.csv"

CATEGORIES_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "national_categories"
)

DURATION_FILE = (
    PROJECT_ROOT / "data" / "raw" / "actual_duration.csv.xlsx"
)

DURATION_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "duration"
)

def create_spark_session():
    """Create a Spark session with project settings."""
    return (
        SparkSession.builder
        .appName("GPAppointmentsRegionalTransform")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem")
        .config("spark.hadoop.fs.permissions.enabled", "false")
        .getOrCreate()
    )


def standardise_whitespace(df, columns):
    """Trim labels and replace repeated whitespace with one space."""

    for column_name in columns:
        df = df.withColumn(
            column_name,
            F.regexp_replace(
                F.trim(F.col(column_name)),
                r"\s+",
                " ",
            ),
        )

    return df


def standardise_staff_type(df):
    """Standardise inconsistent practice staff labels."""

    return df.withColumn(
        "hcp_type",
        F.when(
            F.lower(F.trim(F.col("hcp_type")))
            == "other practice staff",
            "Other Practice Staff",
        ).otherwise(F.col("hcp_type")),
    )

def aggregate_regional_appointments(df):
    """Aggregate regional records while preserving appointment counts."""

    grouping_columns = [
        "icb_ons_code",
        "appointment_month",
        "appointment_status",
        "hcp_type",
        "appointment_mode",
        "time_between_book_and_appointment",
    ]

    return (
        df
        .groupBy(*grouping_columns)
        .agg(
            F.sum("count_of_appointments")
            .cast("long")
            .alias("count_of_appointments")
        )
    )


def transform_regional(spark):
    """Clean and aggregate the regional appointments data."""

    # Define the source schema explicitly.
    schema = StructType([
        StructField("icb_ons_code", StringType(), True),
        StructField("appointment_month", StringType(), True),
        StructField("appointment_status", StringType(), True),
        StructField("hcp_type", StringType(), True),
        StructField("appointment_mode", StringType(), True),
        StructField(
            "time_between_book_and_appointment",
            StringType(),
            True,
        ),
        StructField("count_of_appointments", LongType(), True),
    ])

    # Read the raw CSV without changing the source file.
    raw_df = (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(str(RAW_FILE))
    )

    raw_rows = raw_df.count()
    raw_total = raw_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Raw regional rows: {raw_rows:,}")
    print(f"Raw appointment total: {raw_total:,}")

    # Standardise wait-band whitespace.
    cleaned_df = standardise_whitespace(
        raw_df,
        ["time_between_book_and_appointment"],
    )

    # Aggregate duplicate-looking records without discarding counts.
    regional_df = aggregate_regional_appointments(cleaned_df)

    # Add a month column for partitioning the Parquet output.
    regional_df = regional_df.withColumn(
        "month",
        F.to_date(
            F.concat(F.col("appointment_month"), F.lit("-01")),
            "yyyy-MM-dd",
        ),
    )

    output_rows = regional_df.count()
    output_total = regional_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Clean regional rows: {output_rows:,}")
    print(f"Clean appointment total: {output_total:,}")

    # Verify the required results before writing.
    assert output_rows == 295_692, (
        f"Expected 295,692 rows, but got {output_rows:,}"
    )
    assert output_total == raw_total == 742_804_525, (
        f"Appointment total mismatch: raw={raw_total:,}, "
        f"clean={output_total:,}"
    )

    # Write Parquet partitioned by month.
    (
        regional_df
        .write
        .mode("overwrite")
        .partitionBy("month")
        .parquet(str(OUTPUT_DIR))
    )

    print(f"Regional Parquet saved to: {OUTPUT_DIR}")


def transform_national_categories(spark):
    """Clean and validate the national categories appointments data."""

    # Define the source schema explicitly.
    schema = StructType([
        StructField("appointment_date", StringType(), True),
        StructField("icb_ons_code", StringType(), True),
        StructField("sub_icb_location_name", StringType(), True),
        StructField("service_setting", StringType(), True),
        StructField("context_type", StringType(), True),
        StructField("national_category", StringType(), True),
        StructField("count_of_appointments", LongType(), True),
        StructField("appointment_month", StringType(), True),
    ])

    # Use the supplied schema so the BOM in the source header
    # does not become part of the Spark column names.
    raw_df = (
        spark.read
        .option("header", True)
        .option("encoding", "UTF-8")
        .schema(schema)
        .csv(str(CATEGORIES_FILE))
    )

    raw_rows = raw_df.count()
    raw_total = raw_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Raw national categories rows: {raw_rows:,}")
    print(f"Raw national categories total: {raw_total:,}")

    # Standardise surrounding and repeated whitespace in labels.

    text_columns = [
        "icb_ons_code",
        "sub_icb_location_name",
        "service_setting",
        "context_type",
        "national_category",
    ]

    
    cleaned_df = standardise_whitespace(raw_df, text_columns)



    # Parse dates explicitly using the required day-first format.
    cleaned_df = cleaned_df.withColumn(
        "appointment_date",
        F.to_date(
            F.col("appointment_date"),
            "dd/MM/yyyy",
        ),
    )

    # Add a date column representing the first day of each month.
    cleaned_df = cleaned_df.withColumn(
        "month",
        F.trunc(F.col("appointment_date"), "month"),
    )

    # Check for missing or invalid dates and appointment counts.
    invalid_dates = cleaned_df.filter(
        F.col("appointment_date").isNull()
    ).count()

    invalid_counts = cleaned_df.filter(
        F.col("count_of_appointments").isNull()
    ).count()

    assert invalid_dates == 0, (
        f"Found {invalid_dates:,} missing or invalid appointment dates"
    )

    assert invalid_counts == 0, (
        f"Found {invalid_counts:,} missing appointment counts"
    )

    output_rows = cleaned_df.count()
    output_total = cleaned_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Clean national categories rows: {output_rows:,}")
    print(f"Clean national categories total: {output_total:,}")

    # Validate that cleaning did not lose rows or appointment counts.
    assert raw_rows == output_rows == 817_394, (
        f"Expected 817,394 rows; raw={raw_rows:,}, "
        f"clean={output_rows:,}"
    )

    assert raw_total == output_total == 296_046_770, (
        f"Appointment total mismatch: raw={raw_total:,}, "
        f"clean={output_total:,}"
    )

    # Write the cleaned data as month-partitioned Parquet.
    (
        cleaned_df
        .write
        .mode("overwrite")
        .partitionBy("month")
        .parquet(str(CATEGORIES_OUTPUT_DIR))
    )

    print(
        "National categories Parquet saved to: "
        f"{CATEGORIES_OUTPUT_DIR}"
    )


def transform_duration(spark):
    """Read, clean and validate the actual appointment duration data."""

    schema = StructType([
        StructField("sub_icb_location_code", StringType(), True),
        StructField("sub_icb_location_ons_code", StringType(), True),
        StructField("sub_icb_location_name", StringType(), True),
        StructField("icb_ons_code", StringType(), True),
        StructField("region_ons_code", StringType(), True),
        StructField("appointment_date", DateType(), True),
        StructField("actual_duration", StringType(), True),
        StructField("count_of_appointments", LongType(), True),
    ])

    # This source is an Excel workbook, not a CSV file.
    pandas_df = pd.read_excel(
        DURATION_FILE,
        sheet_name="actual_duration",
        engine="openpyxl",
    )

    # Ensure dates become Python date objects before creating the
    # Spark DataFrame with its explicit schema.
    pandas_df["appointment_date"] = (
        pd.to_datetime(
            pandas_df["appointment_date"],
            errors="coerce",
        )
        .dt.date
    )

    # Convert NumPy/Pandas values into ordinary Python values.
    records = list(
        pandas_df.itertuples(index=False, name=None)
    )

    duration_df = spark.createDataFrame(
        records,
        schema=schema,
    )

    raw_rows = duration_df.count()
    raw_total = duration_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Raw duration rows: {raw_rows:,}")
    print(f"Raw duration appointment total: {raw_total:,}")

    # Standardise whitespace in text columns without changing
    # the original source workbook.
    text_columns = [
        "sub_icb_location_code",
        "sub_icb_location_ons_code",
        "sub_icb_location_name",
        "icb_ons_code",
        "region_ons_code",
        "actual_duration",
    ]

    cleaned_df = standardise_whitespace(duration_df, text_columns)

    # Add a month column for Parquet partitioning.
    cleaned_df = cleaned_df.withColumn(
        "month",
        F.trunc(F.col("appointment_date"), "month"),
    )

    invalid_dates = cleaned_df.filter(
        F.col("appointment_date").isNull()
    ).count()

    invalid_counts = cleaned_df.filter(
        F.col("count_of_appointments").isNull()
    ).count()

    assert invalid_dates == 0, (
        f"Found {invalid_dates:,} missing or invalid dates"
    )

    assert invalid_counts == 0, (
        f"Found {invalid_counts:,} missing appointment counts"
    )

    output_rows = cleaned_df.count()
    output_total = cleaned_df.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    print(f"Clean duration rows: {output_rows:,}")
    print(f"Clean duration appointment total: {output_total:,}")

    # Validate the required row count and total.
    assert raw_rows == output_rows == 137_793, (
        f"Expected 137,793 rows; raw={raw_rows:,}, "
        f"clean={output_rows:,}"
    )

    assert raw_total == output_total == 167_980_692, (
        f"Appointment total mismatch: raw={raw_total:,}, "
        f"clean={output_total:,}"
    )

    (
        cleaned_df
        .write
        .mode("overwrite")
        .partitionBy("month")
        .parquet(str(DURATION_OUTPUT_DIR))
    )

    print(f"Duration Parquet saved to: {DURATION_OUTPUT_DIR}")


def main():
    spark = create_spark_session()

    try:
        transform_regional(spark)
        transform_national_categories(spark)
        transform_duration(spark)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
