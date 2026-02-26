# Lesson 6 — Optimization, Pricing & Operations

> The final lesson covers cost management, performance tuning, common failure modes, and the key decision between Dataproc, BigQuery, and Dataflow.

---

## Pricing — The Full Model

### Dataproc Charge Formula

```
Dataproc charge = $0.010 × number_of_vCPUs × hours_running
```

- Billed **per-second** with a **1-minute minimum**
- Applies to ALL nodes (master + all workers)
- **On top of** Compute Engine VM cost (separate billing line)

### Total Cost Breakdown

```
Total cluster cost = Dataproc charge
                   + Compute Engine VM cost (per instance)
                   + Standard Persistent Disk (per GB provisioned)
                   + Cloud Monitoring
                   + (optional) Cloud Storage egress
                   + (optional) BigQuery queries
```

### Worked Example

**Cluster:** 1 master (n1-standard-4) + 5 workers (n1-standard-4, 4 vCPUs each)
**Duration:** 2 hours

```
Total vCPUs = 1×4 + 5×4 = 24 vCPUs
Dataproc charge = $0.010 × 24 × 2 = $0.48

Compute Engine (n1-standard-4 = ~$0.19/hr per VM):
  = 6 VMs × $0.19 × 2 hrs = $2.28

Total = $0.48 + $2.28 = $2.76 for 2 hours
```

### Preemptible VM Savings Example

```
8 workers replaced with preemptible VMs (~80% cheaper):
  Regular:     8 × $0.19/hr × 8 hrs = $12.16 GCE cost
  Preemptible: 8 × $0.04/hr × 8 hrs =  $2.56 GCE cost
  Savings: $9.60 (79%)

Dataproc charge stays the same — $0.010/vCPU/hr regardless.
```

### Serverless for Apache Spark Pricing

Separate model — charged per **DCU (Dataproc Compute Unit)**:
```
Serverless charge = DCUs used × $0.054/DCU-hour
                  + Shuffle storage
```
Check https://cloud.google.com/dataproc-serverless/pricing for current rates.

---

## Cost Optimization Strategies

### 1. Ephemeral Clusters (biggest win)
```
Persistent cluster (24h/day):  100% of VM cost
Ephemeral (30 min/job × 4/day): ~8% of VM cost
Savings: ~92%
```
Rule: **Never run a Dataproc cluster with nothing to do.**

### 2. Preemptible Secondary Workers
```
20% primary + 80% preemptible → ~60-70% GCE cost reduction
```

### 3. Right-size the Cluster
- Start small; scale via autoscaling or manual resize
- Check YARN utilization in Cloud Monitoring — if CPU < 50%, you're over-provisioned

### 4. Use Parquet / ORC formats
- Columnar formats reduce data read → fewer vCPU hours → lower Dataproc charge

### 5. GCS Lifecycle Policies
- Archive old input data to Coldline/Archive storage
- GCS is cheap but Coldline ($0.004/GB/month) vs Standard ($0.020/GB/month) adds up

---

## Performance Tuning

### Problem 1: Data Skew

**Symptom:** Most tasks finish in 2 seconds, but one task runs for 30 minutes.
**Cause:** One partition has far more data than others (e.g., all records for user_id=NULL).

```python
# Diagnose: check partition sizes
df.rdd.mapPartitions(lambda iter: [sum(1 for _ in iter)]).collect()

# Fix 1: Salting — add random prefix to skewed key
import random
from pyspark.sql.functions import concat, lit

df = df.withColumn(
    "salted_key",
    concat(col("skewed_key"), lit("_"), (col("id") % 10).cast("string"))
)

# Fix 2: Filter out NULLs before groupBy, process separately
df_valid = df.filter(col("key").isNotNull())
df_null = df.filter(col("key").isNull())
result_valid = df_valid.groupBy("key").agg(...)
result_null = df_null.agg(...)  # aggregate separately
result = result_valid.union(result_null)
```

### Problem 2: Too Many Small Files

**Symptom:** Job is slow even though total data is small; Spark launches thousands of tiny tasks.
**Cause:** Source has millions of tiny files (e.g., one file per event from Pub/Sub).

```python
# Fix: Coalesce before writing, repartition at read time
df = spark.read.parquet("gs://my-bucket/raw/").repartition(200)

# Or coalesce output files
df.coalesce(10).write.parquet("gs://my-bucket/compacted/")
```

**Rule of thumb:** Target partition sizes of 128 MB–1 GB.

### Problem 3: Wrong Shuffle Partition Count

```python
# Default is 200 — too many for small data, too few for large data
# Tune based on: total_data_size_MB / 200 MB per partition
# Example: 400 GB of data → 400,000 MB / 200 = 2,000 partitions

spark.conf.set("spark.sql.shuffle.partitions", "2000")

# Or set at SparkSession creation
spark = SparkSession.builder \
    .config("spark.sql.shuffle.partitions", "2000") \
    .getOrCreate()
```

### Problem 4: Out of Memory (OOM)

**Symptoms:** `java.lang.OutOfMemoryError`, executor lost, job retries repeatedly.

```bash
# Fix 1: Increase executor memory
gcloud dataproc jobs submit pyspark my_job.py \
  --cluster=my-cluster \
  --properties=spark.executor.memory=8g,spark.driver.memory=4g

# Fix 2: Use larger machine type
gcloud dataproc clusters create my-cluster \
  --worker-machine-type=n1-highmem-8  # 8 vCPUs, 52 GB RAM

# Fix 3: Avoid .collect() on large DataFrames
# BAD:
data = df.collect()   # pulls EVERYTHING to driver

# GOOD:
df.write.parquet("gs://my-bucket/output/")  # write distributed
```

### Problem 5: Slow Joins

```python
# Fix 1: Broadcast small tables
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")

# Fix 2: Ensure join keys have same type
# Mismatched types cause full scan + cast
large_df = large_df.withColumn("user_id", col("user_id").cast("string"))
small_df = small_df.withColumn("user_id", col("user_id").cast("string"))
```

---

## Key Spark Configuration Reference

| Property | Default | When to change |
|----------|---------|----------------|
| `spark.sql.shuffle.partitions` | 200 | Change to `data_GB × 10` |
| `spark.executor.memory` | 1g | Increase if OOM errors |
| `spark.executor.cores` | 1 | Increase to 4-5 for CPU-bound jobs |
| `spark.driver.memory` | 1g | Increase if driver OOM (large collect) |
| `spark.memory.fraction` | 0.6 | Fraction of heap for execution + storage |
| `spark.dynamicAllocation.enabled` | false | Enable for variable workloads |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB | Increase to auto-broadcast larger tables |

---

## Dataproc vs BigQuery vs Dataflow — Decision Guide

| Scenario | Best Service | Reason |
|----------|-------------|--------|
| Ad-hoc SQL on large tables | **BigQuery** | Serverless SQL, no setup, fast |
| Scheduled SQL-based ETL | **BigQuery** (Scheduled Queries or dbt) | No cluster management |
| Migrate existing Spark/Hadoop code | **Dataproc** | Same API — zero code changes |
| ML training with Spark MLlib | **Dataproc** | Native Spark ML ecosystem |
| Complex multi-stage batch pipelines | **Dataproc** | Full Spark control |
| Real-time streaming (Apache Beam) | **Dataflow** | Managed Beam runner |
| Streaming with Kafka + Spark | **Dataproc** (Structured Streaming) | Native Spark + Kafka connectors |
| Fully serverless batch Spark | **Dataproc Serverless** | No cluster to manage |
| Already on Kubernetes | **Dataproc on GKE** | Reuse existing GKE infrastructure |

---

## Common Interview Answers

### "When would you choose Dataproc over BigQuery?"

> "If the customer has existing Spark or Hadoop code they want to run on GCP without rewriting it, Dataproc is the right choice — it's the same Spark API, just managed. BigQuery is better when the workload is SQL-based and you want a fully serverless experience with no cluster management. For ML training at scale with custom code, Dataproc with Spark MLlib is also the better fit."

### "How would you handle a Dataproc job that's too expensive?"

> "Three levers: First, use the ephemeral cluster pattern — create, run, delete — so you only pay during job execution. Second, add preemptible secondary workers at 60-90% lower GCE cost. Third, right-size the cluster — check YARN utilization in Cloud Monitoring and reduce machine type or worker count if it's below 50%."

### "A Dataproc job is slow. How do you diagnose it?"

> "Check the Spark UI (accessible via History Server on port 18080 or through Cloud Console). Look at the stage timeline — find the longest stage. If one task is much slower than others, it's data skew. If there are thousands of tiny tasks, it's a small files problem. Check GC time — if > 20% of task time is GC, increase executor memory. Look at shuffle read/write size — large shuffle usually means a join or groupBy that can be optimized with broadcast or pre-aggregation."

---

## Quick Reference Card

```
CLUSTER MANAGEMENT
─────────────────────────────────────────────────────
Create:   gcloud dataproc clusters create NAME --region=REGION --num-workers=N
Delete:   gcloud dataproc clusters delete NAME --region=REGION
Scale:    gcloud dataproc clusters update NAME --num-workers=N

JOB SUBMISSION
─────────────────────────────────────────────────────
PySpark:  gcloud dataproc jobs submit pyspark gs://BUCKET/job.py --cluster=NAME
Wait:     gcloud dataproc jobs wait JOB_ID --region=REGION
Kill:     gcloud dataproc jobs kill JOB_ID --region=REGION

PRICING FORMULA
─────────────────────────────────────────────────────
$0.010 × vCPUs × hours   (+ Compute Engine VM cost)
Billed per-second, 1-minute minimum

COST TIPS
─────────────────────────────────────────────────────
1. Ephemeral clusters → biggest savings
2. Preemptible workers → 60-91% cheaper GCE
3. Parquet format → read less data
4. Autoscaling → right-size automatically

PERFORMANCE TIPS
─────────────────────────────────────────────────────
Slow join         → broadcast small table
Data skew         → salting or split key
OOM               → increase executor.memory, avoid .collect()
Too many tasks    → repartition(200) on read
Slow aggregation  → check shuffle.partitions setting
```

---

## Final Design Challenge

**Scenario:** A customer runs 50 nightly Spark batch jobs on a 20-node on-premises Hadoop cluster. Each job takes 15–45 minutes. They want to migrate to GCP with minimal rewrite. Their budget is tight.

**Design a Dataproc architecture that:**
1. Minimizes cost
2. Requires no code changes
3. Handles job failures gracefully
4. Scales automatically

<details><summary>Suggested Architecture</summary>

1. **Keep Spark code unchanged** — upload to GCS, submit via `gcloud dataproc jobs submit pyspark`
2. **Ephemeral clusters per job** — create cluster, run job, delete cluster → pay only for 15-45 min not 24h
3. **Preemptible secondary workers** — 4 primary + 16 preemptible per cluster → ~65% GCE cost reduction
4. **Cloud Composer (Airflow)** — orchestrate all 50 jobs with DAGs; `trigger_rule="all_done"` ensures cluster deletion even on failure
5. **Cloud Storage for all data** — no HDFS dependency, data persists between clusters
6. **Autoscaling policy** — set min=4, max=20 workers; let YARN pending memory drive scaling
7. **Cloud Monitoring alerts** — alert on job failure, high shuffle spill, or excessive GC time

**Estimated savings vs persistent 20-node cluster:** 70–85% compute cost reduction.

</details>

---

## Course Complete! 🎉

| Lesson | Covered |
|--------|---------|
| 1 — What is Dataproc? | ✅ |
| 2 — How Spark Works | ✅ |
| 3 — Cluster Architecture | ✅ |
| 4 — Managing Clusters | ✅ |
| 5 — Writing PySpark Jobs | ✅ |
| 6 — Optimization, Pricing & Operations | ✅ |

**Next steps:**
- Run the exercises in `exercises/03-dataproc-pyspark/`
- Deep-dive into `docs/12-dataproc-from-scratch.md` for Spark internals
- Practice the design challenge above out loud
