# Lesson 3 — Cluster Architecture

> Understanding the physical structure of a Dataproc cluster lets you choose the right configuration and debug failures.

---

## Cluster Overview

A Dataproc cluster has two types of nodes:

```
┌──────────────────────────────────────────────────────────────┐
│                    DATAPROC CLUSTER                          │
│                                                              │
│  ┌─────────────────────────────────┐                         │
│  │         MASTER NODE(S)          │                         │
│  │                                 │                         │
│  │  • YARN ResourceManager         │                         │
│  │  • HDFS NameNode                │                         │
│  │  • Spark Driver (when running)  │                         │
│  │  • Hive Metastore               │                         │
│  │  • History Server               │                         │
│  └─────────────────────────────────┘                         │
│                   │                                          │
│       ┌───────────┼───────────┐                              │
│       ↓           ↓           ↓                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                        │
│  │ WORKER  │ │ WORKER  │ │ WORKER  │  ... N workers          │
│  │         │ │         │ │         │                        │
│  │ YARN NM │ │ YARN NM │ │ YARN NM │                        │
│  │ HDFS DN │ │ HDFS DN │ │ HDFS DN │                        │
│  │Executor │ │Executor │ │Executor │                        │
│  └─────────┘ └─────────┘ └─────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Master Node Components

| Component | Role |
|-----------|------|
| **YARN ResourceManager** | Allocates CPU/memory to applications; the cluster's resource broker |
| **HDFS NameNode** | Manages the file system namespace (which blocks live on which DataNodes) |
| **Spark Driver** | Runs in YARN cluster mode on the master when you submit a job |
| **Hive Metastore** | Stores table/schema definitions for Hive and Spark SQL |
| **Spark History Server** | Web UI for completed job DAGs and metrics — port 18080 |

---

## Worker Node Components

| Component | Role |
|-----------|------|
| **YARN NodeManager** | Reports capacity to ResourceManager; launches containers |
| **HDFS DataNode** | Stores actual data blocks (but rarely used — see GCS section below) |
| **Spark Executor** | JVM that runs tasks; one executor per worker (or more, depending on config) |

---

## GCS vs HDFS — The Critical Architectural Difference

This is one of the most important Dataproc concepts for interviews.

### On-premises Hadoop:
```
Storage (HDFS) = Compute nodes
Data lives ON the worker machines
Moving computation to data = good
```

### Dataproc on GCP:
```
Storage (GCS) = Separate from compute
Workers read from gs://my-bucket/
Compute and storage are DECOUPLED
```

### Why GCS is Better for Dataproc

| Concern | HDFS | GCS |
|---------|------|-----|
| Persistence | Data lost when cluster deleted | Data survives cluster deletion |
| Scaling | Must grow cluster to add storage | Scale storage and compute independently |
| Cost | Pay for VMs even when idle (to keep data) | Pay only for storage (very cheap) |
| Durability | Depends on HDFS replication (3×) | 11 nines of durability (Google managed) |
| Performance | Low latency (local disk) | Slightly higher latency; mitigated by Dataproc connectors |

**Practical rule:** Store all data in GCS. Use HDFS only for temporary shuffle files and intermediate results during a job.

```python
# Read from GCS (recommended)
df = spark.read.parquet("gs://my-bucket/input/")

# Write to GCS (recommended)
df.write.parquet("gs://my-bucket/output/")
```

---

## Cluster Types

### Standard (1 master, N workers)
```
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --num-workers=4 \
  --worker-machine-type=n1-standard-4
```
- Default setup
- Master is a single point of failure (job queue lost if master dies)
- Fine for development and most batch jobs

### High Availability (3 masters, N workers)
```
gcloud dataproc clusters create my-ha-cluster \
  --region=us-central1 \
  --num-masters=3 \
  --num-workers=4
```
- Three master nodes with Zookeeper for leader election
- YARN ResourceManager and HDFS NameNode are replicated
- Use for production, long-running clusters, or SLA-sensitive jobs

### Single-Node (1 node, no workers)
```
gcloud dataproc clusters create my-dev-cluster \
  --region=us-central1 \
  --single-node
```
- Master runs everything; no separate workers
- Use for development, testing, Jupyter notebooks
- Not suitable for production jobs

### Serverless for Apache Spark
```
gcloud dataproc batches submit pyspark my_job.py \
  --region=us-central1
```
- No cluster to manage — Google handles everything
- Separate pricing (per DCU — Dataproc Compute Unit)
- No warm-up time issues (sessions persist)
- Less flexible: limited Spark configuration control

---

## Machine Type Guidance

| Worker role | Recommended type | Notes |
|-------------|-----------------|-------|
| General compute | `n1-standard-4` or `n2-standard-4` | 4 vCPUs, 15 GB RAM |
| Memory-intensive | `n1-highmem-8` | 8 vCPUs, 52 GB RAM — for large joins/aggregations |
| GPU/ML | `n1-standard-8` + GPU | Attach NVIDIA T4 for Spark ML or TensorFlow on Spark |
| Primary workers | Regular VMs | Always-on, HDFS DataNodes |
| Secondary workers | Preemptible/Spot VMs | Cost reduction; Spark-safe |

---

## Initialization Actions

Scripts that run on every node when the cluster is created — used to install additional software.

```bash
# Install Python packages on cluster creation
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --initialization-actions=gs://my-bucket/init.sh
```

Example `init.sh`:
```bash
#!/bin/bash
pip install pandas scikit-learn
```

---

## Dataproc Images

Each Dataproc cluster runs a specific **image version** that pins the versions of all Hadoop ecosystem components.

```bash
# Check available images
gcloud dataproc clusters create my-cluster \
  --image-version=2.1-debian11

# Image 2.1 → Spark 3.3, Hadoop 3.3, Hive 3.1
# Image 2.2 → Spark 3.5, Hadoop 3.4
```

---

## Practice Q&A

**Q1: What runs on the Dataproc master node?**
<details><summary>Answer</summary>
YARN ResourceManager, HDFS NameNode, Spark Driver (for submitted jobs), Hive Metastore, and the Spark History Server.
</details>

**Q2: Why does Dataproc use GCS instead of HDFS for primary storage?**
<details><summary>Answer</summary>
GCS decouples compute from storage. Data persists after cluster deletion (no vendor lock-in), you can scale each independently, and you only pay for storage when the cluster is off. HDFS data would be lost when the cluster is deleted.
</details>

**Q3: What is a High Availability cluster and when should you use it?**
<details><summary>Answer</summary>
An HA cluster has 3 master nodes with Zookeeper leader election. Use it for production or long-running clusters where master failure would be unacceptable.
</details>

**Q4: When would you use a Single-Node cluster?**
<details><summary>Answer</summary>
For development, testing, and running Jupyter notebooks. Not for production jobs.
</details>

**Q5: What is an initialization action?**
<details><summary>Answer</summary>
A script (stored in GCS) that runs on every cluster node at creation time, used to install additional Python packages or software before jobs start.
</details>
