# 🌊 Streaming Analytics — Frameworks & GCP Patterns

> Reference guide for streaming concepts, frameworks, and how to talk about them in your interview.

---

## Core Streaming Concepts (Framework-Agnostic)

These apply across all tools — know them well.

| Concept | Definition |
|---------|-----------|
| **Event time** | When the event actually happened (e.g., user click timestamp) |
| **Processing time** | When the system processes the event (usually later) |
| **Watermark** | Threshold: "events older than X are considered late" |
| **Tumbling window** | Fixed, non-overlapping buckets (e.g., every 5 minutes) |
| **Sliding window** | Overlapping (e.g., last 10 min, updated every 1 min) |
| **Session window** | Per-user gaps define windows (e.g., idle >30 min = new session) |
| **Exactly-once** | Every event is processed exactly once, even with retries/failures |
| **At-least-once** | Events might be processed more than once — simpler but requires idempotent sinks |
| **State** | Aggregation memory across events: running counts, recent N events, current balance |

---

## 1. Streaming with BigQuery (GCP Native Pattern)

BigQuery is not a streaming engine — it is a **warehouse that accepts streaming input** and serves fast SQL on near-real-time tables.

### Typical Architecture

```
App / Service
     ↓
  Pub/Sub  (event ingestion, durable, scalable)
     ↓
  Dataflow (Beam streaming pipeline)
   - Parse JSON
   - Enrich (geo, device, user profile)
   - Window and aggregate
   - Write to BigQuery
     ↓
  BigQuery  (partitioned + clustered table)
     ↓
  Looker / BI (near-real-time dashboards)
```

### Ingestion Options into BigQuery

| Method | Latency | Best For |
|--------|---------|---------|
| Streaming inserts (API) | Seconds | Simple, low-moderate volume |
| Pub/Sub → Dataflow → BQ | < 1–2 min | Complex transforms, high volume |
| Storage Write API | Seconds | High throughput with exactly-once |
| Batch load from GCS | Minutes to hours | Cost-efficient for non-urgent data |

### Pre-Sales Pitch

> "For streaming analytics on GCP, the most common pattern is Pub/Sub for ingestion, Dataflow for streaming transforms and enrichment, and BigQuery as the serving layer for dashboards and ML. This gives sub-minute freshness with standard SQL on top — and no infrastructure to manage."

---

## 2. Streaming with Apache Spark (Structured Streaming)

Spark's streaming API runs on **Dataproc** in GCP context.

### How It Works

- Model: treats the stream as an **unbounded DataFrame**
- Implementation: micro-batches (e.g., every 1–5 seconds) or continuous processing
- Define: Source → Transformations → Window → Sink
- State: stored in a state store on GCS (checkpoints for fault tolerance)
- Guarantees: exactly-once when configured with idempotent sinks

### Example Mental Model

```
Source: Kafka/Pub/Sub topic "clicks"
  ↓
Spark Structured Streaming:
  - Parse JSON + add event timestamp
  - Windowed count: COUNT(*) per user_id per 5-min window
  - Sink: BigQuery (via connector) or Parquet on GCS
```

### When to Recommend Spark Streaming on Dataproc

- Customer already has significant Spark code / team skills
- Need to reuse existing Spark libraries (MLlib, custom UDFs)
- Batch and streaming workloads can share the same code
- Prefer micro-batch semantics

---

## 3. Streaming with Apache Flink

Flink is a **true streaming engine** (not micro-batch). It's the most powerful option for complex event-time processing.

### Key Differentiators vs Spark

| Aspect | Spark Structured Streaming | Apache Flink |
|--------|---------------------------|-------------|
| Architecture | Micro-batch (default) | True streaming |
| Event-time handling | Good | Excellent (core design) |
| State management | Good | Very advanced |
| Latency | Sub-second to seconds | Sub-second |
| Ecosystem | Huge (Spark SQL, ML, etc.) | Growing |
| GCP managed option | Dataproc | Not natively managed — use Dataflow instead |

### On GCP

- Flink is not natively managed on GCP
- **Dataflow (Beam)** covers the same use cases in a fully managed way
- Position: "If you're looking at Flink for advanced event-time streaming, Dataflow gives you the same capabilities as a fully managed service — you don't manage clusters."

---

## 4. Apache Beam & Dataflow (GCP's Native Choice)

### What Beam Is

- A **unified programming model** for batch and streaming pipelines
- Write once, run on multiple backends (Dataflow, Flink, Spark)
- Core abstractions: `PCollection` (distributed dataset), `PTransform` (transform), `Pipeline` (DAG)

### What Dataflow Is

- Google Cloud's **managed runner** for Beam pipelines
- Fully serverless: no cluster sizing, auto-scales, handles failures
- Strong event-time semantics, exactly-once, watermarks — built in

### Why It Matters for Your Interview

| Scenario | What to Say |
|---------|------------|
| Customer builds new streaming pipelines | "Dataflow/Beam is the serverless, cloud-native choice — no clusters, strong guarantees" |
| Customer mentions Flink | "Dataflow covers the same use cases as a managed service — you get event-time, exactly-once, and no cluster ops" |
| Customer has existing Spark | "Start with Dataproc. For new streaming, consider Dataflow for the managed experience" |
| "What's the difference between Dataflow and Dataproc?" | See comparison table below |

### Dataproc vs Dataflow — The Key Comparison

| Dimension | Dataproc | Dataflow |
|-----------|---------|---------|
| Underlying engine | Apache Spark / Hadoop | Apache Beam |
| Cluster management | You manage (with autoscaling) | Fully serverless |
| Best for | Existing Spark workloads, custom libs | New cloud-native batch/stream pipelines |
| Streaming | Spark Structured Streaming | Beam windowing, watermarks, exactly-once |
| Operational overhead | Low (managed) | Minimal (serverless) |
| Migration path | Lift-and-shift from on-prem Hadoop | New pipelines, greenfield |

---

## 5. Other Frameworks — One-Liners for the Interview

| Framework | What It Is | GCP Mapping |
|-----------|-----------|------------|
| Kafka Streams | Stream processing library embedded in Kafka — no separate cluster | No direct GCP equivalent; Dataflow for similar use cases |
| ksqlDB | SQL on top of Kafka Streams | No direct GCP equivalent |
| Apache Kafka | Distributed event log (message broker) | Pub/Sub (managed) or Managed Kafka on GCP |
| Apache Flink | True streaming engine, advanced event-time | Dataflow (Beam) as managed equivalent |
| Apache Airflow | Workflow orchestration (DAGs, schedules) | Cloud Composer (managed Airflow) |
| dbt | SQL-based data transformation in warehouses | Works natively with BigQuery |

---

## 6. Choosing the Right Streaming Approach (Interview Script)

When asked *"How would you do streaming analytics for X?"*, walk through:

**Step 1 — Ingestion:**
> "Events come from apps or devices into Pub/Sub — or Kafka if they already use it."

**Step 2 — Processing (choose and justify):**

- **Dataflow (Beam):** *"For robust, low-latency, event-time, exactly-once processing. Fully managed — the easiest operational story on GCP."*
- **Spark Structured Streaming on Dataproc:** *"If they have significant Spark skills and code they want to reuse. Micro-batch semantics."*
- **Kafka Streams:** *"For lightweight processing tightly coupled to Kafka — no separate cluster."*

**Step 3 — Storage & serving:**
> "Land results in BigQuery for analytical queries and dashboards. For low-latency live lookups in applications, consider Bigtable or Firestore."

**Step 4 — Analytics:**
> "Dashboards on BigQuery via Looker. Alerts based on threshold breaches. ML scoring in the Dataflow pipeline via Vertex AI."

### Sample Interview Answer (60 seconds)

> "On GCP, for streaming analytics I'd land events in Pub/Sub, then use Dataflow for continuous processing and enrichment — because it's serverless, handles event-time and exactly-once semantics automatically. Results go into a partitioned BigQuery table for near-real-time dashboards.
>
> If the customer already has a significant Spark codebase, we could use Spark Structured Streaming on Dataproc instead, still landing aggregates in BigQuery. For the most demanding low-latency event-time processing, Dataflow or Apache Flink are the right fit — and on GCP, Dataflow is the fully managed version of that capability."

---

## 7. AWS → GCP Streaming Stack Translation

| AWS | GCP |
|-----|-----|
| Kinesis Data Streams | Pub/Sub |
| Kinesis Data Firehose | Pub/Sub + Dataflow → BigQuery |
| Kinesis Data Analytics | Dataflow (Beam) |
| MSK (Managed Kafka) | Pub/Sub or Managed Kafka on GCP |
| AWS Glue Streaming | Dataflow or Dataproc Spark Streaming |
| Redshift Streaming Ingestion | BigQuery Streaming inserts / Storage Write API |
