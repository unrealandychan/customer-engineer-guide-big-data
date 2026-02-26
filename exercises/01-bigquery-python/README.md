# Category 01 — BigQuery with Python

Practice the BigQuery Python client library. Each exercise builds on the previous one.

## Setup

```bash
pip install google-cloud-bigquery google-cloud-bigquery-storage pyarrow pandas db-dtypes
```

Set your project:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

## Exercises

| File | Topic | Difficulty |
|------|-------|-----------|
| `ex01_run_query.py` | Run a query and print results | 🟢 Beginner |
| `ex02_parameterized_query.py` | Safe parameterized queries | 🟢 Beginner |
| `ex03_load_from_gcs.py` | Load a CSV/JSON from GCS into a table | 🟡 Intermediate |
| `ex04_create_partitioned_table.py` | Create and insert into a partitioned + clustered table | 🟡 Intermediate |
| `ex05_window_functions.py` | Write window function queries | 🟡 Intermediate |
| `ex06_schema_management.py` | Create, update, and delete tables via the API | 🟡 Intermediate |
| `ex07_streaming_insert.py` | Stream rows into BigQuery using the insertAll API | 🔴 Advanced |
| `ex08_query_stats.py` | Inspect job metadata: bytes scanned, slot usage | 🔴 Advanced |

## Learning Goals

After completing all exercises you should be able to:
- Run queries programmatically and retrieve results as Pandas DataFrames
- Use parameterized queries to avoid SQL injection
- Create tables with partition and cluster configurations
- Load data from GCS into BigQuery
- Read query job metadata (bytes scanned, duration)
- Stream rows into BigQuery from a Python application
