# 🌊 Big Data Topics 2026 — What's New & What to Know

> **Source:** Google Cloud Blog (Feb 2026), Google Research, GCP official docs  
> **Purpose:** Cover the latest topics HR/interviewers specifically flag in 2025–2026 interview cycles

---

## 1. BigQuery Editions (Replaces Old Flat-Rate vs On-Demand)

> ⚠️ **This is a 2023–2024 shift that many candidates still get wrong. Know it cold.**

### The Four Tiers

| Edition | Pricing Model | Key Differentiator | SLO |
|---------|--------------|-------------------|-----|
| **Standard** | Slot-hours (autoscaling only, max 1,600 slots) | Entry-level capacity; no BI Engine, no BQML | 99.9% |
| **Enterprise** | Slot-hours (autoscaling + baseline) | BI Engine, BQML, CMEK, VPC-SC, continuous queries | 99.99% |
| **Enterprise Plus** | Slot-hours (autoscaling + baseline) | Adds Assured Workloads (FedRAMP/CJIS/IL4/ITAR), managed DR, cross-region export | 99.99% |
| **On-Demand** | Per TiB processed ($6.25/TiB) | No reservations; free 1 TB/month; best for exploratory/dev | 99.99% |

### Key Edition Facts to Cite

- Standard: autoscaling **only** — no baseline slots, max 1,600 slots per reservation
- Enterprise: unlocks **continuous queries** (streaming SQL), **BQML**, **BI Engine**, **vector indexes**, **BigQuery Omni**
- Enterprise Plus: adds **Assured Workloads** compliance controls (ITAR, FedRAMP High), **managed disaster recovery**
- Commitments still available on Enterprise/Enterprise+: **1-yr = 20% discount**, **3-yr = 40% discount**
- Cross-user caching: Enterprise/Enterprise+ only (Standard = single-user only)

### Pre-Sales Pitch

> "BigQuery editions give you a single platform that scales from ad-hoc exploration on on-demand pricing, all the way up to compliance-grade regulated workloads with Enterprise Plus — you don't need to run two different data warehouses for your regulated and non-regulated workloads."

---

## 2. BigQuery Global Queries (Preview — Feb 2026)

> **Hot topic**: announced February 18, 2026. Almost certainly to come up.

### What It Is

Query data stored in **different geographic regions with a single SQL statement** — no ETL pipeline required.

```sql
SET @@location = 'US';  -- control where query executes

WITH transactions AS (
  SELECT customer_id, amount FROM `eu_transactions.sales_2024`
  UNION ALL
  SELECT customer_id, amount FROM `asia_transactions.sales_2024`
)
SELECT c.name, SUM(t.amount) AS total_sales
FROM hq_customers.customers AS c
JOIN transactions AS t ON c.id = t.customer_id
GROUP BY c.name;
```

### How It Works

1. BigQuery decomposes the query into per-region sub-queries
2. Runs each sub-query in its home region
3. Transfers **only the results** (minimized transfer) to the designated execution location
4. Assembles final result

### Governance Controls

- **Opt-in by default** — administrators must explicitly enable it per project
- Requires special per-user/service-account permission to run global queries
- Respects existing **VPC Service Controls** — data doesn't move in violation of established policies
- You control the execution location (data residency compliance)

### Pre-Sales Pitch

> "Multinational companies today must store data in the region it originates to meet GDPR, data sovereignty, and latency requirements. Global queries let you analyze all of it together with a single SQL statement — without building complex ETL pipelines to centralize the data first. EssilorLuxottica called it 'a powerful way to stay both secure and insight-driven.'"

---

## 3. BigQuery AI Functions — Gemini 3.0 Era (Jan–Feb 2026)

### The New AI Function Surface

| Function | Purpose | Status |
|----------|---------|--------|
| `AI.GENERATE()` | Free-form text generation, structured output extraction, multimodal (text/image/video/audio) | **GA** |
| `AI.GENERATE_TABLE()` | Same as GENERATE but returns a table-valued function output | **GA** |
| `AI.EMBED()` | Generate embeddings from text/images | **Preview** |
| `AI.SIMILARITY()` | Cosine similarity between two texts/images (auto-embeds) | **Preview** |
| `AI.SEARCH()` | Semantic search using managed embedding columns | **Preview** |

### Key Capability: One SQL Call, Five AI Tasks

```sql
SELECT AI.GENERATE(
  'Analyze this news article: ' || text,
  output_schema => STRUCT(
    entities ARRAY<STRING>,
    topic STRING,
    sentiment STRING,
    spanish_translation STRING,
    one_sentence_summary STRING
  )
)
FROM `bigquery-public-data.bbc_news.fulltext`
LIMIT 100;
```

### Simplified Auth: End User Credentials (EUC)

- Previously: configure a separate connection + service account for every Vertex AI integration
- Now: enable EUC → your personal IAM identity authenticates Vertex AI requests
- `connection_id` parameter is now **optional** for interactive queries
- Just grant yourself `Vertex AI User` role

### Autonomous Embedding Generation (Feb 2026)

```sql
-- Define an autonomous embedding column — BigQuery keeps it in sync automatically
ALTER TABLE mydataset.products
ADD COLUMN description_embedding FLOAT64[]
  OPTIONS (embedding_column = TRUE, source_column = 'description');
```

- BigQuery **automatically re-generates embeddings** when source data changes — no pipeline needed
- Integrated with `VECTOR_SEARCH` — create a vector index on the source column directly
- Use `AI.SEARCH` for simplified semantic search without touching embeddings manually

### Gemini 3.0 Support

```sql
SELECT AI.GENERATE(
  prompt,
  model => 'projects/myproject/locations/us-central1/publishers/google/models/gemini-3-flash'
)
FROM my_table;
```

### Pre-Sales Pitch

> "Your data analysts can now do entity extraction, sentiment analysis, translation, and summarization from a single SQL query — no Python, no Vertex AI SDK setup, no separate pipeline. BigQuery becomes the unified platform for both analytics and AI inference."

---

## 4. Conversational Analytics API (Jan 2026)

### What It Is

A **Gemini-powered API** to build context-aware data agents that:
- Understand natural language questions
- Generate and execute SQL against BigQuery
- Return answers as text, tables, and visual charts

### Architecture

```
User NL Question
      ↓
DataAgentServiceClient (configure access + context)
      ↓
ConversationReference (stateful session)
      ↓
Streamed response: Schema → SQL → Data → Chart → Text summary
```

### Two Conversation Modes

| Mode | How It Works | Use Case |
|------|-------------|----------|
| **Stateless** | You send full conversation history each request | Simple one-off Q&A |
| **Stateful** | API manages conversation history server-side | Follow-up questions, multi-turn analysis |

### Use Cases to Cite

- **Internal self-service**: Support/Sales asks "Why did signups drop last week?" → instant answer
- **Embedded SaaS analytics**: Let your customers query their own usage data in plain English
- **Dynamic reporting**: Replace static PDFs with conversational dashboards

### Pre-Sales Pitch

> "Instead of fielding 50 ad-hoc data requests from business stakeholders, you deploy one Conversational Analytics agent pointed at your BigQuery tables. Anyone in the company can ask data questions in plain English and get back charts and summaries — no SQL knowledge required."

---

## 5. Open Table Formats — Iceberg, Delta, Hudi in BigQuery

### Why This Matters (2025–2026 Trend)

Customers no longer want to be locked into proprietary formats. BigQuery now supports **open table formats** as first-class citizens.

### Supported Formats

| Format | Origin | BigQuery Support |
|--------|--------|-----------------|
| **Apache Iceberg** | Netflix (FOSS) | Native read/write; BigLake Metastore integration |
| **Delta Lake** | Databricks | Read via BigLake external tables |
| **Apache Hudi** | Uber (FOSS) | Read via BigLake external tables |

### How It Works: BigLake

BigLake is the GCP unified storage engine that bridges:
- **BigQuery** (serverless SQL)
- **Dataproc/Spark** (distributed compute)
- **Cloud Storage** (open format files: Parquet, Avro, ORC)

```
Cloud Storage (Parquet/Iceberg files)
           ↕  (BigLake Metastore)
    ┌──────┴──────┐
 BigQuery       Dataproc/Spark
 (SQL analytics) (ML/complex ETL)
```

### Pre-Sales Anti-Lock-In Story

> "We believe in open ecosystems. Store your data as Apache Iceberg on Cloud Storage — BigQuery can query it natively, Dataproc Spark can process it, and if you ever want to read it with another engine, it's just Parquet files. No proprietary format required."

---

## 6. Data Engineering Agents & Agentic AI on GCP (2025–2026)

### The New Paradigm

BigQuery is evolving from "data warehouse" → **"autonomous data-to-AI platform"**

### GCP Data Agent Types

| Agent Type | What It Does |
|-----------|-------------|
| **Data Engineering Agent** | Builds pipelines, writes Dataflow/SQL transforms automatically |
| **Conversational Analytics Agent** | Answers NL questions against BigQuery data |
| **BigQuery ML (BQML)** | Trains and deploys ML models with SQL |
| **Gemini in BigQuery** | Code assist, SQL generation, data preparation suggestions |

### The Agentic Workflow Pattern

```
Data Products (structured BQ tables + metadata)
         ↓
AI Agents (read data products, act on them)
         ↓
Orchestration (Cloud Composer / Eventarc / ADK)
         ↓
Business Outcomes (decisions, automation, insights)
```

### Pre-Sales Pitch

> "Data products — your curated BigQuery tables with proper descriptions, ownership, and lineage — are the foundation that makes AI agents reliable. An agent grounded in well-governed data products gives you trustworthy automation. This is the story: BigQuery → Dataplex governance → AI agents → business value."

---

## 7. Google's Foundational Big Data Papers (Must Know for Technical Depth)

> HR said "read the Google whitepapers." These are the canonical papers that BigQuery's architecture is built on.

### The Core Papers

| Paper | Year | What It Introduced | BigQuery Connection |
|-------|------|-------------------|-------------------|
| **MapReduce** | 2004 | Distributed batch processing (map + reduce functions) | Foundation for Dataproc/Hadoop |
| **Bigtable** | 2006 | Distributed NoSQL wide-column store | Powers Google's internal tables; Bigtable product |
| **Chubby** | 2006 | Distributed lock service / consensus | Infrastructure for coordination |
| **Dremel** | 2010 | Columnar storage for nested data + multi-level execution tree | **The direct ancestor of BigQuery** |
| **Colossus** | ~2010 | Google's next-gen distributed filesystem (after GFS) | BigQuery storage backend |
| **Spanner** | 2012 | Globally distributed ACID-compliant database | Cloud Spanner product |
| **F1** | 2013 | Distributed SQL database on top of Spanner | Influenced BigQuery's SQL engine |
| **Mesa** | 2014 | Highly available, scalable data warehousing system | Influenced BigQuery internals |
| **Dremel 2.0 (2020)** | 2020 | Updated Dremel — disaggregated storage+compute, shuffle | Modern BigQuery architecture |

### Dremel Deep Dive (Know This!)

Dremel = the engine behind BigQuery. Key concepts:

**1. Columnar Storage for Nested Records**
- Dremel represents nested records (like Protocol Buffers) in a purely columnar layout
- Uses **repetition levels** and **definition levels** to encode nesting without actual nesting
- Result: read only the columns you need → massive I/O reduction

**2. Multi-Level Execution Tree**
- Query → Root server → Intermediate servers → Leaf servers (storage)
- Each level: partial aggregation → result pushed up
- **Thousands of nodes** work in parallel → seconds on trillion-row tables
- Analogous to: a general → colonels → captains → soldiers (divide and conquer)

**3. In-Situ Processing**
- Dremel reads from Colossus (storage) directly — no data movement to a separate compute cluster
- This is the origin of BigQuery's **storage-compute separation**

**Elevator Pitch:**
> "BigQuery's speed comes from Dremel: instead of reading entire rows, it reads only the columns your query touches — stored as nested columnar data. Thousands of servers each process a shard and aggregate in parallel. A trillion-row table query completes in seconds because no single server sees more than a tiny slice."

---

## 8. Dataflow Streaming — New ML Infrastructure (2025–2026)

### What's New in Dataflow

- **ML inference integration**: Dataflow now has native support for running model inference as a pipeline step (RunInference transform with batching + GPU support)
- **Streaming SQL on Dataflow**: Write Apache Beam pipelines in SQL (Beam SQL) executed on Dataflow runners
- **Exactly-once delivery** on Pub/Sub → Dataflow → BigQuery (Storage Write API committed mode)

### Continuous Queries in BigQuery (Enterprise Edition)

A **new streaming paradigm** (BigQuery Enterprise required):

```sql
-- Continuously reads from a BigQuery table as data arrives
-- and writes transformed results to another table
EXPORT DATA OPTIONS(
  uri = 'pubsub://projects/myproject/topics/alerts',
  format = 'JSON'
)
AS
SELECT user_id, SUM(amount) as total
FROM APPENDS(TABLE transactions, NULL, NULL)  -- reads new appends continuously
WHERE amount > 1000
GROUP BY user_id;
```

- Runs **perpetually**, like a streaming job — not a batch query
- Eliminates need for a separate Dataflow pipeline for simple streaming transforms
- Works with **Pub/Sub output**, Bigtable output, or another BigQuery table

---

## 9. Cloud Composer 3 & Airflow 3.1 (2025–2026)

### What's New

- **Cloud Composer 3**: Latest generation — fully serverless execution, better isolation
- **Airflow 3.1 support**: announced January 2026
- **Gemini Cloud Assist integration**: Click "Investigate" on a failed DAG task → Gemini analyzes logs, identifies patterns (resource exhaustion, timeouts), provides fix recommendations
- **JDBC Driver for BigQuery** (Preview, Jan 2026): Google-built open-source JDBC driver for high-performance Java → BigQuery connections

### Key Airflow 3.1 Features

- Improved **backfill** UI and API
- **Asset-based scheduling** (trigger DAGs based on data availability, not time)
- Enhanced **task group** visualization

---

## 10. Dataplex Universal Catalog (2025 Rebrand + Expansion)

> Formerly: "Dataplex" + "Data Catalog" as separate products → now unified

### What Changed

- **Dataplex Universal Catalog** = Dataplex + Data Catalog + Lineage — merged into one governance platform
- Now embedded directly into BigQuery: **semantic search** for tables, **data lineage** in BQ console
- **AI-powered metadata**: Gemini generates table descriptions automatically

### Key Features

| Feature | What It Does |
|---------|-------------|
| Semantic search | Find tables by business meaning, not just name |
| Data lineage | Visualize how data flows from source → transformations → final table |
| Policy tags | Column-level classification (PII, confidential) → drives column-level access |
| Data quality | Define and run data quality checks; results visible in catalog |
| Business glossary | Define canonical business terms; link to columns |

### Pre-Sales Story

> "Your data governance story is: Dataplex Universal Catalog discovers and classifies every dataset automatically, applies policy tags to PII columns so only authorized roles can see them, and shows data lineage so you can prove regulatory compliance. All of this integrates natively with BigQuery — your analysts see it right in the console."

---

## 11. BigQuery Vector Search & AI.SEARCH

### The RAG (Retrieval Augmented Generation) Pattern in BigQuery

```
1. Store documents/text in BigQuery table
2. Add autonomous embedding column (AI manages embeddings)
3. Create vector index on embedding column
4. At query time: AI.SEARCH(TABLE, column, "natural language query")
5. Feed results as context to LLM (AI.GENERATE)
```

### Key Functions

```sql
-- Simple semantic search (no manual embedding management)
SELECT * FROM AI.SEARCH(
  TABLE mydataset.products,
  'description',
  'a really fun outdoor toy for kids'
);

-- Compute similarity between two texts
SELECT AI.SIMILARITY('How do I cancel my subscription?',
                     'What is the process to end my account?');
-- Returns: ~0.92 (high similarity)

-- Vector search with precomputed embeddings (for scale)
SELECT query.id, base.id, distance
FROM VECTOR_SEARCH(
  TABLE mydataset.products,
  'description_embedding',
  (SELECT embedding FROM mydataset.query_embeddings)
);
```

---

## 12. Key Numbers Table — 2026 Edition

| Metric | Value | Notes |
|--------|-------|-------|
| BigQuery on-demand price | $6.25/TiB scanned | First 1 TB/month free |
| Slot cost (Enterprise) | ~$0.06/slot-hour | Varies by region |
| Commitment discount | 20% (1-yr), 40% (3-yr) | Enterprise/Enterprise+ |
| BQ Standard edition max slots | 1,600 per reservation | Autoscaling only |
| Max partitions per table | 10,000 | Ingestion-time or column |
| Max clustering columns | 4 | Applied after partitioning |
| Storage Write API savings | ~50% vs legacy streaming | Committed mode, exactly-once |
| BI Engine RAM pricing | ~$0.04/GB/hour | In-memory acceleration |
| Dataproc preemptible savings | 60–80% | vs standard VMs |
| ESG TCO vs on-prem Hadoop | 50% lower | Published ESG study |
| ESG TCO vs AWS EMR | 30–50% lower | Same study |
| Dremel columnar compression | 5–10x | vs row-oriented formats |
| BigQuery query speed SLA | Seconds on TBs | Petabytes in minutes |

---

## 📚 Source Links (All Verified Feb 2026)

| Topic | URL |
|-------|-----|
| BigQuery overview | https://cloud.google.com/bigquery/docs/introduction |
| BigQuery Editions | https://cloud.google.com/bigquery/docs/editions-intro |
| Global queries (Preview) | https://cloud.google.com/bigquery/docs/global-queries |
| AI.GENERATE / AI.EMBED | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate |
| Autonomous embeddings | https://cloud.google.com/bigquery/docs/autonomous-embedding-generation |
| Conversational Analytics API | https://cloud.google.com/gemini/docs/conversational-analytics-api/overview |
| Dataplex Universal Catalog | https://cloud.google.com/dataplex/docs |
| Dremel paper (original) | https://research.google/pubs/pub36632/ |
| Cloud Composer 3 | https://cloud.google.com/composer/docs |
| BigQuery pricing | https://cloud.google.com/bigquery/pricing |
| What's new in Data Cloud | https://cloud.google.com/blog/products/data-analytics/whats-new-with-google-data-cloud |
