# Lesson 1 — What is Dataflow & Apache Beam?

> **Official docs:**
> - https://cloud.google.com/dataflow/docs/overview
> - https://beam.apache.org/documentation/programming-guide/

---

## The Problem They Solve

Imagine you need to process 10 million events per second from user devices, clean them, enrich them with user data, and write results to BigQuery — in real time. Or you need to process 100 TB of historical logs overnight in a batch job.

Both problems share the same challenge: **moving and transforming large amounts of data reliably and at scale**, whether the data is bounded (batch) or unbounded (streaming).

Traditionally, batch and streaming required completely different codebases and engines. Beam and Dataflow unify them.

---

## Apache Beam vs Google Cloud Dataflow

These two things are often confused. They are related but different:

```
┌─────────────────────────────────────────────────────────────────┐
│                      APACHE BEAM                                │
│                                                                 │
│  Open-source SDK — YOU write pipelines using Beam's API         │
│  Available in Java, Python, Go, TypeScript                      │
│  Defines WHAT your pipeline does                                │
│                                                                 │
│  "Write once, run anywhere"                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ your pipeline runs ON a runner
                    ┌───────────┼───────────────┐
                    ↓           ↓               ↓
             ┌──────────┐  ┌──────────┐  ┌──────────┐
             │Dataflow  │  │  Flink   │  │  Spark   │
             │(GCP)     │  │(on-prem) │  │(on-prem) │
             └──────────┘  └──────────┘  └──────────┘
```

| | Apache Beam | Google Cloud Dataflow |
|--|------------|----------------------|
| **What it is** | Open-source SDK + programming model | Fully managed runner for Beam on GCP |
| **You write** | Pipeline code (Python/Java/Go) | Nothing extra — just set `--runner=DataflowRunner` |
| **Who runs it** | The runner you choose | Google-managed fleet of worker VMs |
| **Analogy** | SQL query you write | The database engine that executes it |

**Summary:** Beam = the language. Dataflow = the managed engine that executes Beam pipelines on GCP.

---

## What Dataflow Offers (Official Advantages)

### 1. Fully Managed
- Google manages all worker VMs — you never SSH into machines
- VMs are allocated when a job starts, deleted when it finishes
- No cluster to keep running between jobs

### 2. Automatically Scalable
- Dataflow **autoscales** worker count based on data volume
- **Horizontal Autoscaling**: adds/removes VMs mid-job
- **Dynamic Work Rebalancing**: moves work between VMs to prevent stragglers

### 3. Unified Batch + Streaming
- The **same pipeline code** handles both batch files and live streams
- Switch with a single flag: `--runner=DataflowRunner`
- Streaming pipelines support **exactly-once** processing by default

### 4. Portable (via Apache Beam)
- Write once → run on Dataflow today, Flink tomorrow — same code
- No vendor lock-in at the pipeline logic level

### 5. Observable
- Real-time job graph in Cloud Console
- Each pipeline stage shows throughput, latency, and worker utilization
- Integrated with Cloud Logging and Cloud Monitoring

---

## Dataflow Use Cases (from official docs)

| Use case | Example |
|----------|---------|
| **Data movement / ETL** | Read Pub/Sub messages → transform → write to BigQuery |
| **Streaming analytics** | Count page views per minute in real time |
| **Batch processing** | Process a month of log files overnight |
| **Real-time ML** | Score ML models on streaming events |
| **Log processing at scale** | Ingest and analyze 1B log lines/day |
| **BI dashboard backend** | Supply near-real-time aggregates to Looker |

---

## How Dataflow Executes a Pipeline

```
1. You write a Beam pipeline (Python/Java/Go)
2. You run it with DataflowRunner
          ↓
3. Beam SDK serializes pipeline graph
4. SDK uploads code + dependencies to GCS
5. Dataflow service creates a job
          ↓
6. Dataflow allocates worker VMs
7. Workers execute pipeline stages in parallel
8. Dataflow autoscales workers as needed
9. Job completes → VMs are automatically deleted
```

A typical architecture:

```
Pub/Sub  →  Dataflow  →  BigQuery
  (source)    (transform)    (sink)
                 ↕
           Cloud Storage
           (staging, temp files)
```

---

## Beam Runners

When you run a Beam pipeline, you choose a **runner** — the engine that executes it:

| Runner | Where it runs | Best for |
|--------|-------------|---------|
| **DataflowRunner** | Google Cloud | Production at scale, managed |
| **DirectRunner** | Your local machine | Development and unit testing |
| **FlinkRunner** | Apache Flink cluster | On-premises or Kubernetes |
| **SparkRunner** | Apache Spark cluster | On-premises Spark environments |

```python
# Local development — DirectRunner
python my_pipeline.py

# Production on Dataflow
python my_pipeline.py \
  --runner=DataflowRunner \
  --project=my-project \
  --region=us-central1 \
  --temp_location=gs://my-bucket/temp/
```

---

## Dataflow Templates

**Templates** are pre-packaged Dataflow pipelines that anyone can run without writing code.

- **Google-provided templates:** Pub/Sub → BigQuery, GCS → BigQuery, Kafka → BigQuery, etc.
- **Custom templates:** You package your own pipeline as a template; others deploy it

```bash
# Run a Google-provided template: Pub/Sub to BigQuery
gcloud dataflow jobs run my-streaming-job \
  --gcs-location=gs://dataflow-templates/latest/PubSub_to_BigQuery \
  --region=us-central1 \
  --parameters=\
inputTopic=projects/my-project/topics/my-topic,\
outputTableSpec=my-project:my_dataset.my_table
```

---

## When to Use Dataflow vs Alternatives

| Scenario | Service | Reason |
|----------|---------|--------|
| SQL analytics on large tables | **BigQuery** | Serverless SQL, no pipeline code needed |
| Migrate existing Spark jobs | **Dataproc** | Same Spark API, zero rewrite |
| Real-time streaming with transformations | **Dataflow** | Managed Beam, exactly-once, autoscaling |
| Event ingestion + enrichment + sink | **Dataflow** | Pub/Sub → Dataflow → BigQuery is the canonical pattern |
| Complex ETL with fan-out, merging, windowing | **Dataflow** | Beam's transform model handles these natively |

---

## Practice Q&A

**Q1: What is the relationship between Apache Beam and Google Cloud Dataflow?**
<details><summary>Answer</summary>
Apache Beam is an open-source SDK for writing data pipelines (the programming model). Dataflow is Google's fully managed service that executes Beam pipelines on GCP. You write Beam code; Dataflow runs it.
</details>

**Q2: What is a Beam runner?**
<details><summary>Answer</summary>
A runner is the execution engine that takes a Beam pipeline definition and runs it on a specific platform. Examples: DataflowRunner (GCP), DirectRunner (local), FlinkRunner, SparkRunner.
</details>

**Q3: Name three advantages of Dataflow from the official docs.**
<details><summary>Answer</summary>
Managed (no infrastructure management), scalable (autoscaling + dynamic rebalancing), portable (Beam pipelines can run on other runners), unified batch + streaming, observable (Cloud Console monitoring).
</details>

**Q4: A customer wants to move Pub/Sub messages to BigQuery in real time with exactly-once guarantees. Which GCP service?**
<details><summary>Answer</summary>
Dataflow. The canonical GCP pattern is Pub/Sub → Dataflow → BigQuery. Dataflow provides exactly-once processing for streaming pipelines by default.
</details>

**Q5: What is a Dataflow Template?**
<details><summary>Answer</summary>
A pre-packaged Dataflow pipeline that can be deployed by anyone without writing code. Google provides templates for common scenarios (Pub/Sub → BigQuery, GCS → BigQuery). You can also create custom templates.
</details>
