# Lesson 1 — What is Dataproc?

> **Official doc:** https://cloud.google.com/dataproc/docs/concepts/overview

---

## One-Sentence Definition

**Dataproc** is Google Cloud's **fully managed service for running Apache Spark and Apache Hadoop** workloads — without the operational overhead of managing clusters yourself.

---

## Why Does It Exist?

Before managed services, running Spark or Hadoop meant:

1. Provisioning physical servers (or VMs by hand)
2. Installing, configuring, and patching the Hadoop ecosystem yourself
3. Managing YARN, HDFS, Zookeeper, and a zoo of open-source components
4. Paying for idle servers between jobs

Dataproc solves all of this. You get a ready-to-use Spark/Hadoop cluster in **under 90 seconds**, run your jobs, and delete it when done.

---

## What Dataproc Supports

Dataproc comes pre-installed with:

| Component | What it does |
|-----------|-------------|
| **Apache Spark** | Fast in-memory distributed processing; batch & streaming |
| **Apache Hadoop (MapReduce + HDFS)** | Distributed storage and batch processing |
| **Apache Hive** | SQL-like queries on distributed data |
| **Apache Pig** | Scripting for data transformations |
| **Apache Flink** | Stream processing (available via initialization actions) |
| **Jupyter notebooks** | Interactive exploration on Dataproc clusters |

Plus built-in **connectors** to: BigQuery, Cloud Storage, Bigtable, Cloud Spanner.

---

## The Four Advantages (from official docs)

### 1. Low Cost — $0.01 per vCPU per hour
```
Dataproc charge = $0.010 × number_of_vCPUs × hours_running
```
This is **on top of** the Compute Engine VM cost — but it's tiny compared to on-premises hardware.
Preemptible (Spot) VMs reduce the Compute Engine portion by 60–91%.

### 2. Super Fast — 90-second clusters
Clusters start in **90 seconds or less**. You can spin up a 20-node cluster, run a 30-minute job, and delete it — paying only for 30 minutes of use.

### 3. Integrated — native GCP connections
| GCP Service | Integration |
|-------------|-------------|
| Cloud Storage | Use `gs://` paths directly in Spark — replaces HDFS |
| BigQuery | Spark BigQuery connector reads/writes BQ tables natively |
| Bigtable | HBase-compatible connector |
| Cloud Logging | Cluster and job logs streamed automatically |
| Cloud Monitoring | Metrics dashboards out of the box |

### 4. Managed — no admin work
- OS patches applied automatically
- Hadoop component upgrades managed by Google
- No Zookeeper configuration, no HDFS formatting, no YARN tuning from scratch

---

## Ways to Access Dataproc

| Method | Best for |
|--------|----------|
| **Cloud Console (UI)** | Manual cluster creation, job submission, monitoring |
| **gcloud CLI** | Scripting, automation, one-off jobs |
| **REST API** | Programmatic control from any language |
| **Cloud Client Libraries** | Python, Java, Go apps that manage Dataproc programmatically |
| **Terraform** | Infrastructure-as-code cluster provisioning |

---

## Dataproc Deployment Modes

```
┌─────────────────────────────────────────────────────────────┐
│                       DATAPROC                              │
│                                                             │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  on Compute      │  │  on GKE      │  │  Serverless  │  │
│  │  Engine (VMs)    │  │  (Kubernetes)│  │  for Spark   │  │
│  │                  │  │              │  │              │  │
│  │ • Traditional    │  │ • Share GKE  │  │ • No cluster │  │
│  │   clusters       │  │   cluster    │  │   to manage  │  │
│  │ • Full control   │  │ • Bin-pack   │  │ • Per-batch  │  │
│  │ • Most common    │  │   workloads  │  │   billing    │  │
│  └──────────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

| Mode | When to use |
|------|------------|
| **Compute Engine** | Full control, persistent clusters, custom machine types |
| **GKE** | Already using Kubernetes; want to bin-pack Spark + other workloads |
| **Serverless** | Fully managed, no cluster tuning, pay-per-second, simpler but less flexible |

---

## Dataproc vs BigQuery vs Dataflow (Mental Model)

| Question | Answer |
|----------|--------|
| "I need SQL on massive tables" | **BigQuery** — serverless SQL |
| "I have existing Spark/Hadoop code to run" | **Dataproc** — managed Spark |
| "I need real-time streaming pipelines with Apache Beam" | **Dataflow** — managed Beam |
| "I need ML on huge datasets with custom code" | **Dataproc** — Spark MLlib or bring your own |

---

## Practice Q&A

**Q1: What is Dataproc in one sentence?**
<details><summary>Answer</summary>
Dataproc is Google Cloud's managed service for running Apache Spark and Hadoop workloads without managing cluster infrastructure.
</details>

**Q2: How long does it take to create a Dataproc cluster?**
<details><summary>Answer</summary>
90 seconds or less (official doc confirmed).
</details>

**Q3: What is the Dataproc charge formula?**
<details><summary>Answer</summary>
`$0.010 × number_of_vCPUs × hours_running` — billed per second, 1-minute minimum, on top of Compute Engine VM costs.
</details>

**Q4: A customer has Spark jobs running on-premises. They want to migrate to GCP. Which service?**
<details><summary>Answer</summary>
Dataproc — it runs the same Spark code with no API changes. The customer uses the same `spark-submit` commands.
</details>

**Q5: Name three GCP services that Dataproc integrates with natively.**
<details><summary>Answer</summary>
Cloud Storage (`gs://` paths), BigQuery (Spark BQ connector), Bigtable (HBase connector). Also: Cloud Logging and Cloud Monitoring.
</details>
