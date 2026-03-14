# Dataproc From Scratch — A Complete Tutorial

> **Who this is for:** Someone who has never used Dataproc (or even Hadoop/Spark) and needs to understand what it is, why it exists, how it works internally, and how to use it.  
> **Goal:** After reading this, you can explain Dataproc in a whiteboard session and justify architecture decisions.

---

## Chapter 1: What Problem Does Dataproc Solve?

### The world before managed Spark

Imagine you have 10 TB of server logs and you need to:
1. Parse each line
2. Join them with a user database (500 GB)
3. Compute per-user session statistics
4. Write the results to a data warehouse

A single machine with a database can't hold 10 TB in memory and process it efficiently. You need to distribute the work across many machines.

**Apache Hadoop** solved this in 2006 — it let you run code across a cluster of cheap commodity servers. **Apache Spark** improved on it in 2014 — same distributed processing, but 100x faster by doing most work in memory instead of writing to disk.

**The problem: running these systems yourself is hard**

| Pain point | Reality |
|-----------|---------|
| Cluster setup | Days to weeks of configuration |
| Software versions | Dependency conflicts between Hadoop, Spark, Hive, YARN |
| Hardware | You need to buy and rack physical servers |
| Scaling | You provision peak capacity and pay for it 24/7 |
| Patching/upgrades | Your team does this manually |
| Failures | You manage node replacement, data replication |

**Dataproc is Google's answer:** Give Google all of that complexity. You get a Hadoop/Spark cluster in 90 seconds, run your job, and tear it down. You pay only for the time the cluster exists.

### Dataproc in one sentence

> Dataproc is Google Cloud's fully managed Apache Hadoop, Spark, Hive, and Flink service — the GCP equivalent of AWS EMR — that lets you run distributed data processing jobs without managing any cluster infrastructure.

---

## Chapter 2: How Distributed Processing Works

Before understanding Dataproc, you need to understand what runs ON Dataproc.

### The MapReduce model (the original idea)

MapReduce, invented at Google and published in 2004, is the foundational model for distributed data processing. Even though Spark has mostly replaced it, understanding MapReduce makes everything else click.

**The word count example:**

Suppose you have 1 TB of text files and you want to count how many times each word appears.

**Step 1: Map (split and transform)**
```
Machine 1 reads chunk:  "the quick brown fox"
  → emits: (the,1) (quick,1) (brown,1) (fox,1)

Machine 2 reads chunk:  "the lazy fox"
  → emits: (the,1) (lazy,1) (fox,1)

Machine 3 reads chunk:  "quick brown dog"
  → emits: (quick,1) (brown,1) (dog,1)
```

**Step 2: Shuffle (group by key)**
```
All (the, 1) pairs go to the same reducer
All (fox, 1) pairs go to the same reducer
All (quick, 1) pairs go to the same reducer
... etc.
```

**Step 3: Reduce (aggregate)**
```
Reducer for "the":    [1, 1] → 2
Reducer for "fox":    [1, 1] → 2
Reducer for "quick":  [1, 1] → 2
Reducer for "brown":  [1, 1] → 2
Reducer for "lazy":   [1]   → 1
Reducer for "dog":    [1]   → 1
```

The key insight: the work is **embarrassingly parallel**. 1,000 machines can each process 1/1000th of the data simultaneously.

### The Spark improvement

MapReduce wrote intermediate results to disk between every step, making multi-step jobs very slow. **Spark** keeps data in memory across steps.

The core abstraction in Spark is the **RDD (Resilient Distributed Dataset)** — and later **DataFrame** (the modern high-level API).

```
MapReduce job with 5 steps:
  Read → disk → Map → disk → Shuffle → disk → Reduce → disk → Write
  Disk I/O: 4 times per record

Spark job with 5 steps:
  Read → [in memory pipeline] → Write
  Disk I/O: 1 time per record (only read and final write)
```

Result: Spark is typically 10-100x faster than MapReduce for iterative workloads.

---

## Chapter 3: Spark Architecture — How It Actually Works

### The cluster topology

```
┌─────────────────────────────────────────────────────────────┐
│                    SPARK CLUSTER                            │
│                                                             │
│  ┌───────────────┐          ┌──────────────────────────┐   │
│  │  Driver Node  │          │     Worker Nodes          │   │
│  │               │          │                          │   │
│  │  SparkContext │◄────────►│  Executor 1  Executor 2  │   │
│  │  DAGScheduler │          │  [Task][Task] [Task][Task]│  │
│  │  TaskScheduler│          │                          │   │
│  │               │          │  Executor 3  Executor 4  │   │
│  └───────────────┘          │  [Task][Task] [Task][Task]│  │
│                              └──────────────────────────┘   │
│                                                             │
│  Resource Manager (YARN): allocates memory/CPU to executors │
└─────────────────────────────────────────────────────────────┘
```

**Driver Node:**  
The "brain" of your Spark application. Your code runs here. It:
- Analyses your code and builds a DAG (execution plan)
- Breaks the DAG into stages and tasks
- Assigns tasks to executors
- Collects results

**Worker Nodes:**  
The "muscle" — they do the actual computation. Each worker runs one or more **executors**.

**Executor:**  
A JVM process on a worker node. Each executor runs multiple **tasks** in parallel (threads) and holds data in memory (cache).

**Task:**  
The smallest unit of work. Each task processes one **partition** of data.

### RDDs and DataFrames — what is a "distributed dataset"?

When you load a 10 TB file into Spark, it's not loaded onto one machine. It's split into **partitions** — chunks of data, each assigned to one task on one executor.

```
10 TB file → 10,000 partitions of ~1 GB each

Partition 1 → Task 1 on Executor 1 (Worker A)
Partition 2 → Task 2 on Executor 1 (Worker A)
Partition 3 → Task 1 on Executor 2 (Worker B)
...
Partition 10000 → Task 2 on Executor 5000 (Worker 5000)
```

An **RDD** is just a metadata object that describes this collection of partitions and the lineage of transformations applied to it. The actual data lives distributed across the executors.

A **DataFrame** (the modern API) is an RDD with a schema (named typed columns), similar to a SQL table. Most Spark code today uses DataFrames, not raw RDDs.

### Transformations and actions

Spark operations are either **transformations** (lazy — define the plan) or **actions** (trigger execution).

**Transformations (lazy — nothing happens yet):**
```python
df = spark.read.parquet("gs://my-bucket/data/")   # transformation
filtered = df.filter(df.country == "DE")            # transformation
grouped = filtered.groupBy("campaign").sum("amount")# transformation
```

**Actions (trigger execution now):**
```python
grouped.show()         # action → Spark now executes all transformations
grouped.count()        # action
grouped.write.parquet("gs://output/")  # action
```

This laziness is intentional — Spark can optimise the entire plan before executing it.

### The DAG and stages

When you call an action, Spark's **DAGScheduler** analyses all the transformations and builds a DAG (Directed Acyclic Graph).

```
read parquet
    ↓
filter country='DE'
    ↓
groupBy campaign       ← SHUFFLE BOUNDARY (data must be redistributed)
    ↓
sum amount
    ↓
write parquet

Stage 1: read + filter (embarrassingly parallel, no shuffle needed)
Stage 2: groupBy + sum (requires data redistribution — all DE records must group by campaign)
```

**Shuffle** is the expensive operation — data moves between executors across the network. This is why:
- `groupBy`, `join`, `distinct`, `orderBy` create shuffle boundaries (expensive)
- `filter`, `select`, `withColumn` don't shuffle (cheap)

### YARN — the resource manager on Dataproc

On a Dataproc cluster, **YARN (Yet Another Resource Negotiator)** manages how CPU and memory are allocated to Spark executors across worker nodes.

```
Your spark-submit command
    ↓
YARN ApplicationMaster (negotiates resources)
    ↓
YARN allocates containers on worker nodes
    ↓
Spark Executors start inside those containers
    ↓
Tasks run inside executors
```

Think of YARN as the operating system scheduler for the cluster. It ensures multiple jobs can share the cluster fairly, and no single job starves others.

---

## Chapter 4: Dataproc Cluster Architecture

### How Dataproc maps to Spark's architecture

```
Dataproc Cluster
├── Master Node (1 or 3 for HA)
│   ├── YARN ResourceManager        ← manages resource allocation
│   ├── HDFS NameNode               ← manages filesystem metadata (if using HDFS)
│   ├── Spark Driver (for submitted jobs)
│   └── Hive Metastore (optional)
│
└── Worker Nodes (2 to thousands)
    ├── YARN NodeManager            ← reports resources, runs containers
    ├── HDFS DataNode               ← stores data blocks (if using HDFS)
    └── Spark Executors             ← actually run your tasks
```

**Important: on Dataproc, you don't use HDFS**

On-premise Hadoop stores data ON the cluster nodes in HDFS. This forces you to keep the cluster running permanently to access the data.

**On Dataproc, data lives in Cloud Storage (GCS).** The cluster is just compute — stateless compute that you spin up and tear down. Your data persists in GCS regardless of whether the cluster exists.

```
On-premise Hadoop:   [Data in HDFS] = [Cluster nodes] → cluster must stay alive
Dataproc:            [Data in GCS]  ≠ [Cluster nodes] → cluster can die, data is safe
```

This is the single biggest architectural difference and the enabler of ephemeral clusters.

### Cluster types

**Standard cluster:** Master + workers. Default configuration for batch jobs.

```
Master (n2-standard-4):  4 vCPUs, 16 GB RAM  → runs YARN RM, HDFS NN
Workers (n2-standard-4 × 4): each 4 vCPUs, 16 GB RAM → run tasks
Total: 16 vCPUs, 64 GB RAM for compute
```

**High-Availability cluster:** 3 masters instead of 1. If the primary master fails, another takes over automatically. Use for production workloads.

**Single node cluster:** 1 machine only. For development, testing, and small datasets.

**Dataproc Serverless Spark:** No cluster at all. You submit your PySpark script, Google runs it on infrastructure it manages, you pay per slot-second. Best for simple jobs where you don't want to think about cluster sizing.

---

## Chapter 5: The Ephemeral Cluster Pattern

This is the most important operational pattern in Dataproc.

### The old way (always-on clusters)

```
Monday:    Cluster running (8 jobs)     ← you pay
Tuesday:   Cluster running (8 jobs)     ← you pay
Wednesday: Cluster running (8 jobs)     ← you pay
Thursday:  Cluster running (3 jobs)     ← you pay (25% utilization)
Friday:    Cluster running (2 jobs)     ← you pay (12% utilization)
Saturday:  Cluster running (0 jobs)     ← you pay (0% utilization)
Sunday:    Cluster running (0 jobs)     ← you pay (0% utilization)

Monthly cost: 24 hours × 30 days × VM cost = full price
Average utilization: ~40%
```

### The ephemeral way (on-demand clusters)

```
Monday 09:00:  Cluster created    (90 seconds)
Monday 09:01:  Job 1 starts
Monday 11:00:  Job 1 ends
Monday 11:00:  Cluster deleted

Monday 14:00:  Cluster created    (90 seconds)
Monday 14:01:  Job 2 starts
Monday 15:30:  Job 2 ends
Monday 15:30:  Cluster deleted

Monthly cost: sum of actual job runtime × VM cost
Average utilization: ~95%
```

**The savings: typically 50-70% compared to always-on clusters.**

### How to orchestrate ephemeral clusters

Use **Cloud Composer (Apache Airflow)** to automate the lifecycle:

```python
# Airflow DAG that creates a cluster, runs a job, deletes it
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator,
)

create = DataprocCreateClusterOperator(
    task_id="create_cluster",
    cluster_name="etl-{{ ds_nodash }}",
    num_workers=4,
    region="us-central1",
)

run_job = DataprocSubmitJobOperator(
    task_id="run_etl",
    job={
        "pyspark_job": {"main_python_file_uri": "gs://my-bucket/etl.py"}
    },
)

delete = DataprocDeleteClusterOperator(
    task_id="delete_cluster",
    cluster_name="etl-{{ ds_nodash }}",
    trigger_rule="all_done",  # delete even if job failed
)

create >> run_job >> delete
```

---

## Chapter 6: Preemptible and Spot Workers

### What are preemptible workers?

**Preemptible VMs** are Google Compute Engine VMs that cost 60-90% less than regular VMs, with one catch: Google can terminate them at any time (within 24 hours). You get a 30-second notice before termination.

**Spot VMs** are similar but with no fixed 24-hour limit — they can be terminated at any time Google needs the capacity back.

### Why this works for Spark

Spark is designed to handle executor failures gracefully. When a preemptible VM is terminated:
1. YARN detects the lost executor
2. The tasks that were running on it are reassigned to other executors
3. Spark re-runs any lost work using the RDD lineage
4. Your job continues — possibly slower but correctly

**This only works for:**
- Fault-tolerant batch jobs (ETL, data transformation, aggregation)
- Jobs with checkpointing enabled

**This does NOT work for:**
- Jobs with strict time requirements
- Streaming jobs (Dataflow is better for those)

### Recommended configuration

```python
# ~20% regular workers (always available) + ~80% preemptible (cheap but evictable)
cluster_config = {
    "worker_config": {
        "num_instances": 2,           # Regular workers (always stable)
        "machine_type_uri": "n2-standard-4",
    },
    "secondary_worker_config": {
        "num_instances": 8,           # Preemptible workers (cheap, possibly evicted)
        "machine_type_uri": "n2-standard-4",
        "preemptibility": "PREEMPTIBLE",
    },
}
```

With this config, even if all preemptible workers are evicted, your job continues on the 2 regular workers (slower but complete).

---

## Chapter 7: Autoscaling

For long-running clusters, manually sizing the cluster is wasteful. **Autoscaling** adds or removes workers automatically based on YARN's resource utilization.

### How autoscaling works

```
Every 2 minutes, Dataproc evaluates:

  If YARN pending memory > threshold:
    → Add workers (scale up, up to max_instances)

  If YARN yarn.nodemanager.resource.memory-mb utilization < threshold:
    → Remove workers (scale down, down to min_instances), after cooldown period
```

### Example autoscaling policy

```yaml
# dataproc-autoscaling-policy.yaml
workerConfig:
  minInstances: 2       # Never fewer than 2 workers
  maxInstances: 20      # Never more than 20 workers

secondaryWorkerConfig:
  maxInstances: 50      # Up to 50 preemptible workers

basicAlgorithm:
  yarnConfig:
    scaleUpFactor: 1.0          # Add 100% of needed workers (aggressive)
    scaleDownFactor: 0.5        # Remove 50% of excess (conservative)
    scaleUpMinWorkerFraction: 0.0
    scaleDownMinWorkerFraction: 0.0
    gracefulDecommissionTimeout: 1h  # Give tasks time to finish before removing
  cooldownPeriod: 5m   # Wait 5 min between scale operations (avoid thrashing)
```

---

## Chapter 8: Writing PySpark Code — The Essentials

### Setting up a SparkSession

Every PySpark job starts with a SparkSession:

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Create a SparkSession (only one per application)
spark = SparkSession.builder \
    .appName("MyETLJob") \
    .getOrCreate()

# Adjust log level to reduce noise
spark.sparkContext.setLogLevel("WARN")
```

### Reading data

```python
# Read Parquet from Cloud Storage
df = spark.read.parquet("gs://my-bucket/data/year=2026/month=01/")

# Read CSV
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("gs://my-bucket/raw/orders.csv")

# Read from BigQuery (requires BigQuery connector)
df = spark.read \
    .format("bigquery") \
    .option("table", "my-project.analytics.orders") \
    .load()

# Print schema
df.printSchema()

# Preview data (action - triggers computation)
df.show(10)
print(f"Row count: {df.count()}")
```

### Transformations

```python
# Select columns (like SELECT in SQL)
df_selected = df.select("user_id", "country", "amount", "event_date")

# Filter (like WHERE)
df_de = df.filter(F.col("country") == "DE")
df_recent = df.filter(F.col("event_date") >= "2026-01-01")
df_combined = df.filter(
    (F.col("country") == "DE") & (F.col("amount") > 100)
)

# Add new column (like computed column in SQL)
df_enriched = df.withColumn(
    "revenue_bucket",
    F.when(F.col("amount") >= 1000, "VIP")
     .when(F.col("amount") >= 200, "Regular")
     .otherwise("Low")
)

# Rename column
df_renamed = df.withColumnRenamed("event_date", "order_date")

# Drop column
df_clean = df.drop("internal_id")
```

### Aggregations

```python
# GroupBy + aggregate
summary = df.groupBy("country", "campaign") \
    .agg(
        F.count("*").alias("order_count"),
        F.sum("amount").alias("total_revenue"),
        F.avg("amount").alias("avg_order"),
        F.countDistinct("user_id").alias("unique_users")
    ) \
    .orderBy(F.desc("total_revenue"))

summary.show()
```

### Joins

```python
# Read both datasets
orders_df = spark.read.parquet("gs://bucket/orders/")
users_df = spark.read.parquet("gs://bucket/users/")

# Inner join (keep only matching records)
result = orders_df.join(users_df, on="user_id", how="inner")

# Left join (keep all orders, fill nulls for non-matching users)
result = orders_df.join(users_df, on="user_id", how="left")

# Join on multiple columns
result = orders_df.join(
    users_df,
    on=["user_id", "country"],
    how="inner"
)

# Broadcast join (optimize when one table is small)
from pyspark.sql.functions import broadcast
result = orders_df.join(broadcast(users_df), on="user_id", how="inner")
# broadcast() tells Spark to copy the small table to all executors
# instead of shuffling the large table — much faster for small lookups
```

### Window functions

```python
from pyspark.sql import Window

# Running total of revenue by date
window_spec = Window.orderBy("event_date").rowsBetween(
    Window.unboundedPreceding, Window.currentRow
)
df_with_running_total = df.withColumn(
    "cumulative_revenue",
    F.sum("amount").over(window_spec)
)

# Rank within country by spend
rank_spec = Window.partitionBy("country").orderBy(F.desc("total_spend"))
df_ranked = df.withColumn("rank_in_country", F.rank().over(rank_spec))

# Previous row value (lag)
lag_spec = Window.partitionBy("user_id").orderBy("event_date")
df_with_prev = df.withColumn(
    "prev_amount",
    F.lag("amount", 1).over(lag_spec)
)
```

### Writing output

```python
# Write Parquet to Cloud Storage (partitioned by date)
df_result.write \
    .mode("overwrite") \
    .partitionBy("event_date", "country") \
    .parquet("gs://my-bucket/output/processed/")

# Write to BigQuery
df_result.write \
    .format("bigquery") \
    .option("table", "my-project.analytics.daily_summary") \
    .option("temporaryGcsBucket", "my-temp-bucket") \
    .mode("append") \
    .save()

# Write CSV (for human-readable output)
df_result.coalesce(1).write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv("gs://my-bucket/output/report/")
```

### Using Spark SQL

You can also write SQL directly in Spark — often cleaner for complex transformations:

```python
# Register a DataFrame as a temporary SQL view
df.createOrReplaceTempView("orders")
users_df.createOrReplaceTempView("users")

# Write SQL
result = spark.sql("""
    SELECT
        o.country,
        o.campaign,
        COUNT(*)            AS order_count,
        SUM(o.amount)       AS total_revenue,
        COUNT(DISTINCT u.user_id) AS unique_users
    FROM orders o
    INNER JOIN users u ON o.user_id = u.user_id
    WHERE o.event_date >= '2026-01-01'
      AND o.country = 'DE'
    GROUP BY o.country, o.campaign
    ORDER BY total_revenue DESC
""")

result.show()
```

---

## Chapter 9: Common Spark Performance Problems

### Problem 1: Data skew

**Symptom:** 99 tasks finish in 2 minutes, 1 task runs for 45 minutes. You're waiting for one task.

**Cause:** One partition key has vastly more data than others. E.g., in an e-commerce dataset, `user_id = "guest"` might have 80% of all rows.

**Fix:**
```python
# Option 1: Filter the skewed key, process separately, union
regular = df.filter(F.col("user_id") != "guest")
guest = df.filter(F.col("user_id") == "guest")

regular_result = regular.groupBy("user_id").sum("amount")
guest_result = guest.repartition(50).groupBy("user_id").sum("amount")  # force parallelism

result = regular_result.union(guest_result)

# Option 2: Salting — add random prefix to redistribute
import random
df_salted = df.withColumn(
    "user_id_salted",
    F.concat(F.col("user_id"), F.lit("_"), (F.rand() * 10).cast("int").cast("string"))
)
```

### Problem 2: Too many small files

**Symptom:** Job reads 100,000 files of 1 KB each — each file is one task, creating 100,000 tiny tasks with more overhead than work.

**Fix:**
```python
# After reading, coalesce into a reasonable number of partitions
df = spark.read.parquet("gs://bucket/path/").coalesce(100)

# Or repartition (causes a shuffle but creates even-sized partitions)
df = spark.read.parquet("gs://bucket/path/").repartition(200)
```

### Problem 3: Too few partitions (not enough parallelism)

**Symptom:** Only 4 tasks run at once even though you have 200 executor cores. 95% of cluster is idle.

**Fix:**
```python
# Rule of thumb: 2-3 tasks per CPU core
total_cores = 200  # 50 executors × 4 cores each
optimal_partitions = total_cores * 3  # = 600

df = df.repartition(600)

# Also set for shuffle operations
spark.conf.set("spark.sql.shuffle.partitions", "600")
# Default is 200, which is too low for large clusters
```

### Problem 4: Running out of memory (OOM errors)

**Symptom:** `java.lang.OutOfMemoryError` on executors. Stage fails and retries.

**Common causes and fixes:**
```python
# Cause 1: Joining a large table with itself → broadcast the small side
result = large_df.join(broadcast(small_df), on="id")

# Cause 2: Collecting results to driver
# BAD: df.collect() on 100M rows crashes the driver
# GOOD: write to GCS, then sample
df.write.parquet("gs://output/")
sample = df.sample(fraction=0.01).collect()  # only collect 1%

# Cause 3: Grouping by a high-cardinality column with complex aggregations
# → Increase executor memory in cluster config
# executor-memory: 8g → 16g
```

---

## Chapter 10: When to Use Dataproc vs BigQuery vs Dataflow

This is the most critical question in any interview. Get it wrong and you lose credibility.

```
Question to ask: "What is the workload?"

OLAP SQL analytics on structured data
  → BigQuery ✅ (serverless, SQL, fastest for analytics)

Existing Spark/Hadoop jobs from on-prem, minimal code change wanted
  → Dataproc ✅ (lift-and-shift, same Spark code, fastest migration path)

Complex multi-step ETL with custom Python/Scala logic, ML training
  → Dataproc ✅ (full Spark ecosystem, MLlib, custom libraries)

New streaming pipeline (Pub/Sub → transform → BigQuery)
  → Dataflow ✅ (serverless Beam, no cluster to manage, exactly-once semantics)

New batch pipeline, no existing Spark code, want serverless
  → Dataflow or Dataproc Serverless ✅

High-frequency OLTP writes (thousands of rows/second)
  → Cloud Spanner or Cloud SQL ✅ (not BigQuery or Dataproc)
```

### The pre-sales version of this answer

> "The choice between BigQuery, Dataproc, and Dataflow depends on three things: your current stack, your team's skills, and the nature of the workload. If you have existing Spark or Hadoop jobs, Dataproc is the fastest path to the cloud — same code, managed infrastructure, 50-70% lower TCO. If you're building new pipelines and want to eliminate cluster management entirely, Dataflow for streaming or BigQuery for SQL analytics. Most mature GCP data platforms use all three in different layers of the stack."

---

## Chapter 11: Key Dataproc Interview Concepts

### "What is Dataproc?" — 30-second answer

> "Dataproc is Google Cloud's managed Apache Spark and Hadoop service. It lets you run Spark jobs on GCP without managing any cluster infrastructure — the cluster starts in 90 seconds, you run your job, and it tears down. The key architectural difference from on-premise Hadoop is that data lives in Cloud Storage, not on the cluster nodes — so the cluster is stateless compute that can be ephemeral. This, combined with preemptible workers and per-second billing, typically cuts TCO by 50-60% compared to always-on Spark clusters."

### "When would you recommend Dataproc over BigQuery?"

> "When the customer has existing PySpark or Scala Spark jobs they want to migrate to the cloud with minimal code changes. BigQuery is SQL-native, so Spark jobs with complex custom transformations, UDFs, MLlib models, or graph processing don't translate well to SQL. Dataproc runs the same Spark code. I'd also choose Dataproc when the customer needs the full Spark ecosystem — Hive, HBase, Flink — or when they're doing large-scale ML training with Spark MLlib."

### "How do preemptible workers work?"

> "Preemptible VMs cost 60-90% less than regular VMs. Google can terminate them with a 30-second notice. Spark tolerates this because when a node fails, YARN detects it and reassigns the tasks that were running on it to other nodes — those tasks re-run from scratch. The job completes correctly, just potentially slower if many nodes are preempted at once. We protect against this by maintaining a small number of regular workers — typically 20% — so the job always has a stable core even if all preemptibles are reclaimed."

### "What's the difference between Dataproc and Dataflow?"

> "Both run distributed data processing on GCP, but they're different models. Dataproc is a managed cluster — you provision workers, YARN manages resource allocation, and you run Spark/Hadoop jobs. You have full control over the cluster but you manage sizing and tuning. Dataflow is fully serverless — it runs Apache Beam pipelines with no cluster to manage at all. Dataflow auto-scales workers at the task level. For lift-and-shift of existing Spark jobs: Dataproc. For new cloud-native streaming pipelines: Dataflow."

---

## Quick Reference Card

```
Dataproc Mental Model:
  Data in Cloud Storage (GCS) — persists independently
    ↑ read by
  Spark Executors on Worker Nodes — stateless compute
    ↑ managed by
  YARN ResourceManager on Master Node — allocates CPU/memory
    ↑ submitted to
  Your PySpark/Scala code via spark-submit or Dataproc Jobs API

Cluster types:
  Standard      → 1 master + N workers
  High-Avail    → 3 masters + N workers (production)
  Single-node   → 1 machine (dev/test)
  Serverless    → no cluster (submit PySpark, Google manages everything)

Cost levers (highest to lowest impact):
  1. Ephemeral clusters (pay only for job runtime)
  2. Preemptible/Spot workers (60-90% cheaper)
  3. Autoscaling (right-size to workload)
  4. Spark tuning (fewer shuffles, less data movement)
  5. Right VM size (CPU vs memory ratio for workload type)

Spark execution model:
  Action triggered → DAGScheduler builds stages → stages become TaskSets
  → TaskScheduler assigns tasks to executors → executors run tasks on partitions
  → shuffle between stages → results aggregated → output written

Key Spark operations cost:
  Cheap (no shuffle): filter, select, withColumn, map
  Expensive (shuffle): groupBy, join, distinct, orderBy, repartition
```
