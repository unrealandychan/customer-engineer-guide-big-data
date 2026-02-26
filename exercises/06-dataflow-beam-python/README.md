# Category 06 — Apache Beam / Dataflow (Python)

## What is Apache Beam?

Apache Beam is a **unified programming model** for batch and streaming data pipelines.
You write your pipeline once; it runs on any runner:

| Runner          | Where it runs              | Use case                        |
|-----------------|----------------------------|---------------------------------|
| `DirectRunner`  | Local machine (your laptop)| Dev, unit testing               |
| `DataflowRunner`| Google Cloud Dataflow      | Production — serverless, managed|
| `SparkRunner`   | Apache Spark / Dataproc    | Existing Spark infra            |
| `FlinkRunner`   | Apache Flink               | Low-latency streaming           |

**Beam vs Dataflow (interview one-liner):**
> Beam is the programming model (the SDK). Dataflow is Google's fully-managed, autoscaling runner for Beam — you pay per vCPU-hour and workers scale automatically.

---

## Key Concepts

| Term               | Definition                                             |
|--------------------|--------------------------------------------------------|
| `Pipeline`         | The complete DAG of transforms + data                  |
| `PCollection`      | Distributed, immutable dataset (batch or streaming)    |
| `PTransform`       | An operation applied to one or more PCollections       |
| `DoFn`             | User-defined function inside `ParDo` (the most common transform)|
| `CombineFn`        | Partial-aggregation function (efficient `GroupByKey`)  |
| `Window`           | Groups streaming elements by time for aggregation      |
| `Watermark`        | Tracks how far behind event-time processing is lagging |
| `Side Input`       | Read-only extra data injected into a transform         |
| `CoGroupByKey`     | Join two keyed PCollections (full outer join)          |

---

## Exercises

| File                       | Topic                                          |
|----------------------------|------------------------------------------------|
| `ex01_beam_pipeline.py`    | Batch CSV→BigQuery + Streaming Pub/Sub→BigQuery|
| `ex02_custom_transforms.py`| Composite PTransforms, CombineFn, CoGroupByKey |

---

## Setup

```bash
# Install Beam with GCP extras
pip install "apache-beam[gcp]"

# Set credentials
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

---

## Run Locally (DirectRunner)

```bash
# Batch pipeline (reads from a local or GCS CSV)
python ex01_beam_pipeline.py \
    --runner DirectRunner \
    --input gs://your-bucket/events.csv \
    --project your-project-id

# Custom transforms demo
python ex02_custom_transforms.py --runner DirectRunner
```

## Deploy to Dataflow

```bash
python ex01_beam_pipeline.py \
    --runner DataflowRunner \
    --project your-project-id \
    --region us-central1 \
    --temp_location gs://your-bucket/temp/ \
    --staging_location gs://your-bucket/staging/ \
    --input gs://your-bucket/events.csv
```

## Streaming on Dataflow

```bash
python ex01_beam_pipeline.py \
    --runner DataflowRunner \
    --project your-project-id \
    --region us-central1 \
    --temp_location gs://your-bucket/temp/ \
    --staging_location gs://your-bucket/staging/ \
    --subscription projects/your-project-id/subscriptions/your-sub
```

---

## Window Types Cheat Sheet

```
Fixed (Tumbling)   |--1min--|--1min--|--1min--|
Sliding            |--2min--|
                      |--2min--|
                         |--2min--|
Session            |--activity--|gap|--activity--|
Global             |-------entire pipeline-------|
```

```python
from apache_beam.transforms.window import FixedWindows, SlidingWindows, Sessions, GlobalWindows

beam.WindowInto(FixedWindows(60))            # 1-minute tumbling
beam.WindowInto(SlidingWindows(120, 60))     # 2-min window, slide every 1 min
beam.WindowInto(Sessions(gap_size=300))      # Session: 5-min inactivity gap
beam.WindowInto(GlobalWindows())             # Single global window (default)
```

---

## Dataflow vs Dataproc Decision Framework

| Factor                  | Use Dataflow               | Use Dataproc               |
|-------------------------|----------------------------|----------------------------|
| Programming model       | Apache Beam                | Spark / Hadoop ecosystem   |
| Operational overhead    | Zero (serverless)          | Cluster management needed  |
| Existing codebase       | New pipelines              | Existing Spark/Hive jobs   |
| Streaming               | Native, auto-scaled        | Spark Structured Streaming |
| Startup time            | ~3 min (job graph compile) | ~90 sec (cluster boot)     |
| Cost model              | Per vCPU-sec, autoscaled   | Per cluster-hour           |
| ML library integration  | Limited                    | MLlib, pandas on Spark     |
