"""
Exercise 02 — PySpark Structured Streaming (Simulated)
--------------------------------------------------------
Goal:
    - Understand Spark Structured Streaming concepts
    - Read from a streaming source (rate source for local testing, Pub/Sub in production)
    - Apply windowed aggregations with event-time
    - Write streaming output to a sink (console, GCS, or BigQuery)

Interview relevance:
    "How does Spark Structured Streaming compare to Dataflow?"
    "When would you use Dataproc Spark Streaming vs Dataflow?"

Run locally:
    pip install pyspark
    python ex02_structured_streaming.py

On Dataproc (with Pub/Sub connector):
    gcloud dataproc jobs submit pyspark ex02_structured_streaming.py \
        --cluster=my-cluster \
        --region=us-central1 \
        --packages=com.google.cloud.spark:spark-pubsub:0.1.0-beta
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, FloatType, TimestampType
)


# ---------------------------------------------------------------------------
# EXERCISE 2a: Local streaming with the built-in 'rate' source
# ---------------------------------------------------------------------------
def streaming_with_rate_source() -> None:
    """
    The 'rate' source generates rows at a fixed rate — great for local testing.
    Each row: timestamp (processing time), value (incrementing counter)

    This simulates an event stream without Pub/Sub or Kafka.
    """
    spark = (
        SparkSession.builder
        .appName("Structured Streaming — Rate Source")
        .master("local[2]")           # 2 local threads
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # TODO: Read from the rate source
    # spark.readStream.format("rate").option("rowsPerSecond", 10).load()
    stream_df = (
        spark.readStream
        .format("rate")
        .option("rowsPerSecond", 10)
        .load()
    )

    # 'value' is the row counter — simulate it as a 'user_id' bucket
    # Add derived columns to make it look like event data
    events_df = stream_df.select(
        F.col("timestamp").alias("event_time"),
        (F.col("value") % 20).cast("string").alias("user_id"),  # 20 simulated users
        F.when(F.col("value") % 3 == 0, "purchase")
         .when(F.col("value") % 3 == 1, "click")
         .otherwise("view").alias("action"),
        (F.rand() * 100).alias("amount"),
    )

    # ---------------------------------------------------------------------------
    # EXERCISE 2b: Tumbling window aggregation (event-time based)
    # ---------------------------------------------------------------------------
    # TODO: Apply a 10-second tumbling window on event_time
    # F.window("event_time", "10 seconds") creates a window column
    windowed_df = (
        events_df
        .withWatermark("event_time", "5 seconds")   # tolerate up to 5s late data
        .groupBy(
            F.window("event_time", "10 seconds"),   # tumbling 10-second window
            "action"
        )
        .agg(
            F.count("*").alias("event_count"),
            F.countDistinct("user_id").alias("unique_users"),
            F.sum("amount").alias("total_amount"),
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "action",
            "event_count",
            "unique_users",
            F.round("total_amount", 2).alias("total_amount"),
        )
    )

    # ---------------------------------------------------------------------------
    # EXERCISE 2c: Write to console sink (for local testing)
    # ---------------------------------------------------------------------------
    # TODO: Start the streaming query writing to console
    # .outputMode("update") — only show rows that changed in this micro-batch
    # .outputMode("complete") — show all rows (requires aggregation)
    query = (
        windowed_df.writeStream
        .outputMode("update")
        .format("console")
        .option("truncate", False)
        .option("numRows", 20)
        .trigger(processingTime="5 seconds")  # micro-batch every 5 seconds
        .start()
    )

    print("\n=== Structured Streaming started (runs for 30 seconds) ===")
    print("You should see windowed aggregations every 5 seconds.")
    print("Key concepts:")
    print("  - Watermark: tolerate events up to 5s late")
    print("  - Window: 10-second tumbling buckets")
    print("  - outputMode=update: only show changed rows per batch")
    print()

    # Run for 30 seconds then stop
    query.awaitTermination(timeout=30)
    spark.stop()
    print("\nStreaming query stopped.")


# ---------------------------------------------------------------------------
# EXERCISE 2d: Write to GCS (Parquet, checkpoint for fault tolerance)
# ---------------------------------------------------------------------------
def streaming_to_gcs(bucket: str) -> None:
    """
    In production, you'd write streaming output to GCS (Parquet files)
    or directly to BigQuery. This shows the pattern.

    Key production requirements:
      - Checkpoint location: for fault tolerance and exactly-once
      - Trigger interval: controls micro-batch frequency
    """
    spark = (
        SparkSession.builder
        .appName("Structured Streaming — GCS sink")
        .getOrCreate()
    )

    stream_df = spark.readStream.format("rate").option("rowsPerSecond", 5).load()
    output_df = stream_df.select(
        F.col("timestamp"),
        (F.col("value") % 10).alias("bucket"),
    )

    # TODO: Write to GCS with checkpoint
    query = (
        output_df.writeStream
        .format("parquet")
        .option("path", f"gs://{bucket}/streaming-output/")
        .option("checkpointLocation", f"gs://{bucket}/checkpoints/streaming-ex2/")
        .trigger(processingTime="30 seconds")
        .start()
    )

    # In production you'd call query.awaitTermination() (no timeout)
    # For exercise, just show the query object
    print(f"Streaming query started. Writing to gs://{bucket}/streaming-output/")
    print(f"Checkpoint at: gs://{bucket}/checkpoints/streaming-ex2/")
    print(f"Query ID: {query.id}")
    print(f"Query status: {query.status}")
    query.stop()
    spark.stop()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        streaming_to_gcs(sys.argv[1])
    else:
        streaming_with_rate_source()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Change the window from tumbling (10s) to sliding (10s window, 5s slide):
#    F.window("event_time", "10 seconds", "5 seconds")
#    How does the output change? Why do rows appear in multiple windows?
#
# 2. Add a second aggregation: session window per user_id
#    F.session_window("event_time", "30 seconds")
#    This creates a window per user that resets after 30s of inactivity.
#
# 3. Research: how would you connect this to a Pub/Sub source on GCP?
#    Use the spark-pubsub connector. What changes in the readStream section?
#
# 4. Dataproc vs Dataflow comparison exercise:
#    - This job runs on Dataproc (Spark cluster)
#    - Equivalent Dataflow job would use Apache Beam PubSubIO + Window transforms
#    - Key trade-off: Dataflow is serverless, Dataproc needs cluster management
#    Write a one-paragraph note comparing both for this use case.
