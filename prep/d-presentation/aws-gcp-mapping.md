# Interview D — Presentation: AWS ↔ GCP Service Mapping

This is your bidirectional translation layer. You have deep AWS experience — this file lets you:
1. Defend every GCP architectural choice with confidence
2. Quickly answer "what's the AWS equivalent?" from Gene (technical probing)
3. Show you understand the conceptual model of both platforms, not just syntax

**Strategy:** When describing GCP choices, always say: *"This is the GCP approach — the AWS analogue is X, which I have deep experience with. The key difference here is Y."*

---

## Core Service Mapping Table

| Category | AWS Service | GCP Service | Key Difference to Know |
|---|---|---|---|
| **Object Storage** | S3 | Cloud Storage (GCS) | GCS has per-bucket location; S3 has per-bucket and per-object settings. Both support multi-region. |
| **Streaming Ingest** | Kinesis Data Streams | Pub/Sub | Pub/Sub is serverless (no shard management). Kinesis requires shard capacity planning. Pub/Sub has global routing; Kinesis is regional. |
| **Streaming Analytics** | Kinesis Data Analytics (Flink) | Dataflow (Apache Beam) | Beam is multi-runner (Dataflow, Spark, Flink). Kinesis Analytics is Flink-native. Dataflow is serverless and autoscales; KDA requires capacity config. |
| **Batch ETL** | AWS Glue | Dataproc / Dataflow | Glue is PySpark-based; Dataflow is Beam; Dataproc is managed Spark/Hadoop. Dataflow is preferable for unified batch+stream. |
| **Data Warehouse** | Redshift | BigQuery | BigQuery is fully serverless (no cluster management). Redshift requires node/cluster sizing. BQ separates compute from storage natively. BQ has built-in ML (BigQuery ML). |
| **Data Lake** | S3 + AWS Lake Formation | GCS + Dataplex | Lake Formation adds governance on top of S3. Dataplex is a unified data management layer — it federates across GCS, BigQuery, and Vertex AI. |
| **Workflow Orchestration** | AWS Step Functions / MWAA (Airflow) | Cloud Composer (Airflow) | Both are managed Airflow. MWAA is newer and more managed. Cloud Composer has tighter BigQuery + Dataflow integration. |
| **BI / Visualization** | Amazon QuickSight | Looker / Looker Studio | Looker Studio is free (Tableau-lite). Looker is enterprise with semantic layer (LookML). QuickSight is SPICE-cached; BQ+Looker Studio is live SQL. |
| **ML Platform** | SageMaker | Vertex AI | Vertex AI has a more unified pipeline story (Vertex Pipelines ≈ SageMaker Pipelines). Vertex Feature Store is analogous to SageMaker Feature Store. Both support custom containers. |
| **Feature Store** | SageMaker Feature Store | Vertex AI Feature Store | Similar APIs. Vertex is tighter with BigQuery for feature serving. |
| **Model Training** | SageMaker Training Jobs | Vertex AI Training / Custom Jobs | Nearly equivalent. Vertex has better integration with BigQuery datasets. |
| **Data Catalog / Metadata** | AWS Glue Data Catalog | Data Catalog | Data Catalog is standalone; Glue Catalog is embedded in Glue. Data Catalog federates metadata from BigQuery, GCS, Pub/Sub. |
| **Data Governance** | AWS Lake Formation (permissions) | Dataplex | Dataplex is broader — covers data quality, lineage, and policy enforcement across GCS + BQ. Lake Formation focuses on permission governance. |
| **Database Migration** | AWS Database Migration Service (DMS) | Database Migration Service (DMS) / BigQuery Data Transfer | Both have DMS. BigQuery Data Transfer Service handles cloud-to-BQ migrations (S3, Redshift, Teradata, etc.). |
| **Message Queue** | SQS | Pub/Sub (pull mode) | Pub/Sub in pull mode ≈ SQS. Pub/Sub in push mode ≈ SNS → SQS fanout. |
| **Notification / Fan-out** | SNS | Pub/Sub Topics with multiple subscriptions | Conceptually equivalent. Pub/Sub is unified for both notification and queue patterns. |
| **Serverless Functions** | Lambda | Cloud Functions / Cloud Run | Cloud Run is for containerized workloads (≈ Lambda containers). Cloud Functions ≈ Lambda traditional functions. |
| **Container Orchestration** | EKS | GKE (Google Kubernetes Engine) | GKE is the original managed Kubernetes. Both are equivalent for pipeline execution. |
| **Data Transfer / Ingestion** | AWS DataSync | Transfer Service / Storage Transfer Service | Both handle on-prem to cloud and cloud-to-cloud transfer. |
| **IAM / Access Control** | AWS IAM | Cloud IAM | Conceptually equivalent. GCP uses projects/folders/org hierarchy; AWS uses accounts/OUs. GCP IAM is condition-based; AWS IAM is policy-document based. |

---

## Deep Comparisons for Interview D (Most Likely to Come Up)

### BigQuery vs Redshift (the core question)

**Why BigQuery for this scenario:**
- Serverless — no cluster to size, no downtime for scaling. Critical for a 1-year migration where data volumes are unknown.
- Storage + compute are separate billing — cost predictable, no idle cluster cost.
- Native streaming ingest from Pub/Sub (Dataflow → BQ) — both batch and stream land in the same table format.
- BigQuery ML runs demand forecasting in pure SQL — no separate ML cluster, no data movement.
- Multi-brand = multi-dataset — BigQuery's dataset-level IAM maps perfectly to brand isolation.

**When Redshift would win:**
- If the customer already has a Snowflake or Redshift investment and migration cost > benefit
- If the team heavily uses existing Redshift tooling (dbt connectors, BI tools)
- If price performance for single-tenant, high-concurrency workloads is a priority

---

### Pub/Sub vs Kinesis (streaming ingest choice)

**Why Pub/Sub:**
- Serverless — no shard planning. Kinesis requires you to pre-configure shard count = throughput mistakes early in migration.
- Global message routing — all 3 brands can publish from any region; Kinesis is regional by default.
- Exactly-once guarantee at the Dataflow consumer level — Pub/Sub + Dataflow is a proven pair.

**When Kinesis would win:**
- If the customer has existing Kinesis infrastructure and data producers
- If low-latency (<200ms end-to-end) is a hard requirement (Kinesis Enhanced Fan-Out offers lower latency)

---

### Dataflow vs Spark (processing choice)

**Why Dataflow:**
- Unified batch + stream in one framework (Apache Beam) — one codebase for both pipeline types. Critical when you need to migrate batch pipelines to streaming without rewriting.
- Serverless autoscaling — no cluster to manage. During migration, this matters.
- Native GCP integration — Pub/Sub → Dataflow → BigQuery is fully managed.

**When Spark/Dataproc would win:**
- If the team has heavy PySpark investment and many existing Spark jobs to reuse
- For very large-scale ML feature computation where Spark's in-memory model is more efficient

---

### Dataplex vs Custom Governance

**Why Dataplex:**
- Federates governance across GCS + BigQuery in one policy layer — you don't have to build two separate governance systems
- Supports data quality rules (automated row-level checks that run on schedule)
- Data lineage tracking is built in — shows where data came from and how it was transformed
- PII tagging + per-brand access control enforced at the asset level

**When you'd skip Dataplex:**
- Small-scale, single-brand, low-compliance scenario — manual tagging in Data Catalog is sufficient
- If the customer wants a cloud-agnostic governance layer (use open-source alternatives like Apache Atlas)

---

## AWS-Strong Bridging Script (Use This Live)

When Gene probes your GCP knowledge:

> *"On AWS, I'd use [X] for this. On GCP, the equivalent is [Y]. The key architectural difference is [Z] — specifically, [Y] handles [specific aspect] differently because [concrete reason]. In this scenario, I chose [Y] because [customer-specific reason]."*

Example:
> *"On AWS, we'd use Kinesis + Glue for this ingestion pattern. On GCP, I chose Pub/Sub + Dataflow. The key difference is that Dataflow gives us unified batch and streaming in a single Apache Beam framework — so the same code handles our nightly batch loads from each brand AND the real-time POS event stream. That's valuable in a migration context because we don't maintain two codebases."*
