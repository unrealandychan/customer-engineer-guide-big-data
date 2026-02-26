# Lesson 01 — What is BigQuery?

> **Official doc:** [cloud.google.com/bigquery/docs/introduction](https://cloud.google.com/bigquery/docs/introduction)  
> **Time:** ~20 minutes

---

## 1.1 The one-sentence definition

> BigQuery is a **fully managed, serverless, petabyte-scale data warehouse** on Google Cloud. You run SQL queries on large datasets and pay only for what you use — no servers to provision or manage.

---

## 1.2 Why BigQuery was built

Traditional databases (MySQL, PostgreSQL) are built for **transactional workloads** — inserting and updating individual records quickly. They struggle when you need to:

- Scan billions of rows to compute a total
- Join two 1 TB tables together
- Run 200 analysts simultaneously on the same dataset

BigQuery was built at Google to solve Google's own scale problem (petabytes of web data, thousands of engineers). The key design decisions were:

| Decision | What it means |
|----------|---------------|
| **Separate storage from compute** | Your data lives in Google's distributed storage. Compute is rented on demand, scales to zero when idle |
| **Columnar storage** | Only read the columns a query needs, not entire rows |
| **Massively parallel execution** | Split one query across thousands of machines simultaneously |
| **Serverless** | No cluster to provision, patch, scale, or pay for when idle |

---

## 1.3 The architecture in one diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOU                                      │
│        SQL query in console / bq CLI / Python client            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  COMPUTE LAYER (Dremel engine)                  │
│                                                                 │
│   Root server          Mixer servers          Leaf servers      │
│   (final result) ←── (partial results) ←── (scan columns)      │
│                                                ↑                │
└────────────────────────────────────────────────┼────────────────┘
                                                 │ reads
┌────────────────────────────────────────────────┼────────────────┐
│                  STORAGE LAYER (Colossus)       │                │
│                                                 │                │
│   [ country col ]  [ amount col ]  [ date col ] │               │
│   DE DE US FR …    450 120 890 …   2026-01 …   │               │
│                                                                  │
│   Data replicated across multiple locations. 11 nines durability│
└─────────────────────────────────────────────────────────────────┘
```

**Key insight from Google's own docs:**
> *"BigQuery's architecture consists of two parts: a storage layer that ingests, stores, and optimizes data and a compute layer that provides analytics capabilities. These compute and storage layers efficiently operate independently of each other thanks to Google's petabit-scale network."*

This independence means Google can improve storage and compute separately — and that you only pay for compute when queries are running.

---

## 1.4 BigQuery's four capability areas

According to the official docs, BigQuery covers four areas:

### Storage
- Columnar format (Capacitor) stored on Colossus
- Automatic replication across availability zones
- Supports: standard tables, external tables, table clones, table snapshots, materialized views
- Automatic encryption at rest

### Analytics
- SQL queries (fully ANSI-compliant GoogleSQL)
- Window functions, geospatial functions, ML functions
- Federated queries (query data in GCS, Spanner, Bigtable without loading it)
- BI Engine for sub-second dashboard queries

### AI / ML
- **BigQuery ML** — train ML models using SQL (no Python required)
- **AI functions** — `AI.GENERATE_TEXT()`, `AI.EMBED_TEXT()`, `AI.SIMILARITY()` using Gemini models
- Vector search for semantic similarity
- Integration with Vertex AI

### Administration
- IAM for access control (project / dataset / table / column / row level)
- Reservations and slot commitments (capacity pricing)
- Jobs API (query, load, export, copy)
- Audit logging, data lineage, data quality via Dataplex

---

## 1.5 BigQuery vs traditional databases

| Feature | MySQL/PostgreSQL | BigQuery |
|---------|-----------------|----------|
| Best for | Transactional (OLTP) | Analytical (OLAP) |
| Query 1 TB | Minutes to hours | Seconds |
| Infrastructure | You manage servers | Fully managed |
| Scaling | Manual (add servers) | Automatic |
| Concurrent users | Dozens | Thousands |
| Update individual rows | Fast | Expensive (avoid) |
| Cost model | Fixed server cost | Pay per query |

---

## 1.6 BigQuery Interfaces

You can interact with BigQuery through:

| Interface | Best for |
|-----------|----------|
| **Google Cloud Console** | Interactive queries, exploring data, UI-based work |
| **bq CLI** | Scripting, automation, loading data from command line |
| **Python client library** | ETL pipelines, data engineering workflows |
| **Go / Java / Node.js clients** | Application-level integrations |
| **REST API / RPC API** | Custom integrations |
| **JDBC / ODBC drivers** | Connecting BI tools (Tableau, Power BI) |
| **Looker Studio / Looker** | Dashboard and reporting |

---

## 1.7 Gemini in BigQuery (2025–2026 feature)

The official docs highlight Gemini-powered features:

- **SQL generation** — describe what you want in plain English, Gemini writes the SQL
- **Query explanation** — paste a complex query, Gemini explains it line by line
- **Data canvas** — drag-and-drop interface: find tables → join → query → visualise using natural language
- **Data insights** — auto-generated queries that explore your table and surface patterns
- **Python code generation** — generates BigQuery DataFrame code from natural language

---

## Practice Exercise 01

**No SQL needed yet** — answer these questions in your own words:

1. What is the difference between the storage layer and compute layer in BigQuery?
2. Why can't you use BigQuery as a replacement for MySQL in a web application?
3. Name three different ways you could send a query to BigQuery.
4. What does "serverless" mean in the context of BigQuery?

**Answers to check yourself:**

<details>
<summary>Click to reveal</summary>

1. Storage layer (Colossus) holds the data permanently. Compute layer (Dremel) is spun up only when a query runs and scales based on query size. They scale independently.

2. BigQuery is OLAP (analytical) not OLTP (transactional). It has seconds-level query latency (not milliseconds), doesn't support high-QPS single-row writes efficiently, and DML (UPDATE/DELETE) operations are expensive compared to a traditional RDBMS.

3. Cloud Console (UI), `bq` CLI, Python/Go/Java client library, REST API, JDBC/ODBC driver, Looker Studio.

4. You don't provision servers, choose machine types, set cluster sizes, or manage infrastructure. Google handles all of that. You just run queries.

</details>

---

**Next:** [Lesson 02 — How BigQuery Stores Data →](02-storage.md)
