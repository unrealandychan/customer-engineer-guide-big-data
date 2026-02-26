# Lesson 2 — How Spark Works

> Dataproc is mostly a Spark service. To use it well, you need to understand how Spark actually processes data.

---

## The Big Idea: Distributed Processing

A single machine can process data limited by its RAM and CPU. Spark solves this by splitting data across **many machines** and processing pieces in parallel.

```
Single machine:              Spark cluster:
┌──────────┐                 ┌──────┐ ┌──────┐ ┌──────┐
│ 1 CPU    │  →  100x data  │ node │ │ node │ │ node │
│ 64 GB RAM│                 │  1   │ │  2   │ │  3   │
└──────────┘                 └──────┘ └──────┘ └──────┘
                             All work in parallel
```

---

## Core Data Abstractions

### RDD — Resilient Distributed Dataset
The low-level foundation. An RDD is a **collection of data partitioned across nodes**.
- **Resilient** = can recover from node failures by replaying lineage
- **Distributed** = split across the cluster
- **Dataset** = just a collection of records (can be any type)

You rarely use RDDs directly in modern Spark — DataFrames are preferred.

### DataFrame
A **table of data with named columns and a schema** — like a distributed Pandas DataFrame or a SQL table.

```python
# DataFrame — preferred in modern Spark
df = spark.read.parquet("gs://my-bucket/data/")
df.filter(df.age > 30).groupBy("city").count().show()
```

DataFrames are **optimized** — Spark's Catalyst optimizer rewrites your query into the most efficient physical plan.

### Dataset (Scala/Java only)
Typed DataFrames. Not available in Python. Don't worry about this for PySpark work.

---

## Lazy Evaluation — The Key Insight

Spark does **nothing** until you call an **action**.

```
transformations (lazy)       action (triggers execution)
─────────────────────────    ──────────────────────────
df.filter(...)               .show()
df.select(...)               .count()
df.groupBy(...)              .collect()
df.join(...)                 .write.parquet(...)
df.withColumn(...)
```

When you call `.show()`, Spark looks at all queued transformations, builds an optimized **execution plan**, and runs it.

**Why lazy?**
- Spark can optimize the whole chain at once (e.g., push filters down before joins)
- Nothing runs until you're ready — no wasted computation on intermediate results

---

## The DAG — Directed Acyclic Graph

When you trigger an action, Spark builds a **DAG** — a graph showing the sequence of computations.

```
read CSV   →   filter   →   groupBy   →   sort   →   write
    ↘              ↗
     repartition
```

The DAG Scheduler divides this into **stages**. A new stage begins wherever a **shuffle** is required.

---

## Stages and Shuffle

### Shuffle = the most expensive operation
A **shuffle** moves data between partitions (and potentially between nodes) so that records that need to be grouped together end up on the same node.

```
BEFORE groupBy (data on 3 nodes):      AFTER groupBy (shuffle):
Node 1: city=Paris, city=Berlin        Node 1: all Paris records
Node 2: city=Paris, city=Tokyo         Node 2: all Berlin records
Node 3: city=Berlin, city=Tokyo        Node 3: all Tokyo records
                                       (network transfer happened)
```

**Shuffles happen for:**
- `groupBy`, `groupByKey`
- `join` (unless broadcast join)
- `distinct`
- `repartition`
- `orderBy` / `sort`

**Why care?** Each shuffle writes data to disk and sends it over the network. Minimize shuffles = faster jobs.

### ShuffleMapStage vs ResultStage
Spark creates two types of stages:
- **ShuffleMapStage** — computes output for a shuffle (writes shuffle files to disk)
- **ResultStage** — the final stage that produces the output you asked for

---

## Tasks

Within each stage, Spark creates **one task per partition**.

```
Stage with 200 partitions → 200 tasks run in parallel across executors
```

Default partition count is often 200 (controlled by `spark.sql.shuffle.partitions`).

---

## Executors

An **executor** is a **Java Virtual Machine (JVM) process** running on a worker node. Each executor:
- Has its own memory heap
- Runs multiple tasks in parallel (one per CPU core)
- Stores cached data in memory

```
Worker Node:
┌────────────────────────────────────┐
│  Executor JVM                      │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ Task 1 │ │ Task 2 │ │ Task 3 │  │
│  │(core 1)│ │(core 2)│ │(core 3)│  │
│  └────────┘ └────────┘ └────────┘  │
│  Memory: 8 GB (heap + off-heap)    │
└────────────────────────────────────┘
```

### Executor Failure Tolerance
If an executor fails, the **driver** reschedules those tasks on another executor. This is Spark's fault tolerance — it does NOT re-read all data, just re-runs the lost tasks.

---

## The Driver

The **driver** is the process running your `main()` function or notebook. It:
- Builds the DAG
- Talks to the cluster manager (YARN) to request executor resources
- Schedules tasks across executors
- Collects results when you call `.collect()`

**NEVER** call `.collect()` on a huge DataFrame — it brings all data to the driver and causes OOM.

---

## YARN — The Cluster Manager on Dataproc

YARN (Yet Another Resource Negotiator) manages resources on the cluster.

```
┌─────────────────────────────────────────┐
│              MASTER NODE                │
│                                         │
│  YARN ResourceManager  ←→  Spark Driver │
│       │                                 │
│       │ allocates resources             │
│       ↓                                 │
│  ┌──────────┐  ┌──────────┐             │
│  │ Worker 1 │  │ Worker 2 │             │
│  │ YARN NM  │  │ YARN NM  │             │
│  │ Executor │  │ Executor │             │
│  └──────────┘  └──────────┘             │
└─────────────────────────────────────────┘
```

### YARN Deployment Modes

| Mode | Where driver runs | Best for |
|------|------------------|---------|
| **cluster mode** | On a worker node inside YARN | Production jobs — driver survives SSH disconnect |
| **client mode** | On the machine that submitted the job | Interactive / debugging — logs visible immediately |

On Dataproc: `gcloud dataproc jobs submit pyspark` uses **cluster mode** by default.

---

## Spark Configuration Key Settings

| Setting | Default | What it controls |
|---------|---------|-----------------|
| `spark.sql.shuffle.partitions` | 200 | Partitions after a shuffle — tune for your data size |
| `spark.executor.memory` | 1g | Memory per executor |
| `spark.executor.cores` | 1 | Cores per executor |
| `spark.driver.memory` | 1g | Driver memory |
| `spark.dynamicAllocation.enabled` | false | Let Spark scale executors automatically |

---

## Practice Q&A

**Q1: What is the difference between a transformation and an action in Spark?**
<details><summary>Answer</summary>
Transformations (like `filter`, `groupBy`, `join`) are lazy — they build the execution plan. Actions (like `show()`, `count()`, `write`) trigger actual computation.
</details>

**Q2: What is a shuffle and why is it expensive?**
<details><summary>Answer</summary>
A shuffle redistributes data across nodes so records that belong together land on the same node. It's expensive because it writes to disk and transfers data over the network.
</details>

**Q3: What is a Spark executor?**
<details><summary>Answer</summary>
A JVM process running on a worker node that executes tasks, stores cached data in memory, and runs one task per CPU core.
</details>

**Q4: What happens if an executor fails?**
<details><summary>Answer</summary>
The driver reschedules the failed tasks on another executor. Data is re-read or recomputed from the lineage — no full job restart required.
</details>

**Q5: In YARN cluster mode, where does the driver run?**
<details><summary>Answer</summary>
On a worker node inside the YARN cluster — not on the submitting machine. This makes production jobs resilient to SSH disconnects.
</details>
