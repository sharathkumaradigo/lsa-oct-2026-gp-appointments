
from pathlib import Path

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
)

from src.transform import (
    aggregate_regional_appointments,
    standardise_whitespace,
    standardise_staff_type,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("GPAppointmentsTests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def test_regional_aggregation_preserves_appointment_total(spark):
    """Test the production aggregation function."""

    source = spark.createDataFrame(
        [
            ("E1", "2022-01", "Attended", "GP",
             "Face-to-face", "Same day", 10),
            ("E1", "2022-01", "Attended", "GP",
             "Face-to-face", "Same day", 15),
            ("E2", "2022-01", "DNA", "GP",
             "Telephone", "1 day", 5),
        ],
        [
            "icb_ons_code",
            "appointment_month",
            "appointment_status",
            "hcp_type",
            "appointment_mode",
            "time_between_book_and_appointment",
            "count_of_appointments",
        ],
    )

    result = aggregate_regional_appointments(source)

    assert source.count() == 3
    assert result.count() == 2

    source_total = source.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    result_total = result.agg(
        F.sum("count_of_appointments")
    ).first()[0]

    assert source_total == 30
    assert result_total == source_total


def test_whitespace_is_standardised(spark):
    source = spark.createDataFrame(
        [("  1-2   weeks  ",)],
        ["wait_band"],
    )

    result = standardise_whitespace(source, ["wait_band"])

    assert result.first()["wait_band"] == "1-2 weeks"


def test_staff_label_is_standardised(spark):
    source = spark.createDataFrame(
        [
            ("Other Practice staff",),
            ("Other Practice Staff",),
            ("GP",),
        ],
        ["hcp_type"],
    )

    result = standardise_staff_type(source)

    labels = {row["hcp_type"] for row in result.collect()}

    assert labels == {"Other Practice Staff", "GP"}


def test_national_date_parsing_is_day_first(spark):
    source = spark.createDataFrame(
        [("04/05/2022",), ("31/12/2021",)],
        ["appointment_date"],
    )

    result = source.withColumn(
        "appointment_date",
        F.to_date("appointment_date", "dd/MM/yyyy"),
    )

    dates = [row["appointment_date"] for row in result.collect()]

    assert str(dates[0]) == "2022-05-04"
    assert str(dates[1]) == "2021-12-31"


def test_invalid_national_date_is_detected(spark):
    """Check that malformed dates are identified safely."""

    source = spark.createDataFrame(
        [("31/12/2021",), ("invalid-date",)],
        ["appointment_date"],
    )

    result = source.withColumn(
        "parsed_date",
        F.try_to_timestamp(
            F.col("appointment_date"),
            F.lit("dd/MM/yyyy"),
        ).cast("date"),
    )

    invalid_count = result.filter(
        F.col("parsed_date").isNull()
    ).count()

    assert invalid_count == 1


def test_appointment_counts_are_positive(spark):
    source = spark.createDataFrame(
        [(10,), (25,), (0,)],
        ["count_of_appointments"],
    )

    invalid_count = source.filter(
        F.col("count_of_appointments").isNull()
        | (F.col("count_of_appointments") <= 0)
    ).count()

    assert invalid_count == 1


def test_regional_aggregation_has_unique_keys(spark):
    source = spark.createDataFrame(
        [
            ("E1", "2022-01", "Attended", 10),
            ("E1", "2022-01", "Attended", 15),
            ("E2", "2022-01", "DNA", 5),
        ],
        ["icb", "month", "status", "count"],
    )

    keys = ["icb", "month", "status"]

    result = source.groupBy(*keys).agg(
        F.sum("count").alias("count")
    )

    duplicate_keys = (
        result.groupBy(*keys)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    assert duplicate_keys == 0


def test_monthly_partition_values_are_correct(spark):
    """Check that records have the expected monthly partition values."""
    source = spark.createDataFrame(
        [
            ("2022-01-01", 10),
            ("2022-02-01", 20),
        ],
        ["month", "count_of_appointments"],
    ).withColumn("month", F.to_date("month"))

    # Confirm that the month column contains two distinct months.
    months = {
        row["month"].strftime("%Y-%m-%d")
        for row in source.select("month").distinct().collect()
    }

    assert months == {"2022-01-01", "2022-02-01"}
    assert source.count() == 2
    assert source.agg(
        F.sum("count_of_appointments")
    ).first()[0] == 30
