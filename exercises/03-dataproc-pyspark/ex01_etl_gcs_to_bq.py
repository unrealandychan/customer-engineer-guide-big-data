"""
Exercise 01 — PySpark ETL: Read from GCS, Transform, Write to BigQuery
------------------------------------------------------------------------
Goal:
    - Run a PySpark job locally (or on Dataproc)
    - Read Parquet/CSV data from GCS
    - Apply DataFrame transformations (filter, groupBy, window functions)
    - Write results to BigQuery using the Spark BigQuery connector

Interview relevance:
    "How would you submit a Spark job on Dataproc?"
    "How does Dataproc differ from Dataflow for batch ETL?"

Run locally (for testing):
    pip install pyspark
    python ex01_etl_gcs_to_bq.py

Submit to Dataproc:
    gcloud dataproc jobs submit pyspark ex01_etl_gcs_to_bq.py \
        --cluster=my-cluster \
        --region=us-central1 \
        --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar \
        -- --project=your-project-id --bucket=your-bucket --dataset=spark_exercises
"""

import argparse
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, FloatType, DateType
)


# ---------------------------------------------------------------------------
# Schema for the sample events dataset
# ---------------------------------------------------------------------------
EVENTS_SCHEMA = StructType([
    StructField("event_id",    StringType(),  nullable=False),
    StructField("event_date",  DateType(),    nullable=False),
    StructField("event_type",  StringType(),  nullable=True),
    StructField("country",     StringType(),  nullable=True),
    StructField("user_id",     StringType(),  nullable=True),
    StructField("amount",      FloatType(),   nullable=True),
])


def create_spark_session(project_id: str, temp_bucket: str) -> SparkSession:
    """
    Create a SparkSession configured for the BigQuery connector.
    On Dataproc, the connector is pre-installed.
    Locally, you need to add the JAR via .config("spark.jars", "...").
    """
    # TODO: Build SparkSession with BigQuery connector settings
    spark = (
        SparkSession.builder
        .appName("GCS-to-BigQuery ETL")
        .config("spark.sql.shuffle.partitions", "8")   # Reduce for small local jobs
        # BigQuery connector config (on Dataproc these are set via initialization actions)
        .config("temporaryGcsBucket", temp_bucket)     # Needed for BQ write via connector
        .getOrCreate()
    )
    spark.conf.set("parentProject", project_id)
    return spark


# ---------------------------------------------------------------------------
# EXERCISE 1a: Read CSV from GCS
# ---------------------------------------------------------------------------
def read_from_gcs(spark: SparkSession, gcs_path: str):
    """
    Read a CSV file from GCS into a Spark DataFrame.
    Equivalent of: spark.read.csv("gs://bucket/path/file.csv")
    """
    print(f"Reading from: {gcs_path}")

    # TODO: Read CSV with header and infer schema
    # spark.read.option("header", True).option("inferSchema", True).csv(gcs_path)
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(gcs_path)
    )
    print(f"Rows loaded: {df.count()}")
    df.printSchema()
    df.show(5, truncate=False)
    return df


# ---------------------------------------------------------------------------
# EXERCISE 1b: Transform — clean, enrich, aggregate
# ---------------------------------------------------------------------------
def transform(df):
    """
    Apply a series of DataFrame transformations:
    1. Filter out rows with null amounts
    2. Add a derived column: amount_usd (convert GBP rows at 1.27 rate)
    3. Aggregate: daily revenue by country and event_type
    4. Add a window function: rolling 7-day revenue per country
    """

    # Step 1: Filter nulls
    # TODO: df.filter(F.col("amount").isNotNull())
    df_clean = df.filter(F.col("amount").isNotNull())

    # Step 2: Add derived column
    # TODO: Use F.when(...).otherwise(...) to convert GBP → USD
    df_enriched = df_clean.withColumn(
        "amount_usd",
        F.when(F.col("country") == "GB", F.col("amount") * 1.27)
         .otherwise(F.col("amount"))
    )

    # Step 3: Aggregate daily revenue
    # TODO: groupBy event_date, country, event_type → agg SUM(amount_usd), COUNT(*)
    df_agg = (
        df_enriched
        .groupBy("event_date", "country", "event_type")
        .agg(
            F.sum("amount_usd").alias("revenue_usd"),
            F.count("*").alias("event_count"),
            F.countDistinct("user_id").alias("unique_users"),
        )
        .orderBy("event_date", "country")
    )

    # Step 4: Window function — 7-day rolling revenue per country
    # TODO: Define a window spec partitioned by country, ordered by event_date,
    #        with a rows between -6 preceding and current row
    window_spec = (
        Window
        .partitionBy("country")
        .orderBy("event_date")
        .rowsBetween(-6, Window.currentRow)
    )

    df_windowed = df_agg.withColumn(
        "rolling_7d_revenue",
        F.sum("revenue_usd").over(window_spec)
    )

    print("\nTransformed DataFrame (sample):")
    df_windowed.show(10, truncate=False)
    return df_windowed


# ---------------------------------------------------------------------------
# EXERCISE 1c: Write results to BigQuery
# ---------------------------------------------------------------------------
def write_to_bigquery(df, project_id: str, dataset: str, table: str) -> None:
    """
    Write the transformed DataFrame to a BigQuery table.
    Uses the Spark BigQuery connector (indirect write via GCS temp bucket).

    Write modes:
      overwrite  → WRITE_TRUNCATE (replaces table)
      append     → WRITE_APPEND
      errorifexists → WRITE_EMPTY
    """
    full_table = f"{project_id}.{dataset}.{table}"
    print(f"\nWriting to BigQuery: {full_table}")

    # TODO: Use df.write.format("bigquery") to write the DataFrame
    (
        df.write
        .format("bigquery")
        .option("table", full_table)
        .mode("overwrite")    # WRITE_TRUNCATE
        .save()
    )
    print(f"Write complete: {full_table}")


# ---------------------------------------------------------------------------
# EXERCISE 1d: Write results to Parquet on GCS (alternative sink)
# ---------------------------------------------------------------------------
def write_to_gcs_parquet(df, gcs_output_path: str) -> None:
    """
    Write DataFrame to GCS as Parquet — a common intermediate format.
    Parquet is columnar, compressed, and efficient for BigQuery external tables.
    """
    print(f"\nWriting Parquet to: {gcs_output_path}")
    # TODO: Use df.write.parquet(gcs_output_path, mode="overwrite")
    df.write.parquet(gcs_output_path, mode="overwrite")
    print(f"Parquet write complete: {gcs_output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="PySpark ETL: GCS → BigQuery")
    parser.add_argument("--project",   required=True, help="GCP project ID")
    parser.add_argument("--bucket",    required=True, help="GCS bucket (for temp and output)")
    parser.add_argument("--dataset",   default="spark_exercises", help="BigQuery dataset")
    parser.add_argument("--input",     default="exercises/events.csv", help="GCS input path")
    args = parser.parse_args()

    gcs_input  = f"gs://{args.bucket}/{args.input}"
    gcs_output = f"gs://{args.bucket}/output/daily_revenue_parquet"

    spark = create_spark_session(args.project, args.bucket)

    # Run the ETL pipeline
    raw_df       = read_from_gcs(spark, gcs_input)
    transformed  = transform(raw_df)
    write_to_gcs_parquet(transformed, gcs_output)
    write_to_bigquery(transformed, args.project, args.dataset, "daily_revenue")

    spark.stop()
    print("\nETL job complete.")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Add a data quality check: assert no null event_date rows exist after
#    the filter step. Raise an exception if data quality fails.
#
# 2. Replace the CSV read with a Parquet read. How does the schema handling change?
#
# 3. Modify the write_to_bigquery function to use partitionBy("event_date")
#    so the output BigQuery table is partitioned. What changes in the write call?
#
# 4. Add repartition(4) before writing. How does it affect the number of output
#    files in GCS when writing Parquet? Why does this matter for Dataproc cost?
