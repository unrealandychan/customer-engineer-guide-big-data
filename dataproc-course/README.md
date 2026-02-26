# Dataproc Mini-Course

A structured, six-lesson course on **Google Cloud Dataproc** built from the
[official documentation](https://cloud.google.com/dataproc/docs).

---

## Course Map

| # | Lesson | What you will learn |
|---|--------|---------------------|
| 1 | [What is Dataproc?](01-what-is-dataproc.md) | Definition, advantages, deployment modes, when to use it |
| 2 | [How Spark Works](02-how-spark-works.md) | RDDs, DataFrames, DAG, shuffle, YARN, executors |
| 3 | [Cluster Architecture](03-cluster-architecture.md) | Master/worker nodes, GCS vs HDFS, cluster types |
| 4 | [Managing Clusters](04-managing-clusters.md) | gcloud CLI, ephemeral patterns, preemptibles, autoscaling |
| 5 | [Writing PySpark Jobs](05-writing-pyspark-jobs.md) | SparkSession, transforms, aggregations, BQ/GCS connectors |
| 6 | [Optimization, Pricing & Operations](06-optimization-pricing-and-operations.md) | Cost model, tuning, common failures, decision guide |

---

## Prerequisites

- Basic Python (you don't need to know Spark beforehand)
- Familiarity with what SQL does (helpful but not required)
- A Google Cloud project with billing enabled (for hands-on practice)

---

## Official Documentation Links

| Topic | URL |
|-------|-----|
| Product Overview | https://cloud.google.com/dataproc/docs/concepts/overview |
| Quickstart (create cluster) | https://cloud.google.com/dataproc/docs/quickstarts |
| Submit a Job | https://cloud.google.com/dataproc/docs/guides/submit-job |
| Life of a Job | https://cloud.google.com/dataproc/docs/concepts/jobs/life-of-a-job |
| Pricing | https://cloud.google.com/dataproc/pricing |
| Best Practices | https://cloud.google.com/dataproc/docs/guides/dataproc-best-practices |
| Serverless for Apache Spark | https://cloud.google.com/dataproc-serverless/docs |
| Dataproc on GKE | https://cloud.google.com/dataproc/docs/concepts/jobs/dataproc-gke |

---

## How to Use This Course

1. Read each lesson in order — each builds on the previous.
2. Every lesson ends with a **Practice Q&A** section — try to answer before revealing.
3. Run the hands-on code in `exercises/03-dataproc-pyspark/` in this repo.
4. After Lesson 6, attempt the design challenge at the end.

---

## Companion Material in This Repo

| File | What it covers |
|------|---------------|
| `docs/12-dataproc-from-scratch.md` | Deep-dive Spark internals & PySpark patterns |
| `exercises/03-dataproc-pyspark/` | Runnable PySpark ETL & streaming examples |
| `exercises/07-terraform-gcp/02-dataproc/` | Terraform cluster provisioning |
