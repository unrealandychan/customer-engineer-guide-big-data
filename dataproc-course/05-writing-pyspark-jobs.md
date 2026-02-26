# Lesson 5 — Writing PySpark Jobs

> This lesson covers the practical code patterns you will use every day with Dataproc.

---

## SparkSession — The Entry Point

Every PySpark job starts with a `SparkSession`.

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("My ETL Job") \
    .getOrCreate()

# Access the underlying SparkContext if needed
sc = spark.sparkContext
```

On Dataproc, you don't need to configure the master URL — Dataproc handles YARN connection automatically.

---

## Reading Data

### From Cloud Storage (GCS)

```python
# Parquet (recommended — columnar, efficient)
df = spark.read.parquet("gs://my-bucket/data/events/")

# CSV
df = spark.read.option("header", "true") \
               .option("inferSchema", "true") \
               .csv("gs://my-bucket/data/users.csv")

# JSON
df = spark.read.json("gs://my-bucket/data/logs/")

# ORC
df = spark.read.orc("gs://my-bucket/data/warehouse/")

# With explicit schema (faster than inferSchema — recommended for production)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("created_at", TimestampType(), True),
    StructField("value", IntegerType(), True),
])

df = spark.read.schema(schema).parquet("gs://my-bucket/data/events/")
```

### From BigQuery

```python
# Requires spark-bigquery-connector (pre-installed on Dataproc)
df = spark.read \
    .format("bigquery") \
    .option("table", "my_project.my_dataset.my_table") \
    .load()

# Filter pushdown — only reads matching rows from BQ (fast)
df = spark.read \
    .format("bigquery") \
    .option("table", "my_project.dataset.events") \
    .option("filter", "event_date >= '2024-01-01'") \
    .load()
```

---

## Writing Data

### To Cloud Storage

```python
# Write Parquet (partitioned by date — recommended)
df.write \
  .mode("overwrite") \
  .partitionBy("year", "month") \
  .parquet("gs://my-bucket/output/events/")

# Append mode
df.write \
  .mode("append") \
  .parquet("gs://my-bucket/output/events/")

# CSV output
df.write \
  .mode("overwrite") \
  .option("header", "true") \
  .csv("gs://my-bucket/output/report.csv")
```

### To BigQuery

```python
# Write to BigQuery
df.write \
  .format("bigquery") \
  .option("table", "my_project.dataset.output_table") \
  .option("temporaryGcsBucket", "my-temp-bucket") \
  .mode("overwrite") \
  .save()
```

---

## Core Transformations

### Selecting and Filtering

```python
from pyspark.sql.functions import col, lit, when

# Select columns
df_selected = df.select("user_id", "event_type", "value")

# Filter rows
df_filtered = df.filter(col("event_type") == "purchase")
df_filtered = df.filter((col("value") > 100) & (col("event_type") == "purchase"))

# Add a column
df = df.withColumn("value_usd", col("value") / 100)

# Add a constant column
df = df.withColumn("source", lit("dataproc_job"))

# Conditional column
df = df.withColumn(
    "tier",
    when(col("value") > 1000, "premium")
    .when(col("value") > 100, "standard")
    .otherwise("basic")
)

# Rename
df = df.withColumnRenamed("user_id", "userId")

# Drop
df = df.drop("internal_id")
```

### Aggregations

```python
from pyspark.sql.functions import count, sum, avg, max, min, countDistinct

# Simple groupBy
result = df.groupBy("event_type") \
           .agg(
               count("*").alias("total_events"),
               sum("value").alias("total_value"),
               avg("value").alias("avg_value"),
               countDistinct("user_id").alias("unique_users")
           )

# Multiple groupBy keys
result = df.groupBy("event_type", "country") \
           .agg(count("*").alias("events"))

# Pivot (cross-tabulation)
pivot = df.groupBy("user_id") \
          .pivot("event_type") \
          .agg(count("*")) \
          .fillna(0)
```

### Joins

```python
# Inner join (default)
result = orders.join(users, on="user_id", how="inner")

# Left join
result = orders.join(users, on="user_id", how="left")

# Join on multiple keys
result = orders.join(users,
    on=["user_id", "region"],
    how="inner"
)

# Join with different column names
result = orders.join(
    users,
    orders.customer_id == users.user_id,
    how="left"
).drop(users.user_id)
```

### Broadcast Join — Eliminate Shuffle for Small Tables

```python
from pyspark.sql.functions import broadcast

# If 'lookup_table' is small (< a few hundred MB), broadcast it
result = large_df.join(
    broadcast(small_lookup_df),
    on="product_id",
    how="left"
)
```

A broadcast join sends the small table to every executor, avoiding a full shuffle. This is the single most impactful optimization for joins with a small table.

---

## Window Functions

```python
from pyspark.sql.functions import rank, dense_rank, row_number, lag, lead, sum as spark_sum
from pyspark.sql.window import Window

# Define a window
w = Window.partitionBy("user_id").orderBy("created_at")

# Rank within each user
df = df.withColumn("event_rank", rank().over(w))

# Previous event value (lag)
df = df.withColumn("prev_value", lag("value", 1).over(w))

# Running total per user
df = df.withColumn("running_total", spark_sum("value").over(
    Window.partitionBy("user_id").orderBy("created_at").rowsBetween(
        Window.unboundedPreceding, Window.currentRow
    )
))

# 7-day moving average
df = df.withColumn("ma7", avg("value").over(
    Window.partitionBy("user_id").orderBy("event_date_unix").rangeBetween(
        -6 * 86400, 0  # 6 days before through current row
    )
))
```

---

## Spark SQL

You can run SQL directly on DataFrames by registering them as temporary views.

```python
# Register as SQL view
df.createOrReplaceTempView("events")
users.createOrReplaceTempView("users")

# Run SQL
result = spark.sql("""
    SELECT
        u.country,
        e.event_type,
        COUNT(*) as total,
        SUM(e.value) as revenue
    FROM events e
    JOIN users u ON e.user_id = u.user_id
    WHERE e.created_at >= '2024-01-01'
    GROUP BY u.country, e.event_type
    ORDER BY revenue DESC
""")

result.show(20)
```

---

## Submitting Jobs to Dataproc

### Option 1: gcloud CLI

```bash
# Basic submission
gcloud dataproc jobs submit pyspark gs://my-bucket/jobs/etl.py \
  --cluster=my-cluster \
  --region=us-central1

# With job arguments (after --)
gcloud dataproc jobs submit pyspark gs://my-bucket/jobs/etl.py \
  --cluster=my-cluster \
  --region=us-central1 \
  -- --input=gs://my-bucket/input/ --output=gs://my-bucket/output/

# With Spark properties
gcloud dataproc jobs submit pyspark gs://my-bucket/jobs/etl.py \
  --cluster=my-cluster \
  --region=us-central1 \
  --properties=spark.sql.shuffle.partitions=400,spark.executor.memory=4g

# With additional Python files or packages
gcloud dataproc jobs submit pyspark gs://my-bucket/jobs/etl.py \
  --cluster=my-cluster \
  --region=us-central1 \
  --py-files=gs://my-bucket/libs/utils.py \
  --files=gs://my-bucket/config/settings.json
```

### Option 2: spark-submit (from master node)

```bash
# SSH into master node first
gcloud compute ssh CLUSTER_NAME-m --zone=us-central1-a

# Then run spark-submit
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 10 \
  --executor-cores 4 \
  --executor-memory 8g \
  --driver-memory 4g \
  --conf spark.sql.shuffle.partitions=400 \
  gs://my-bucket/jobs/etl.py \
  --input gs://my-bucket/input/ \
  --output gs://my-bucket/output/
```

---

## Complete ETL Job Example

```python
"""
daily_etl.py — Complete PySpark ETL job for Dataproc
"""
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, sum as spark_sum, count

def main(input_path: str, output_path: str, date: str):
    spark = SparkSession.builder \
        .appName(f"Daily ETL — {date}") \
        .getOrCreate()

    # --- EXTRACT ---
    events = spark.read \
        .option("inferSchema", "true") \
        .parquet(f"{input_path}/date={date}/")

    users = spark.read \
        .format("bigquery") \
        .option("table", "my_project.users.dim_users") \
        .load()

    # --- TRANSFORM ---
    enriched = events.join(users, on="user_id", how="left")

    daily_summary = enriched \
        .filter(col("event_type") == "purchase") \
        .groupBy("country", "product_id") \
        .agg(
            count("*").alias("total_orders"),
            spark_sum("value").alias("gross_revenue")
        )

    # --- LOAD ---
    daily_summary.write \
        .format("bigquery") \
        .option("table", "my_project.reporting.daily_summary") \
        .option("temporaryGcsBucket", "my-temp-bucket") \
        .mode("append") \
        .save()

    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    main(args.input, args.output, args.date)
```

---

## Practice Q&A

**Q1: How do you avoid a full shuffle when joining a small table with a large table?**
<details><summary>Answer</summary>
Use a broadcast join: `large_df.join(broadcast(small_df), on="key")`. The small table is sent to every executor so no network shuffle is needed.
</details>

**Q2: What is the difference between `mode("overwrite")` and `mode("append")` when writing?**
<details><summary>Answer</summary>
`overwrite` deletes all existing data in the target location before writing. `append` adds new files without deleting existing ones.
</details>

**Q3: How do you pass arguments to a PySpark job submitted via gcloud?**
<details><summary>Answer</summary>
Add `--` after the script path, then list arguments: `gcloud dataproc jobs submit pyspark my_job.py --cluster=... -- --date=2024-01-01`
</details>

**Q4: Why should you define a schema explicitly instead of using `inferSchema`?**
<details><summary>Answer</summary>
`inferSchema` reads the entire dataset to infer types — slow for large files. An explicit schema avoids this extra read pass and prevents type mismatches in production.
</details>

**Q5: What does `createOrReplaceTempView` do?**
<details><summary>Answer</summary>
It registers a DataFrame as a temporary SQL view in the SparkSession, allowing you to query it with `spark.sql("SELECT ... FROM view_name")`.
</details>
