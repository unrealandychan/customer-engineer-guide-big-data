# Lesson 6 — Dataflow Operations and Best Practices

> **Official docs:**
> - https://cloud.google.com/dataflow/docs/monitor-jobs
> - https://cloud.google.com/dataflow/docs/guides/troubleshooting-your-pipeline

---

## Monitoring Dataflow Jobs

### The Dataflow Monitoring UI

Navigate to **Cloud Console → Dataflow → Jobs** to see all jobs.

Each job shows:
- **Job graph**: visual DAG of all pipeline stages; each node = one transform step
- **Stage metrics**: throughput (elements/sec), wall time per stage, bytes processed
- **Worker information**: number of workers, machine type, autoscaling events
- **Logs**: stackdriver logs per job, filterable by worker/severity

```
How to read the job graph:
─────────────────────────────────────────────────────────────
[Read Pub/Sub] → [Parse JSON] → [Window] → [Group] → [Write BQ]
     ↑                 ↑                      ↑
  throughput        latency               bottleneck?
 10K msgs/sec      2ms/element           ← look here if slow
─────────────────────────────────────────────────────────────
```

**Spotting bottlenecks:**
- The slowest stage has the highest "wall time"
- A stage with many workers but still slow → likely data skew
- A stage with one worker processing everything → key distribution issue

### Cloud Monitoring and Logging

Dataflow integrates with Cloud Monitoring for custom alerts:

```bash
# View job logs
gcloud dataflow jobs show JOB_ID --region=us-central1

# Stream logs in real time
gcloud logging read "resource.type=dataflow_step AND resource.labels.job_id=JOB_ID" \
  --limit 100 \
  --format=json
```

---

## Custom Metrics

Beyond built-in monitoring, add custom metrics to your pipeline:

```python
import apache_beam as beam

class ProcessOrderFn(beam.DoFn):
    def __init__(self):
        # Counters: track counts
        self.valid_orders = beam.metrics.Metrics.counter('pipeline', 'valid_orders')
        self.invalid_orders = beam.metrics.Metrics.counter('pipeline', 'invalid_orders')
        # Distributions: track value distributions
        self.order_amounts = beam.metrics.Metrics.distribution('pipeline', 'order_amounts')

    def process(self, element):
        try:
            amount = float(element['amount'])
            if amount > 0:
                self.valid_orders.inc()
                self.order_amounts.update(int(amount))
                yield element
            else:
                self.invalid_orders.inc()
        except (ValueError, KeyError):
            self.invalid_orders.inc()
```

Metrics appear in the Dataflow UI under **"Custom Counters"** and in Cloud Monitoring.

---

## Autoscaling and Worker Configuration

### How Autoscaling Works

Dataflow autoscaling adjusts worker count based on:
- **Throughput**: how many elements are being processed per second
- **Backlog**: for streaming, how much unprocessed data has accumulated in Pub/Sub
- **Worker utilization**: if workers are idle or CPU-bound

```
Job start: 5 workers
Data spike → Dataflow adds workers (up to max_num_workers)
Data slows → Dataflow removes workers
Job end → all workers deleted
```

### Worker Configuration Options

```python
from apache_beam.options.pipeline_options import WorkerOptions

worker_opts = options.view_as(WorkerOptions)
worker_opts.num_workers = 5             # Initial worker count
worker_opts.max_num_workers = 50        # Maximum autoscaling ceiling
worker_opts.machine_type = 'n1-standard-4'  # VM type (4 vCPU, 15GB RAM)
worker_opts.disk_size_gb = 50           # Persistent disk per worker
```

### Preemptible Workers (Cost Optimization)

Preemptible VMs cost ~80% less but can be terminated at any time by GCP. Beam handles restarts gracefully.

```python
worker_opts.use_preemptible = True
```

> **Use for:** Batch jobs where occasional restarts are acceptable.
> **Avoid for:** Streaming jobs or time-critical batch work.

---

## Cost Optimization

### 1. Use Streaming Engine (streaming jobs)
Moves windowing and shuffle computation off worker VMs to Google's managed backend. Reduces worker memory/disk requirements significantly.

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --enable_streaming_engine
```

### 2. Use Dataflow Shuffle (batch jobs)
Like Streaming Engine but for batch — offloads shuffle operations.

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --experiments=shuffle_mode=service
```

### 3. At-Least-Once Mode (streaming)
Trade exactly-once guarantees for lower cost and latency. Data is processed at-least-once (may see duplicates downstream).

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --at_least_once
```

### 4. Right-Size Workers

| Workload | Recommended |
|----------|-------------|
| CPU-heavy (ML inference) | `n1-standard-8` or `c2` |
| Memory-heavy (large side inputs) | `n1-highmem-4` |
| I/O-heavy (file reads/writes) | Smaller VMs, more of them |
| General ETL | `n1-standard-4` (default) |

### 5. Minimize GroupByKey and Shuffles

Every `GroupByKey` triggers a network shuffle — the most expensive operation. Prefer `CombinePerKey` which uses combiner lifting to pre-aggregate before shuffle.

---

## Common Issues and Fixes

### Issue 1: Out of Memory (OOM)
**Symptom:** Workers die with `java.lang.OutOfMemoryError` or `MemoryError`
**Causes:** Side inputs too large, large windows accumulating too much state
**Fix:**
```python
# Use a larger machine type
worker_opts.machine_type = 'n1-highmem-8'

# Or reduce side input size — don't load an entire table as a side input
# Use BigQuery joins or smaller lookup tables instead
```

### Issue 2: Data Skew
**Symptom:** 1 worker is at 100% CPU while others are idle; GroupByKey stage is slow
**Cause:** One key has vastly more data than others (e.g., all events have `user_id='unknown'`)
**Fix:**
```python
# Add a random salt to distribute hot keys
import random

def add_salt(element, num_buckets=10):
    key, value = element
    salted_key = f'{key}_{random.randint(0, num_buckets - 1)}'
    return (salted_key, value)

# Two-phase aggregation
salted = kv | 'Salt' >> beam.Map(add_salt)
partial = salted | 'Partial sum' >> beam.CombinePerKey(sum)
# Then strip salt and re-aggregate
```

### Issue 3: Slow Streaming Pipeline
**Symptom:** Pub/Sub backlog keeps growing; pipeline can't keep up
**Fixes:**
- Enable Streaming Engine
- Increase `max_num_workers`
- Profile the bottleneck stage in the UI; optimize the slow transform
- Use at-least-once mode if idempotent

### Issue 4: Pipeline Stuck (No Progress)
**Symptom:** Job shows as running but metrics show 0 throughput
**Causes:** Deadlock in custom code, infinite retry loop, watermark not advancing
**Fix:**
```bash
# Check worker logs for errors
gcloud logging read "resource.type=dataflow_step AND severity>=ERROR"

# Cancel and restart with fewer workers to isolate the issue
gcloud dataflow jobs cancel JOB_ID --region=us-central1
```

---

## Security

### IAM Roles

| Role | Who needs it |
|------|-------------|
| `roles/dataflow.admin` | Engineers who submit and manage jobs |
| `roles/dataflow.worker` | The Dataflow worker service account |
| `roles/bigquery.dataEditor` | Worker SA — to write to BigQuery |
| `roles/pubsub.subscriber` | Worker SA — to read from Pub/Sub |
| `roles/storage.objectAdmin` | Worker SA — to read/write GCS |

The **Dataflow worker service account** is a special service account that the worker VMs run as. By default it's the Compute Engine default SA — for production, use a dedicated SA with least-privilege permissions.

### Network Configuration

```bash
# Run pipeline in a specific VPC network (for private data)
python my_pipeline.py \
  --runner=DataflowRunner \
  --network=my-vpc-network \
  --subnetwork=regions/us-central1/subnetworks/my-subnet \
  --no_use_public_ips  # disable public IPs on workers
```

### Customer-Managed Encryption Keys (CMEK)

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --dataflow_kms_key=projects/my-project/locations/us/keyRings/my-ring/cryptoKeys/my-key
```

---

## Dataflow vs Dataproc vs BigQuery — Final Decision Guide

Use this when a customer asks which service to use for data processing:

| Question | Dataflow | Dataproc | BigQuery |
|----------|----------|----------|----------|
| **Primary model** | Beam pipelines (batch + streaming) | Spark/Hadoop jobs | SQL queries |
| **Use if** | You need streaming ETL OR want unified batch+stream code | You have existing Spark/Hadoop code to migrate | Your data is already in BQ and needs SQL analytics |
| **Streaming?** | ✅ First-class | ⚠️ Yes (Spark Streaming) but more ops overhead | ⚠️ Limited (BQ subscriptions) |
| **Infrastructure** | Fully managed (no cluster) | Managed cluster (you size it) | Fully serverless |
| **Language** | Java, Python, Go (Beam SDK) | Python (PySpark), Scala, Java | SQL |
| **Learning curve** | Medium (Beam concepts) | Low (same as Spark) | Low (SQL) |
| **Pricing** | Per vCPU-hour + Streaming units | Per node-hour (cluster runs even when idle) | Per TB scanned |
| **Cold start** | ~2-5 min per job | ~90 sec cluster start | Seconds |

**Decision shortcuts:**
- "Real-time streaming from Pub/Sub → BigQuery" → **Dataflow**
- "Migrate our Spark cluster from on-prem" → **Dataproc**
- "Ad-hoc analysis on petabyte table" → **BigQuery**
- "Complex ETL with joins, fan-outs, windowed aggregations" → **Dataflow**
- "Train an ML model on big data" → **Dataproc** (Spark MLlib) or **Vertex AI**

---

## 30-Second Interview Answers

**"What is Dataflow and when would you use it?"**
> Dataflow is Google Cloud's fully managed service for running Apache Beam pipelines. It handles all infrastructure — worker VMs, autoscaling, and fault tolerance. I'd recommend it when a customer needs to process both batch and streaming data with the same codebase, or when they're building real-time ETL pipelines from Pub/Sub into BigQuery with exactly-once guarantees.

**"How is Dataflow different from Dataproc?"**
> Both process large data sets, but they're different tools. Dataproc runs Spark and Hadoop — ideal when a customer has existing Spark code or engineers with Spark expertise. Dataflow runs Apache Beam pipelines — better for streaming, more fully managed, and you write once and run on multiple backends. Dataproc requires cluster management; Dataflow has no cluster to manage.

**"What does 'exactly-once processing' mean in Dataflow?"**
> It means each event is processed exactly once and produces exactly one result, even if the system retries due to failures. Dataflow achieves this through idempotent writes and checkpointing. It's the default for streaming jobs. Customers who can tolerate duplicates can opt for at-least-once mode for lower cost and latency.

---

## Quick Reference Card

```
PIPELINE SKELETON:
─────────────────
with beam.Pipeline(options=options) as p:
    (p | 'Read'      >> beam.io.ReadFromPubSub(topic=TOPIC)
       | 'Parse'     >> beam.Map(parse_fn)
       | 'Window'    >> beam.WindowInto(FixedWindows(60))
       | 'Aggregate' >> beam.CombinePerKey(sum)
       | 'Write'     >> beam.io.WriteToBigQuery(TABLE, schema=SCHEMA))

KEY FLAGS:
─────────
--runner=DataflowRunner
--project, --region
--temp_location=gs://bucket/temp
--staging_location=gs://bucket/staging
--streaming (for streaming jobs)
--max_num_workers=N
--requirements_file=requirements.txt
--enable_streaming_engine
--experiments=shuffle_mode=service  (batch shuffle)
--at_least_once (streaming, lower cost)
--no_use_public_ips (VPC private)

CORE TRANSFORMS:
────────────────
beam.Map(fn)             → 1-to-1 transform
beam.FlatMap(fn)         → 1-to-many transform
beam.Filter(fn)          → keep if fn returns True
beam.ParDo(MyDoFn())     → full control (yield 0-N elements)
beam.CombinePerKey(fn)   → aggregate by key (use over GroupByKey)
beam.GroupByKey()        → group all values per key (shuffle)
beam.CoGroupByKey()      → join two PCollections
beam.Flatten()           → merge multiple PCollections
beam.Partition(fn, N)    → split into N PCollections

WINDOW TYPES:
─────────────
FixedWindows(duration_secs)          → non-overlapping buckets
SlidingWindows(size, period)         → overlapping (rolling avg)
Sessions(gap_size)                   → activity-gap based
GlobalWindows()                      → all data = one window
```

---

## Practice Q&A

**Q1: How does Dataflow autoscaling work in streaming mode?**
<details><summary>Answer</summary>
Dataflow monitors the Pub/Sub backlog (unprocessed messages) and worker throughput. If the backlog grows, it adds workers (up to max_num_workers). If backlog shrinks and workers are underutilized, it removes them. This happens dynamically during the job without restarting.
</details>

**Q2: What is data skew and how do you fix it in a Beam pipeline?**
<details><summary>Answer</summary>
Data skew is when one key has far more data than others, causing one worker to be overloaded while others are idle. Fix by salting keys — add a random suffix to distribute hot keys across multiple sub-buckets, do a two-phase aggregation (partial per salt, then final with salt stripped).
</details>

**Q3: A customer wants their Dataflow workers to not have public IPs. How?**
<details><summary>Answer</summary>
Add `--no_use_public_ips` to the pipeline flags, and configure a VPC with Private Google Access enabled. Workers communicate with GCP APIs via internal routes. Also specify `--network` and `--subnetwork` to run in the customer's VPC.
</details>

**Q4: When should you use Streaming Engine?**
<details><summary>Answer</summary>
Always for streaming jobs. Streaming Engine moves windowing state and shuffle off worker VMs to Google's backend. This reduces worker memory requirements (and thus cost), improves autoscaling responsiveness, and is the recommended mode for all streaming Dataflow jobs.
</details>

**Q5: A prospect says "We already use Spark on-prem, should we move to Dataflow or Dataproc on GCP?"**
<details><summary>Answer</summary>
For existing Spark jobs, Dataproc is the faster migration path — same Spark API, zero code changes, just point to GCP resources. Dataflow would require rewriting pipelines in Beam. I'd recommend Dataproc to get them to GCP quickly, then evaluate Dataflow for new streaming use cases or if they want fully managed (no cluster) operations.
</details>
