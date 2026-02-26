# Category 03 — Dataproc + PySpark

## What you will practice

| File                          | Topics                                                      |
|-------------------------------|-------------------------------------------------------------|
| `ex01_etl_gcs_to_bq.py`       | SparkSession, CSV read from GCS, transforms, write to BQ    |
| `ex02_structured_streaming.py` | Rate source, tumbling windows, watermarks, GCS sink         |

---

## Setup

```bash
# Option A: Run locally with PySpark installed
pip install pyspark
export GOOGLE_CLOUD_PROJECT=your-project-id

# Option B: Submit to Dataproc (recommended)
gcloud dataproc jobs submit pyspark ex01_etl_gcs_to_bq.py \
    --cluster=your-cluster \
    --region=us-central1 \
    --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar \
    -- \
    --input_path=gs://your-bucket/events.csv \
    --output_table=your-project:dataset.events \
    --temp_bucket=your-temp-bucket
```

---

## Key PySpark Patterns

```python
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window

spark = SparkSession.builder \
    .config("temporaryGcsBucket", TEMP_BUCKET) \
    .getOrCreate()

df = spark.read.option("header", True).csv("gs://bucket/file.csv")
df = df.withColumn("amount", F.col("amount").cast("double"))
df.write.format("bigquery").option("table", "project:ds.table").mode("overwrite").save()
```

---

## Dataproc vs Dataflow Decision Framework

| Factor           | Dataproc (Spark)              | Dataflow (Beam)              |
|------------------|-------------------------------|------------------------------|
| Existing code    | Existing Spark/Hive jobs      | New pipelines                |
| Operations       | Cluster management needed     | Serverless — zero ops        |
| Streaming        | Structured Streaming          | Native, auto-scaled          |
| ML integration   | MLlib, pandas on Spark        | Limited                      |
| Startup time     | ~90 sec (cluster boot)        | ~3 min (job graph compile)   |
