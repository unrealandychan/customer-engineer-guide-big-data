# Exercises — GCP Hands-On Practice

All exercises use real GCP APIs. Set up credentials first, then work through
categories in order of your priority.

---

## Prerequisites

```bash
# Authenticate
gcloud auth application-default login

# Set default project
gcloud config set project YOUR_PROJECT_ID
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

---

## Category Index

| # | Folder                   | Language     | GCP Service          | Difficulty |
|---|--------------------------|--------------|----------------------|------------|
| 1 | `01-bigquery-python/`    | Python       | BigQuery             | ⭐⭐         |
| 2 | `02-bigquery-go/`        | Go           | BigQuery             | ⭐⭐⭐        |
| 3 | `03-dataproc-pyspark/`   | PySpark      | Dataproc             | ⭐⭐⭐        |
| 4 | `04-pubsub-python/`      | Python       | Pub/Sub              | ⭐⭐         |
| 5 | `05-pubsub-go/`          | Go           | Pub/Sub              | ⭐⭐⭐        |
| 6 | `06-dataflow-beam-python/`| Python      | Dataflow / Beam      | ⭐⭐⭐⭐       |
| 7 | `07-terraform-gcp/`      | Terraform    | All services         | ⭐⭐⭐        |
| 8 | `08-gcs-python-go/`      | Python + Go  | Cloud Storage        | ⭐⭐         |

---

## Exercise Files

### 01 — BigQuery Python

| File                          | Topic                                         |
|-------------------------------|-----------------------------------------------|
| `ex01_run_query.py`           | Execute queries, Pandas DataFrame, job stats  |
| `ex02_parameterized_query.py` | Safe queries, ScalarQueryParameter            |
| `ex03_load_from_gcs.py`       | Load CSV/JSON from GCS into BigQuery          |
| `ex04_create_partitioned_table.py` | Partitioning, clustering, scan cost comparison |
| `ex05_window_functions.py`    | ROW_NUMBER, RANK, LAG/LEAD, QUALIFY, sessions |
| `ex06_schema_management.py`   | Create/evolve schemas, nested RECORD fields   |
| `ex07_streaming_insert.py`    | Streaming inserts (insert_rows_json)          |

### 02 — BigQuery Go

| File                     | Topic                                              |
|--------------------------|----------------------------------------------------|
| `ex01_run_query.go`      | Query execution, struct binding, job statistics    |
| `ex02_load_and_insert.go`| GCS load job, streaming insert, partitioned tables |

### 03 — Dataproc PySpark

| File                          | Topic                                            |
|-------------------------------|--------------------------------------------------|
| `ex01_etl_gcs_to_bq.py`       | ETL: GCS → transform → BigQuery / Parquet        |
| `ex02_structured_streaming.py` | Structured Streaming, tumbling windows, watermark|

### 04 — Pub/Sub Python

| File                        | Topic                                              |
|-----------------------------|----------------------------------------------------|
| `ex01_publish_subscribe.py` | Publish, sync pull, streaming pull, ack/nack       |

### 05 — Pub/Sub Go

| File                        | Topic                                              |
|-----------------------------|----------------------------------------------------|
| `ex01_publish_subscribe.go` | Concurrent publish with goroutines, Receive + Ack  |

### 06 — Dataflow / Beam (Python)

| File                       | Topic                                              |
|----------------------------|----------------------------------------------------|
| `ex01_beam_pipeline.py`    | Batch + streaming Beam pipelines → BigQuery        |
| `ex02_custom_transforms.py`| CombineFn, composite PTransforms, CoGroupByKey     |

### 07 — Terraform GCP

| Folder              | Resources provisioned                                   |
|---------------------|---------------------------------------------------------|
| `01-bigquery/`      | Dataset, partitioned table, IAM                         |
| `02-dataproc/`      | Cluster, autoscaling policy, preemptible workers        |
| `03-pubsub/`        | Topic, dead-letter subscription, IAM                    |
| `04-gcs/`           | Bucket, lifecycle rules, versioning, IAM                |
| `05-full-pipeline/` | End-to-end: GCS + BQ + Pub/Sub + Service Accounts + IAM |

### 08 — Cloud Storage (Python + Go)

| File                | Topic                                                     |
|---------------------|-----------------------------------------------------------|
| `ex01_gcs_python.py`| Upload, download, list, signed URLs, metadata (Python)    |
| `ex01_gcs_go.go`    | Same operations in Go                                     |

---

## Recommended Learning Path

### Path A — Python Focus (3 days)
1. `01-bigquery-python/ex01` → `ex02` → `ex04` → `ex05`
2. `04-pubsub-python/ex01`
3. `08-gcs-python-go/ex01_gcs_python.py`
4. `06-dataflow-beam-python/ex01_beam_pipeline.py`

### Path B — Go Focus (3 days)
1. `02-bigquery-go/ex01` → `ex02`
2. `05-pubsub-go/ex01`
3. `08-gcs-python-go/ex01_gcs_go.go`

### Path C — Infrastructure (2 days)
1. `07-terraform-gcp/01-bigquery/`
2. `07-terraform-gcp/03-pubsub/`
3. `07-terraform-gcp/05-full-pipeline/`

### Path D — Interview Blitz (1 day)
1. `01-bigquery-python/ex04` — partitioning + clustering (most interview-asked)
2. `01-bigquery-python/ex05` — window functions
3. `06-dataflow-beam-python/ex01` — Beam/Dataflow architecture
4. Read: `07-terraform-gcp/05-full-pipeline/main.tf` — understand the full picture
