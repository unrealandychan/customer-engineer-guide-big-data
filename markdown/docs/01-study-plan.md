# 📅 10-Day Study Plan — Google Pre-Sales Interview (GCP Data & Analytics)

> **Interview date:** Adjust from today (February 26, 2026)  
> **Daily commitment:** 2–4 focused hours  
> **Role:** Pre-Sales Engineer — BigQuery · Dataproc · GCP Data Stack

---

## 🗓️ Overview

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 1 | GCP Data Landscape + Environment Setup | Personal cheat sheet: AWS → GCP map |
| Day 2 | BigQuery Fundamentals + SQL | Run hands-on queries, prep 3 verbal answers |
| Day 3 | BigQuery: Storage Design, Cost & Security | Schema design answer ready |
| Day 4 | Dataproc Deep Dive | Spark job submitted, Dataproc vs BQ answer ready |
| Day 5 | Dataflow, Streaming & Orchestration | Streaming pipeline design ready |
| Day 6 | End-to-End Pipeline Design (Whiteboarding) | 2–3 architectures verbalized at whiteboard speed |
| Day 7 | Advanced BigQuery, AI & Governance | AI functions and Dataplex concepts mastered |
| Day 8 | Databases, BI & Competitive Intelligence | Spanner, Looker, and Snowflake/Databricks positioning |
| Day 9 | Soft Skills & Objection Handling | Objection responses polished, STAR stories locked in |
| Day 10 | Mock Interview + Final Polish | Full mock run, review cheat sheets |

---

## Day 1 — GCP Data Landscape + Setup

**Goal:** Build a mental map of GCP. Don't go deep — go wide.

### Study Tasks

- [ ] Read the [GCP data products overview](https://cloud.google.com/products/databases)
- [ ] Write a one-liner for each: BigQuery, Dataproc, Dataflow, Pub/Sub, Composer, Dataplex, Data Fusion, Datastream
- [ ] Create a GCP free project (or verify existing):
  - Enable BigQuery API
  - Enable Dataproc API
- [ ] Build your AWS → GCP mental map (use the table in `00-guideline.md`)

### Verbal Practice

Prepare a 1-sentence answer for:
- "What is BigQuery?"
- "What is Dataproc?"
- "What makes GCP data different from AWS?"

### Deliverable

One page of personal notes: **GCP data stack vs AWS equivalents**

---

## Day 2 — BigQuery Fundamentals + SQL

**Goal:** Get comfortable with BigQuery architecture and SQL dialect.

### Study Tasks

- [ ] Read [BigQuery overview docs](https://cloud.google.com/bigquery/docs/introduction)
- [ ] Open the BigQuery console and:
  - [ ] Explore `bigquery-public-data.samples` dataset
  - [ ] Write and run:
    - A simple `SELECT` with `WHERE` and `GROUP BY`
    - A `JOIN` across two tables
    - A window function: `ROW_NUMBER()`, `SUM() OVER (PARTITION BY ...)`
  - [ ] Note "bytes processed" — experiment by reducing selected columns
- [ ] Optional: skim BigQuery client library for Python or Node.js

### Key Concepts to Understand

- How BigQuery executes a query (distributed, columnar, slots, serverless)
- Why BigQuery is different from a traditional RDBMS
- What are "slots" and how they relate to performance

### Verbal Practice

- "Explain BigQuery to an engineer who only knows PostgreSQL."
- "How is BigQuery's pricing different from a traditional warehouse?"

---

## Day 3 — BigQuery: Storage Design, Partitioning, Clustering & Security

**Goal:** Know how to design schemas for performance and cost. This is a very common interview topic.

### Study Tasks

- [ ] Read docs: [Partitioned tables](https://cloud.google.com/bigquery/docs/partitioned-tables) and [Clustering](https://cloud.google.com/bigquery/docs/clustered-tables)
- [ ] Hands-on in BigQuery console:
  - [ ] Create a table from a GCS CSV/JSON file
  - [ ] Create a date-partitioned table
  - [ ] Create a partitioned + clustered table
  - [ ] Run queries and compare **bytes processed** with vs without filters
- [ ] Review: dataset-level IAM, table-level IAM, row-level + column-level security concepts
- [ ] Read the BigQuery [pricing page](https://cloud.google.com/bigquery/pricing)

### Key Concepts to Understand

| Concept | Detail |
|---------|--------|
| Partitioning | Split table by date/timestamp/integer — enables partition pruning |
| Clustering | Sort within partition by up to 4 columns — enables block pruning |
| On-demand pricing | Pay per TB scanned — optimize by scanning less |
| Flat-rate pricing | Buy slots — predictable cost for heavy workloads |
| `require_partition_filter` | Forces queries to always filter by partition — prevents full scans |
| Partition expiration | Auto-delete old partitions — lifecycle management |

### Verbal Practice

- "How would you design a BigQuery schema for a large event log table?"
- "How do you reduce query cost on a very large table?"
- "What's the difference between partitioning and clustering?"

---

## Day 4 — Dataproc Deep Dive

**Goal:** Understand managed Hadoop/Spark and when to use it vs BigQuery.

### Study Tasks

- [ ] Read [Dataproc overview docs](https://cloud.google.com/dataproc/docs/concepts/overview)
- [ ] Read `12-dataproc-from-scratch.md` and `dataproc-course/` materials
- [ ] Hands-on in GCP console:
  - [ ] Create a small Dataproc cluster
  - [ ] Submit a simple PySpark job (e.g., word count or read from GCS)
  - [ ] Delete the cluster
- [ ] Understand ephemeral clusters and preemptible workers for cost savings

### Key Concepts to Understand

- Lift-and-shift vs cloud-native Spark
- Decoupling compute and storage (using GCS instead of HDFS)
- Dataproc vs Dataflow vs BigQuery trade-offs

### Verbal Practice

- "When should a customer use Dataproc instead of BigQuery?"
- "How does Dataproc save money compared to on-prem Hadoop?"

---

## Day 5 — Dataflow, Streaming & Orchestration

**Goal:** Master the streaming story and how pipelines are scheduled.

### Study Tasks

- [ ] Read `05-streaming-analytics.md` and `dataflow-beam-course/` materials
- [ ] Read `16-ingestion-and-orchestration.md` (Datastream, Composer, Data Fusion)
- [ ] Understand the difference between Pub/Sub (messaging) and Dataflow (processing)
- [ ] Review Apache Beam concepts (PCollections, Transforms, Windowing)

### Key Concepts to Understand

- Exactly-once processing in Dataflow
- Event time vs Processing time
- When to use Cloud Composer (Airflow) vs Cloud Workflows

### Verbal Practice

- "Explain the difference between Pub/Sub and Dataflow."
- "How would you architect a real-time CDC pipeline from an on-prem Oracle database to BigQuery?"

---

## Day 6 — End-to-End Pipeline Design (Whiteboarding)

**Goal:** Connect the pieces. Be able to draw and explain architectures.

### Study Tasks

- [ ] Read `04-whiteboard-questions.md`
- [ ] Practice drawing architectures on a real whiteboard or paper
- [ ] Focus on the "Golden Paths":
  - Batch: GCS → Dataflow/Dataproc → BigQuery
  - Streaming: Pub/Sub → Dataflow → BigQuery
  - CDC: Datastream → GCS → Dataflow → BigQuery

### Key Concepts to Understand

- Where does the data land? (Usually GCS)
- Where is it transformed? (Dataflow, Dataproc, or BigQuery via dbt)
- Where is it served? (BigQuery, Bigtable, Spanner)

### Verbal Practice

- "Draw a real-time fraud detection pipeline."
- "Draw a nightly batch ETL pipeline from 3 different SaaS sources."

---

## Day 7 — Advanced BigQuery, AI & Governance

**Goal:** Learn the 2026 differentiators that win deals.

### Study Tasks

- [ ] Read `09-big-data-topics-2026.md` (Editions, Global Queries)
- [ ] Read `19-vertex-ai-bqml-mlops.md` (BQML, Vertex AI, GenAI)
- [ ] Read `14-data-governance.md` (Dataplex, Data Catalog)
- [ ] Hands-on: Try a simple BQML model or `ML.GENERATE_TEXT` if you have access

### Key Concepts to Understand

- BigQuery Editions (Standard, Enterprise, Enterprise Plus)
- Training ML models using SQL (BQML)
- Centralized governance with Dataplex

### Verbal Practice

- "How does BigQuery integrate with Vertex AI?"
- "A customer is worried about PII data across 100 datasets. How does Dataplex help?"

---

## Day 8 — Databases, BI & Competitive Intelligence

**Goal:** Defend the edges of the data warehouse and position against competitors.

### Study Tasks

- [ ] Read `18-alloydb-and-spanner.md` (HTAP, Global consistency)
- [ ] Read `17-looker-and-bi.md` (Semantic Layer, In-Database Architecture)
- [ ] Read `15-competitive-intelligence.md` (Snowflake, Databricks, Redshift)
- [ ] Read `08-business-case-tco.md` (TCO framing)

### Key Concepts to Understand

- AlloyDB's columnar engine (HTAP)
- Looker's LookML vs PowerBI extracts
- BigQuery's serverless advantage vs Snowflake's virtual warehouses

### Verbal Practice

- "Why should we buy Looker if we already have PowerBI?"
- "We are evaluating Snowflake and BigQuery. Why should we choose Google?"

---

## Day 9 — Soft Skills & Objection Handling

**Goal:** Sound like a trusted advisor, not a feature-pusher.

### Study Tasks

- [ ] Read `soft-skills/01-pushback-handling.md` and `03-objection-handling.md`
- [ ] Read `soft-skills/02-discovery-conversation.md` (SPIN framework)
- [ ] Read `07-star-stories-template.md` and draft 3 personal stories
- [ ] Practice the VERA framework (Validate, Explore, Reframe, Answer)

### Key Concepts to Understand

- The "Doctor not Salesperson" mindset
- Uncovering the *business* problem behind the technical question

### Verbal Practice

- "BigQuery is too expensive. We want to build our own Hadoop cluster." (Handle the objection)
- "Tell me about a time you designed a complex data architecture." (STAR story)

---

## Day 10 — Mock Interview + Final Polish

**Goal:** Put it all together under pressure.

### Study Tasks

- [ ] Run a full 45-minute mock interview (use `soft-skills/06-roleplay-scripts.md`)
- [ ] Record yourself answering 3 technical questions and 1 behavioral question. Watch it back.
- [ ] Review your 1-page cheat sheet
- [ ] Rest and hydrate

### Final Checklist

- [ ] I can explain BigQuery, Dataproc, and Dataflow in 30 seconds each.
- [ ] I can draw a batch and streaming pipeline.
- [ ] I have 3 STAR stories ready.
- [ ] I know how to handle the "Snowflake is better" objection.
