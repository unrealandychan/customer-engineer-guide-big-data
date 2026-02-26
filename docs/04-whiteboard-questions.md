# 🎨 Whiteboard Interview Questions & Detailed Solutions

> Practice each question out loud for 5–10 minutes before checking the solution.  
> These are tuned for a **Google Cloud pre-sales role**: technical depth + business framing.

---

## Q1 — Real-Time Clickstream Analytics Platform

**Prompt:** *"Design a real-time clickstream analytics platform for a web/mobile app on Google Cloud. The business wants near-real-time dashboards (1–5 minute delay) and the ability to run ad-hoc queries on all historical data."*

### What to draw on the whiteboard

```
Users / Mobile App
      ↓
   Pub/Sub  (durable event bus, handles bursts)
      ↓
  Dataflow  (Beam streaming: parse, enrich, window)
    ↙          ↘
 BigQuery      GCS (raw archive)
  (serving)
      ↓
  Looker / BI Dashboards
```

### Step-by-step walkthrough

**1. Clarify first**
- Event volume: thousands/sec? millions/sec?
- Latency target: 1 min? 5 min? (affects windowing strategy)
- Analytics types: fixed dashboards, ad-hoc SQL, ML?

**2. Ingestion — Pub/Sub**
- Apps publish events via HTTPS to backend or directly to Pub/Sub
- Benefits: decouples producers/consumers, durable, handles traffic bursts, built-in replay

**3. Processing — Dataflow (Beam)**
- Streaming Beam pipeline:
  - Source: Pub/Sub subscription
  - Parse JSON, enrich with geo/device metadata, assign event time
  - Windowed aggregations: 1-min tumbling windows per `country`, `campaign_id`
  - Sink 1: aggregated metrics → BigQuery (partitioned table)
  - Sink 2: raw events → GCS (cold archive, Parquet format)
- Alternative: **Spark Structured Streaming on Dataproc** if customer has existing Spark code

**4. Storage — BigQuery**
- Raw events table: `PARTITION BY event_date CLUSTER BY user_id, session_id`
- Aggregated metrics table: per-minute/hour rollups (pre-computed for dashboards)
- Analysts query with standard SQL — both fresh (minutes old) and historical (years)

**5. BI & Dashboards**
- Looker or Looker Studio connected to BigQuery
- Near-real-time: dashboards query the streaming-updated BigQuery table

**6. Cost controls**
- Pub/Sub: pay per message volume
- Dataflow: serverless auto-scaling — pay only for active workers
- BigQuery: partition+cluster to reduce scan; materialized views for dashboard queries; flat-rate slots if steady traffic

**7. Security**
- IAM service accounts for Dataflow → BigQuery and Pub/Sub → Dataflow
- Column-level security for any PII in BigQuery
- VPC Service Controls if strict data perimeter needed

### How to handle pushback

| Pushback | Response |
|---------|---------|
| "Why not just use GA4 + Looker Studio?" | GA4 is web-only. BigQuery lets you unify clickstream + CRM + transactional data for deeper attribution and LTV analysis |
| "Why Dataflow vs Spark Structured Streaming?" | Dataflow is serverless — no cluster sizing or ops. If they have Spark code to reuse, Dataproc is a valid alternative, both land in BigQuery |
| "How do we handle late events?" | Beam watermarks + allowed lateness — define how long to wait (e.g., 10 min) before closing a window; BigQuery handles corrections via MERGE |

---

## Q2 — Batch ETL: On-Prem Database to BigQuery

**Prompt:** *"A customer has a large on-prem relational database (Oracle/MySQL). They want daily refreshed analytics in BigQuery. Design the pipeline."*

### What to draw

```
On-Prem DB (Oracle/MySQL)
      ↓ (VPN or Interconnect)
  Datastream (CDC)  OR  nightly export to GCS
      ↓
  GCS (raw zone — immutable, partitioned by date)
      ↓
  Option A: Load → BigQuery staging → dbt/SQL transforms → analytics tables
  Option B: Dataproc Spark or Dataflow → transform → write to BigQuery
      ↓
  BigQuery (star schema: facts + dimensions)
      ↓
  Looker / BI tools
```

### Step-by-step walkthrough

**1. Clarify**
- Data size, update pattern (CDC vs full nightly dump)?
- Can they install an agent on-prem? VPN or Dedicated Interconnect available?
- Acceptable latency: daily is fine? Hourly?

**2. Ingestion options**
- **CDC with Datastream:** continuous replication into GCS or BigQuery — lower latency, more complex
- **Nightly batch export:** simpler, extract CSV/Avro/Parquet → push to GCS via Cloud Storage Transfer Service or scripts

**3. GCS as raw zone**
- Store all files before loading: `gs://bucket/raw/orders/2026-02-26/`
- Benefits: audit trail, replay capability, vendor-neutral format

**4. Transformation (choose based on complexity)**
- **ELT in BigQuery (preferred for SQL-friendly transforms):**
  - Load raw data to BigQuery staging tables
  - Use scheduled SQL queries or dbt models to transform to clean star schema
  - Simpler to operate, fully serverless
- **ETL with Dataproc or Dataflow (for complex logic):**
  - Spark/Beam job reads from GCS, applies complex transforms, writes to BigQuery
  - Use when: joins with large external data, custom UDFs, existing Spark code

**5. BigQuery modeling**
- Large fact tables: `PARTITION BY order_date CLUSTER BY customer_id, region`
- Dimension tables: unpartitioned (usually small), possibly clustered
- Incremental loads: process only new/changed data — avoid full reloads

**6. Orchestration**
- Cloud Composer (Airflow): `ingest_job → validate → transform → notify`
- Or: BigQuery scheduled queries for simple ELT-only pipelines

**7. Trade-off to articulate**
> "For SQL-friendly transforms, ELT in BigQuery is simpler and serverless. If transforms are complex or rely on Spark libraries, we use Dataproc for ETL before loading. Over time, we try to push more logic into BigQuery to reduce operational components."

---

## Q3 — Migrate On-Prem Hadoop/Spark to GCP

**Prompt:** *"A customer has an on-prem Hadoop/Spark cluster running nightly ETL and some ad-hoc analytics. They want to migrate to GCP, reduce operational overhead, and modernize over time."*

### What to draw

```
PHASE 1 — Lift & Shift
On-prem Hadoop/HDFS  →  Dataproc + Cloud Storage
(same Spark code, minimal changes)

PHASE 2 — Modernize
Dataproc jobs  →  Dataflow (serverless, new pipelines)
Spark analytics  →  BigQuery (SQL-based analytics)
HDFS/GCS  →  BigLake / BigQuery external tables
```

### Step-by-step walkthrough

**Phase 1 — Lift & Shift (Months 1–3)**
- Replace on-prem cluster with Dataproc on GCE
- Replace HDFS with Cloud Storage (HCFS-compatible — minimal code changes)
- Reuse all existing Spark, Hive, Pig jobs
- Use ephemeral clusters for batch (spin up → run → tear down)
- Add preemptible workers + autoscaling → immediate cost savings

**Phase 2 — Modernize (Months 3–12)**
- Move curated datasets from GCS into BigQuery
- Refactor new pipelines as Dataflow (Beam) — serverless, no cluster ops
- Shift BI/analytical queries to BigQuery — cheaper and simpler than Spark
- Introduce Cloud Composer for orchestration
- Add Data Catalog / Dataplex for governance as environment grows

**Cost story:**
- Phase 1: 50%+ TCO reduction vs on-prem (no hardware lifecycle, per-second billing, preemptibles)
- Phase 2: additional savings from moving analytics to serverless BigQuery

**Migration risk mitigation:**
- Run parallel: validate Dataproc results match on-prem for 2–4 weeks before cutover
- Migrate one workload at a time, not big-bang

### How to talk about it in pre-sales style

> "Short-term: preserve your Spark investment, reduce ops and hardware costs with Dataproc. Medium-term: modernize net-new pipelines with Dataflow and BigQuery. Long-term: fewer clusters, more serverless, lower TCO and faster time to insight."

---

## Q4 — BigQuery Cost is "Too High" — Optimization Whiteboard

**Prompt:** *"A customer complains their BigQuery bill is too high. They have a large event fact table and many dashboard queries. How do you diagnose and optimize?"*

### What to draw

```
Current state:
events table (unpartitioned, 50TB)
      ↓
SELECT * ... WHERE user_id = ...  [scans 50TB every time]
      ↓
Cost = $250/query on-demand

Optimized state:
events table
  PARTITION BY event_date
  CLUSTER BY user_id, country
      ↓
SELECT specific cols WHERE event_date > ... AND user_id = ...
      ↓
Scans = 2GB  →  Cost = $0.01/query
```

### Step-by-step walkthrough

**1. Diagnose first (show you don't just guess)**
- Export billing to BigQuery → identify top-cost projects/datasets
- Query `INFORMATION_SCHEMA.JOBS_BY_PROJECT` → find top-cost queries and who runs them
- Often: 2–3 queries on 1–2 tables drive 80% of spend

**2. Table-level fixes**
- Add `PARTITION BY event_date` to large fact tables
- Add `CLUSTER BY user_id, country` (or most-queried dimensions)
- Set `require_partition_filter = TRUE` to prevent accidental full scans
- Migrate from date-sharded tables (`events_20250101`) to single partitioned table
- Add partition expiration for old data

**3. Query-level fixes**
- Replace `SELECT *` with explicit columns
- Add partition filter to every query on large tables
- Replace repeated heavy aggregations with materialized views or pre-aggregated summary tables
- Adopt incremental ETL models — only process new data

**4. Pricing fixes (if sustained heavy usage)**
- Evaluate flat-rate slots for predictable workloads
- Separate reservations for batch ETL vs interactive BI queries

**5. Governance**
- Set budget alerts per project/team
- Use BigQuery Recommender — analyses 30 days of queries → recommends partition/cluster changes with $ savings estimates
- Run analyst education sessions on query best practices

**Expected outcome to quote:**
> "Customers routinely see 50–80% cost reduction on their heaviest workloads after partitioning, clustering, and query hygiene improvements."

---

## Q5 — Near-Real-Time Fraud Detection

**Prompt:** *"Design a system on GCP that detects potentially fraudulent transactions in near real-time and flags them for review."*

### What to draw

```
Payment App (worldwide)
      ↓
   Pub/Sub  (transaction events: user, amount, merchant, geo, timestamp)
      ↓
  Dataflow (Beam)
    - Parse + validate event
    - Enrich: look up user risk score from Bigtable (low latency KV)
    - Call Vertex AI scoring endpoint (ML model: fraud probability)
    - Route:
        score > 0.8  →  "suspicious" Pub/Sub topic  →  alert / case mgmt
        all events   →  BigQuery (transactions + fraud_score column)
      ↓                              ↓
  Alert / Block             BigQuery Analytics
  (Firestore/Redis)         (analysts review, retrain model)
```

### Step-by-step walkthrough

**1. Clarify**
- Required latency: seconds or sub-second? (affects enrichment strategy)
- Peak TPS?
- Rules-based, ML, or hybrid model?

**2. Ingestion — Pub/Sub**
- Apps publish transaction events globally to Pub/Sub
- Durable, handles global bursts, retries

**3. Streaming processing — Dataflow**
- Beam pipeline reads from Pub/Sub
- Enriches each transaction with user/merchant risk features:
  - Fast lookup from **Bigtable** (user profile, velocity counts, recent history)
- Calls **Vertex AI** scoring endpoint for fraud probability
- Routing:
  - High score → write to alert Pub/Sub topic → case management system
  - All events → BigQuery for full audit trail and analytics

**4. Model training — BigQuery ML / Vertex AI**
- Historical transactions in BigQuery (labeled by outcome — fraud / not fraud)
- Train model via BigQuery ML (SQL-based, simple) or Vertex AI (more powerful)
- Re-train periodically as patterns evolve

**5. Analytics — BigQuery**
- Analysts query transactions + fraud scores for false positive review
- Partition by `txn_date`, cluster by `user_id`, `merchant_id`
- Build dashboards: fraud rate by geography, merchant category, time-of-day

**6. Trade-offs to articulate**
> "This design separates online decisioning (streaming pipeline + low-latency ML) from offline analytics (BigQuery). Fully managed components — Pub/Sub, Dataflow, Vertex AI — minimize ops. It scales globally with predictable latency."

---

## Q6 — Choose: Dataproc vs Dataflow vs BigQuery for ETL

**Prompt:** *"A customer wants to build a new hourly pipeline: ingest CSV files from GCS, transform them, load to a warehouse. How do you choose between Dataproc, Dataflow, or pure BigQuery SQL?"*

### What to draw

Three options side by side:

```
Option A: BigQuery ELT (SQL-only)
GCS files → BQ load job → staging table → dbt/SQL transforms → analytics tables

Option B: Dataflow (Beam)
GCS files → Dataflow pipeline → transform → write to BigQuery

Option C: Dataproc (Spark)
GCS files → Dataproc Spark job → transform → write to BigQuery
```

### Decision framework

| Question | Points to Option... |
|----------|---------------------|
| Are transforms SQL-friendly (joins, filters, aggregations)? | BigQuery ELT |
| Does the team know SQL and want minimal ops? | BigQuery ELT |
| Do you need the same code to run batch AND streaming? | Dataflow (Beam) |
| Do you want fully managed, no-cluster pipeline infra? | Dataflow |
| Does the customer have existing Spark code or skills? | Dataproc |
| Are there complex transforms needing custom Spark libs? | Dataproc |
| Is this a new greenfield pipeline, cloud-native? | Dataflow (first choice) |

### How to articulate the decision in the interview

> "If the work is SQL-friendly and the team is warehouse-centric, I'd lean strongly toward BigQuery-native ELT — it's serverless, simple to operate, and analysts can read and maintain the SQL.
>
> If they need cloud-native pipelines with flexible batch/stream semantics and no cluster management, Dataflow/Beam is the right fit.
>
> If they have existing Spark assets or need custom Spark libraries, Dataproc is the easiest migration path with managed clusters.
>
> In practice, many customers combine them: Dataproc for legacy Spark ETL, BigQuery ELT for new analytical transforms, and Dataflow for any new streaming needs."

---

## 🧩 Quick-Reference: Key Trade-Off Summary

| Dimension | BigQuery | Dataflow | Dataproc |
|-----------|----------|----------|----------|
| Managed level | Fully serverless | Serverless | Managed clusters |
| Primary language | SQL | Java/Python (Beam) | Python/Scala/Java (Spark) |
| Best for | SQL analytics, BI, warehousing | New streaming/batch pipelines | Existing Spark/Hadoop workloads |
| Cluster ops | None | None | Minimal (autoscaling helps) |
| Streaming | Via Pub/Sub + Dataflow sink | Native (Beam) | Spark Structured Streaming |
| Cost model | Per TB scanned or slots | Per worker-hour (auto-scales) | Per VM-hour (per second) |
| Learning curve for team | Low (SQL) | Medium (Beam) | Low if Spark experience |
