# 🔍 Gap Topics — Quick Reference for Interview

> These topics weren't in the original source material but are commonly tested in Google pre-sales interviews.
> Each section: 1-line pitch → technical depth → trade-offs → when it comes up.

---

## 1. BigQuery Storage Write API (High Priority 🔴)

### What it is
The **production-grade way to stream data into BigQuery** — replaced the legacy Streaming Inserts API for high-throughput workloads.

### Pre-sales pitch
> "For high-volume real-time ingestion, we recommend the Storage Write API over legacy streaming inserts. It gives you exactly-once semantics, up to 10x higher throughput, and significantly lower cost — it's billed per byte written, not per row."

### Technical depth

| Feature | Legacy Streaming Inserts | Storage Write API |
|---|---|---|
| Delivery guarantee | At-least-once | **Exactly-once** (committed stream) |
| Max throughput | ~1 GB/s per table | ~3–10 GB/s per table |
| Cost | $0.01 per 200 MB | **$0.025 per GB** (cheaper at scale) |
| Deduplication | None (client must handle) | Built-in (committed mode) |
| Best for | Simple, low-volume | Production pipelines |

### Three modes to know

| Mode | Guarantee | Use case |
|---|---|---|
| **Default stream** | At-least-once | Simplest — backward compat with streaming inserts |
| **Committed stream** | Exactly-once | Production pipelines, financial data |
| **Pending stream** | Exactly-once + atomic batch | Load large batches atomically (like a transaction) |

### When the interviewer asks
- *"How do you ensure no duplicate events in BigQuery?"* → Storage Write API committed stream
- *"We need exactly-once end-to-end from Pub/Sub to BigQuery"* → Pub/Sub → Dataflow → Storage Write API

---

## 2. Materialized Views & BI Engine

### Materialized Views

**What it is:** A pre-computed view that BigQuery refreshes automatically. Queries hitting the MV avoid re-scanning the base table.

**Pre-sales pitch:**
> "For dashboards that run the same expensive aggregations repeatedly, materialized views cut query costs and latency dramatically — often 10–100x — because BigQuery serves results from pre-computed storage, not from scanning the raw table."

**Key facts:**
- Auto-refreshed when base table changes (incremental, not full re-scan)
- Smart matching: BQ rewrites queries transparently to use the MV even if the query references the base table
- Max staleness: configurable (e.g., allow up to 30 min stale data for cost savings)
- Cost: storage for MV + refresh compute; query reads from MV = much less scan

```sql
CREATE MATERIALIZED VIEW dataset.daily_revenue AS
SELECT
  DATE(event_time) AS day,
  country,
  SUM(amount)      AS total_revenue
FROM dataset.events
GROUP BY 1, 2;
-- BigQuery auto-refreshes this when `events` is updated
```

### BI Engine

**What it is:** In-memory analysis layer that sits between BigQuery and BI tools (Looker, Looker Studio, Tableau). Speeds up dashboard queries to sub-second.

**Pre-sales pitch:**
> "BI Engine is Google's in-memory acceleration layer for BigQuery. It caches frequently-accessed data in RAM on the same infrastructure, so dashboard queries go from seconds to milliseconds — without changing any SQL or BI tool configuration."

**Key facts:**
- Priced per GB of reserved RAM ($0.04/GB/hour) — predictable cost for dashboard workloads
- Transparent: BI tools don't need changes; BQ decides what to cache
- Best for: fixed dashboards, Looker Studio reports, < 100 GB hot dataset
- Not for: ad-hoc queries over full tables (use slots/flat-rate instead)

**When to recommend:**
- Customer says dashboards are slow → BI Engine
- Customer runs repeated aggregations in dashboards → Materialized Views
- Both are complementary; use both for high-traffic dashboards

---

## 3. Dataplex & Data Catalog (Governance Story)

### Why it matters in pre-sales
Enterprise customers always ask: *"How do we govern data at scale? Who can see what? How do we know where data came from?"*

### Dataplex

**What it is:** Google's **unified data governance and management platform**. Organizes data lakes across GCS, BigQuery, and other storage into logical domains with automated metadata, quality checks, and access control.

**Pre-sales pitch:**
> "Dataplex lets customers centrally manage, monitor, and govern all their data — across GCS data lakes and BigQuery warehouses — without moving it. It gives data stewards a single control plane for access policies, data quality rules, and lineage tracking."

**Key capabilities:**
- **Data Zones:** organize buckets/datasets into logical domains (raw → curated → processed)
- **Auto-discovery:** scans GCS and BQ, infers schemas, registers in Data Catalog automatically
- **Data Quality:** define SQL-based quality rules; runs on a schedule; triggers alerts
- **Lineage:** track which pipeline produced which table (integrates with Dataflow, BQ)
- **IAM integration:** apply fine-grained access policies at the Dataplex lake level

### Data Catalog

**What it is:** Enterprise **metadata management and data discovery** service.

**Pre-sales pitch:**
> "Data Catalog is like Google Search for your enterprise data. Analysts can find datasets across BigQuery, GCS, and other sources, see schemas and sample data, and understand who owns it and what it means — all without asking an engineer."

**Key capabilities:**
- Unified search across all GCP data assets
- Business glossary: link technical columns to business terms (e.g., "MRR" → `sum(subscription_amount)`)
- Policy tags: tag columns for sensitivity → automatically enforces column-level masking in BigQuery
- Lineage: see upstream/downstream dependencies for any table

### The governance answer framework
When asked "how do you handle data governance on GCP?":
```
1. Dataplex   → organize and govern the data lake (GCS + BQ)
2. Data Catalog → discover, document, and search all data assets
3. Policy Tags  → column-level security in BigQuery (PII masking, access control)
4. VPC Service Controls → network-level perimeter (no data leaves the org)
5. Audit Logs  → every BigQuery query logged to Cloud Audit Logs → BigQuery / SIEM
```

---

## 4. Cloud Composer (Airflow on GCP)

### What it is
**Managed Apache Airflow** — orchestrates complex multi-step data pipelines with dependencies, scheduling, retries, and monitoring.

### Pre-sales pitch
> "Cloud Composer gives you managed Airflow without the operational burden of running it yourself. It orchestrates your full data pipeline: trigger a Dataproc job, wait for it to finish, run a BQ transformation, then notify Slack if anything fails — all defined as code."

### When to use Composer vs alternatives

| Scenario | Tool |
|---|---|
| Simple, linear pipeline (one step) | Dataflow / Dataproc alone |
| Multi-step pipeline with dependencies | **Cloud Composer** |
| Event-driven trigger (new file in GCS) | Eventarc + Cloud Functions |
| Real-time streaming | Dataflow (not Composer) |
| Fully managed, no-code ETL | Cloud Data Fusion |

### Key concepts
- **DAG (Directed Acyclic Graph):** the pipeline definition in Python — tasks and their dependencies
- **Operator:** one step in a DAG (e.g., `DataprocSubmitJobOperator`, `BigQueryInsertJobOperator`)
- **Scheduler:** triggers DAG runs on schedule or on-demand
- GCP-native operators for BQ, Dataproc, GCS, Pub/Sub built-in — no custom code needed

### Common interview pattern
*"How do you orchestrate a pipeline that: loads raw data from GCS → runs a Dataproc Spark job → runs a BQ transformation → exports results to GCS?"*
→ Answer: **Cloud Composer DAG** with one operator per step, dependencies defined in the DAG

---

## 5. BigQuery Omni — Cross-Cloud Analytics

### What it is
**BigQuery running in AWS or Azure** — lets you query data in S3 or Azure Data Lake with BigQuery SQL, without moving the data to GCP.

### Pre-sales pitch (key differentiator)
> "BigQuery Omni is a unique capability — it lets customers run BigQuery SQL directly on data sitting in S3 or Azure Blob Storage, without copying it to GCP. This is huge for customers who have data residency requirements, existing AWS/Azure investments, or who aren't ready to move everything to GCP. They get Google's analytics power while the data stays where it is."

### Technical depth
- Uses **Anthos** (Google's multi-cloud infrastructure) to run BQ compute nodes in AWS/Azure regions
- Governed by **BigQuery Omni connections** — cross-region query is billed separately
- Same BigQuery SQL, same IAM, same Looker integration — unified experience
- Typical use case: data in S3 owned by one team, merged with GCP data owned by another → single BQ query

### When it wins deals
- Customer says: *"We can't move our data out of AWS due to contracts/residency"* → BigQuery Omni
- Customer is multi-cloud and wants one analytics layer → BigQuery Omni as the unified query engine
- AWS customer evaluating GCP: low-risk way to try BQ without full migration

---

## 6. Vertex AI & BigQuery ML (The AI Story)

### Why it matters
Every pre-sales conversation eventually lands on AI. You need a crisp answer to: *"What can we do with data once it's in BigQuery?"*

### BigQuery ML (BQML)

**What it is:** Run ML model training and inference directly in BigQuery **using SQL** — no data movement, no Python environment.

**Pre-sales pitch:**
> "BigQuery ML lets data analysts build and deploy ML models using SQL they already know — no Python, no data export, no separate ML infrastructure. For common use cases like churn prediction, demand forecasting, or recommendation scoring, a data analyst can go from raw data to deployed model in hours instead of weeks."

**Supported models (know at least these):**
| Model type | SQL syntax |
|---|---|
| Linear/logistic regression | `CREATE MODEL ... OPTIONS(model_type='logistic_reg')` |
| K-means clustering | `model_type='kmeans'` |
| Time series forecasting | `model_type='arima_plus'` |
| Import TensorFlow model | `model_type='tensorflow'` |
| LLM (Gemini) inference | `ML.GENERATE_TEXT()` |

### Vertex AI

**What it is:** Google's **unified ML platform** for the full ML lifecycle — from data prep to model training, deployment, and monitoring.

**Pre-sales pitch:**
> "Vertex AI is Google's end-to-end ML platform. It integrates directly with BigQuery: data stays in BQ, models train on Vertex, predictions flow back to BQ. Customers get managed notebooks, AutoML for no-code model building, and a model registry with one-click deployment to a REST endpoint."

### The AI pipeline story (memorize this flow)
```
BigQuery (data) → Vertex AI Feature Store (feature engineering)
                → Vertex AI Training (train model)
                → Vertex AI Model Registry (version + deploy)
                → Vertex AI Endpoints (real-time serving)
                → Predictions back to BigQuery (for analysis)
```

### Gemini in BigQuery (latest, 2025+)
- **Gemini in BigQuery:** natural language → SQL (analysts ask questions in English)
- **ML.GENERATE_TEXT():** call Gemini from SQL to classify, summarize, or extract from text columns
- **Data Canvas:** visual, AI-assisted data exploration

**One-liner for interviews:** *"With Gemini in BigQuery, an analyst can type 'show me last quarter's top customers by revenue' and BQ generates the SQL automatically — no SQL knowledge required."*

---

## 7. GCP Security & Compliance Cheat Sheet

### IAM Hierarchy (know this cold)
```
Organization
  └── Folders (business units / environments)
        └── Projects
              └── Resources (BQ datasets, GCS buckets, etc.)
```
- Permissions are **inherited downward** — org-level IAM applies to all resources
- **Principle of least privilege:** grant the lowest role that enables the task

### BigQuery-specific security
| Control | What it does |
|---|---|
| Dataset IAM | Who can read/write/admin a dataset |
| Row-level security | Filter rows per user/group (`CREATE ROW ACCESS POLICY`) |
| Column-level security | Mask/restrict columns via Policy Tags + Data Catalog |
| Authorized views | Share query results without exposing source tables |
| VPC Service Controls | Network perimeter — prevents data exfiltration even with valid IAM |

### Compliance one-liners
- **GDPR/right to erasure:** use partition expiration + DML `DELETE` to purge specific user data
- **PCI-DSS:** column-level security on card numbers, VPC-SC, CMEK for encryption keys
- **HIPAA:** BQ is HIPAA-eligible — sign BAA with Google; use CMEK + audit logs

---

## Quick Recall: Key Numbers for the Interview

| Metric | Value |
|---|---|
| BigQuery on-demand price | $6.25 / TB scanned |
| BigQuery storage (active) | $0.02 / GB / month |
| BigQuery storage (long-term, 90 days) | $0.01 / GB / month |
| Pub/Sub price | $0.04 / GB |
| Dataproc preemptible discount | ~60–80% cheaper than standard VMs |
| Storage Write API vs streaming inserts | ~10x higher throughput, ~50% lower cost |
| Dataplex data quality | SLA-able rules, automated scans, alerting |
| BigQuery max partitions per table | 10,000 |
| BigQuery max clustering columns | 4 |
| BigQuery slot (1 slot) | 1 virtual CPU of BigQuery compute |
| BigQuery flat-rate minimum | 100 slots ($2,000/month) |
