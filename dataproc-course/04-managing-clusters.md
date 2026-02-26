# Lesson 4 — Managing Clusters

> Official doc: https://cloud.google.com/dataproc/docs/guides/submit-job

---

## gcloud Dataproc CLI — Complete Cheatsheet

### Cluster Operations

```bash
# CREATE a cluster
gcloud dataproc clusters create CLUSTER_NAME \
  --region=us-central1 \
  --zone=us-central1-a \
  --master-machine-type=n1-standard-4 \
  --worker-machine-type=n1-standard-4 \
  --num-workers=4 \
  --image-version=2.1-debian11 \
  --project=MY_PROJECT_ID

# CREATE with preemptible secondary workers (cost optimized)
gcloud dataproc clusters create CLUSTER_NAME \
  --region=us-central1 \
  --num-workers=4 \
  --num-secondary-workers=8 \
  --secondary-worker-type=preemptible \
  --worker-machine-type=n1-standard-4

# LIST clusters
gcloud dataproc clusters list --region=us-central1

# DESCRIBE a cluster
gcloud dataproc clusters describe CLUSTER_NAME --region=us-central1

# SCALE (resize) a cluster
gcloud dataproc clusters update CLUSTER_NAME \
  --region=us-central1 \
  --num-workers=8

# DELETE a cluster
gcloud dataproc clusters delete CLUSTER_NAME --region=us-central1
```

### Job Operations

```bash
# SUBMIT a PySpark job
gcloud dataproc jobs submit pyspark gs://my-bucket/jobs/my_job.py \
  --cluster=CLUSTER_NAME \
  --region=us-central1 \
  -- --input=gs://my-bucket/input/ --output=gs://my-bucket/output/

# SUBMIT a Spark (JAR) job
gcloud dataproc jobs submit spark \
  --cluster=CLUSTER_NAME \
  --region=us-central1 \
  --class=org.apache.spark.examples.SparkPi \
  --jars=file:///usr/lib/spark/examples/jars/spark-examples.jar \
  -- 1000

# SUBMIT a Hive job
gcloud dataproc jobs submit hive \
  --cluster=CLUSTER_NAME \
  --region=us-central1 \
  --execute="SELECT count(*) FROM my_table"

# LIST jobs
gcloud dataproc jobs list \
  --cluster=CLUSTER_NAME \
  --region=us-central1

# WAIT for a job and stream output
gcloud dataproc jobs wait JOB_ID \
  --region=us-central1 \
  --project=MY_PROJECT_ID

# KILL a running job
gcloud dataproc jobs kill JOB_ID --region=us-central1
```

---

## Life of a Dataproc Job

From the official docs, a job goes through these states:

```
User submits job
      │
      ↓
  PENDING          ← waiting to be picked up by dataproc agent
      │
      ↓
  RUNNING          ← agent acquired job; driver started
      │
   ┌──┴──┐
   │QUEUED│        ← throttled (insufficient master resources)
   └──┬──┘
      │
  YARN apps complete
      │
      ↓
   DONE / ERROR
```

Key actors:
- **Dataproc service** — receives job from user, routes to agent
- **dataproc agent** — runs on master VM; spawns the driver process
- **driver** — runs your code (spark-submit, hadoop jar, beeline)
- **YARN** — runs the actual tasks on worker nodes

---

## The Ephemeral Cluster Pattern

The most cost-effective and recommended Dataproc pattern for batch jobs.

### Instead of this (persistent cluster):
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Cluster  │    │ Job 1    │    │ (idle)   │    │ Job 2    │
│ running  │    │ runs     │    │ paying   │    │ runs     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
   24 hours        30 min        3 hours           30 min
   = 24 hrs of VM cost
```

### Do this (ephemeral cluster):
```
Create cluster → Run job → Delete cluster    Create cluster → Run job → Delete cluster
   (2 min)       (30 min)   (1 min)             (2 min)       (30 min)   (1 min)
   = 33 min of VM cost per job
```

### Savings: Up to 70% on compute cost for batch workloads.

**The key enabler:** Data lives in **GCS**, not HDFS — so deleting the cluster does NOT delete your data.

---

## Airflow Orchestration for Ephemeral Clusters

Cloud Composer (managed Apache Airflow) is the standard way to automate the ephemeral pattern.

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator,
)
from airflow.utils.dates import days_ago

CLUSTER_NAME = "my-ephemeral-cluster"
REGION = "us-central1"
PROJECT_ID = "my-project"

CLUSTER_CONFIG = {
    "master_config": {
        "num_instances": 1,
        "machine_type_uri": "n1-standard-4",
    },
    "worker_config": {
        "num_instances": 4,
        "machine_type_uri": "n1-standard-4",
    },
}

PYSPARK_JOB = {
    "reference": {"project_id": PROJECT_ID},
    "placement": {"cluster_name": CLUSTER_NAME},
    "pyspark_job": {
        "main_python_file_uri": "gs://my-bucket/jobs/my_etl.py",
        "args": ["--date={{ ds }}"],  # Airflow templating
    },
}

with DAG(
    dag_id="daily_etl",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
) as dag:
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_cluster",
        cluster_name=CLUSTER_NAME,
        region=REGION,
        project_id=PROJECT_ID,
        cluster_config=CLUSTER_CONFIG,
    )

    submit_job = DataprocSubmitJobOperator(
        task_id="run_etl",
        job=PYSPARK_JOB,
        region=REGION,
        project_id=PROJECT_ID,
    )

    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_cluster",
        cluster_name=CLUSTER_NAME,
        region=REGION,
        project_id=PROJECT_ID,
        trigger_rule="all_done",  # delete even if job fails
    )

    create_cluster >> submit_job >> delete_cluster
```

---

## Preemptible (Spot) Workers

### What are preemptible workers?
- Spare compute capacity that Google can reclaim with 30-second warning
- Up to **91% cheaper** than regular VMs
- Perfect for Spark secondary workers because Spark retasks on node failure

### Worker Types

| Type | Persistence | Cost | Data stored? | Safe for Spark? |
|------|-------------|------|-------------|-----------------|
| **Primary workers** | Permanent during cluster lifetime | Full price | HDFS DataNode | Yes |
| **Secondary (preemptible)** | Can be reclaimed any time | 60-91% cheaper | No HDFS data | Yes (Spark retasks) |
| **Secondary (Spot)** | Like preemptible but GKE-native | Similar | No HDFS data | Yes |

### Recommended Split

```
┌─────────────────────────────────────────┐
│  20% primary workers (always available) │
│  80% preemptible workers (cheap)        │
│                                         │
│  Example: 2 primary + 8 preemptible     │
│  Cost saving vs 10 primary: ~65%        │
└─────────────────────────────────────────┘
```

### Why Spark Tolerates Preemptible Workers

1. Preemptible node is reclaimed by GCP
2. YARN NodeManager on that node stops responding
3. YARN ResourceManager detects failure
4. YARN re-schedules the tasks that were running on the lost node to another worker
5. Spark re-reads the lost partitions from GCS (not HDFS)

**No data loss** because data is in GCS, not local HDFS DataNodes.

```bash
# Create cluster with preemptible secondary workers
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --num-workers=2 \
  --num-secondary-workers=8 \
  --secondary-worker-type=preemptible \
  --worker-machine-type=n1-standard-8
```

---

## Autoscaling

Autoscaling automatically adds or removes workers based on YARN pending memory.

```yaml
# autoscaling-policy.yaml
workerConfig:
  minInstances: 2
  maxInstances: 20
  weight: 1

secondaryWorkerConfig:
  minInstances: 0
  maxInstances: 50
  weight: 1

basicAlgorithm:
  cooldownPeriod: 2m
  yarnConfig:
    scaleUpFactor: 1.0        # Double workers when scaling up
    scaleDownFactor: 1.0      # Remove all excess when scaling down
    scaleUpMinWorkerFraction: 0.0
    scaleDownMinWorkerFraction: 0.0
    gracefulDecommissionTimeout: 1h
```

```bash
# Create the policy
gcloud dataproc autoscaling-policies import my-policy \
  --source=autoscaling-policy.yaml \
  --region=us-central1

# Create cluster with autoscaling
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --autoscaling-policy=my-policy
```

**When NOT to use autoscaling:**
- Spark Structured Streaming (dynamic allocation conflicts with streaming executors)
- Jobs with very frequent shuffles (scaling during shuffle causes failures)
- Use Serverless for Apache Spark instead for fully-managed scaling

---

## Practice Q&A

**Q1: What is the ephemeral cluster pattern and why does it save money?**
<details><summary>Answer</summary>
Create a cluster → run the job → delete the cluster. You pay only for the duration of the job, not for idle time. Saves up to 70% on compute. This works because data lives in GCS, not HDFS, so no data is lost when the cluster is deleted.
</details>

**Q2: What is a preemptible worker and why is it safe to use with Spark?**
<details><summary>Answer</summary>
A preemptible VM is a discounted VM that GCP can reclaim at any time. It's safe with Spark because YARN detects the failure and reschedules tasks to other workers. Data is read from GCS (not local HDFS), so no data is lost.
</details>

**Q3: How do you delete a cluster even if its job fails in Airflow?**
<details><summary>Answer</summary>
Set `trigger_rule="all_done"` on the `DataprocDeleteClusterOperator` task — it runs regardless of upstream task success or failure.
</details>

**Q4: What does `gcloud dataproc jobs wait` do?**
<details><summary>Answer</summary>
It blocks and streams the job driver output to your terminal until the job completes — useful for monitoring jobs from the command line.
</details>

**Q5: When should you NOT use autoscaling?**
<details><summary>Answer</summary>
For Spark Structured Streaming jobs and jobs with very frequent shuffles. Use Serverless for Apache Spark instead for fully-managed auto-scaling streaming.
</details>
