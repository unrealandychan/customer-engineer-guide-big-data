# BigQuery From Scratch — A Complete Tutorial

> **Who this is for:** Someone with zero BigQuery experience who needs to understand how it works, why it exists, and how to use it — at both the conceptual and hands-on level.  
> **Goal:** After reading this, you can explain BigQuery to a junior engineer AND to a CFO.

---

## Chapter 1: What Problem Does BigQuery Solve?

### The world before BigQuery

Imagine you work at a company. You collect 50 GB of transaction data every day. After a year, you have 18 TB of data. Your boss asks: *"Which customers in Germany spent more than $500 last month?"*

On a regular database (MySQL, PostgreSQL), this query would:
1. Lock the table
2. Scan all 18 TB row by row
3. Take hours or crash the database
4. Block your application from serving users

**Traditional solutions and their problems:**

| Solution | Problem |
|----------|---------|
| Scale up the database server | Expensive, still slow at scale, single point of failure |
| Build a Hadoop cluster | Weeks to set up, hard to manage, need specialists |
| Redshift / on-prem data warehouse | You must provision exact capacity upfront — too small = slow, too big = expensive |
| Buy more hardware | Hardware depreciates, takes months to arrive |

### What BigQuery does differently

BigQuery was built at Google to solve Google's problem: they have *petabytes* of data and thousands of engineers asking questions every day. The system they built is now available to everyone.

**The key ideas:**
1. **Separate storage from compute** — your data lives in Google's storage, and compute power is summoned on demand
2. **Columnar storage** — instead of storing whole rows, store each column separately
3. **Massively parallel execution** — split your query across thousands of machines simultaneously
4. **Serverless** — you never provision or manage any infrastructure

**Result:** A query scanning 1 TB of data runs in seconds, you pay only for what you scanned, and the next query automatically gets a fresh fleet of machines.

---

## Chapter 2: How BigQuery Stores Data

### Row storage vs Columnar storage

This is the most important concept. Everything else flows from it.

**Row storage (traditional databases):**
```
Row 1: [ user_id=1001, country="DE", amount=450.00, date="2026-01-15" ]
Row 2: [ user_id=1002, country="US", amount=120.00, date="2026-01-15" ]
Row 3: [ user_id=1003, country="DE", amount=890.00, date="2026-01-15" ]
```

All 4 columns for each row are stored together on disk. To answer "total amount for Germany", you must read ALL 4 columns for ALL rows — even though you only need `country` and `amount`.

**Columnar storage (BigQuery):**
```
country column:  [ "DE", "US", "DE", "FR", "DE", "US", ... ]
amount column:   [ 450.00, 120.00, 890.00, 230.00, 310.00, 95.00, ... ]
user_id column:  [ 1001, 1002, 1003, 1004, 1005, 1006, ... ]
date column:     [ "2026-01-15", "2026-01-15", ... ]
```

Each column is stored separately. To answer "total amount for Germany", BigQuery reads ONLY the `country` and `amount` columns — skipping `user_id` and `date` entirely.

**Why this matters:**
- A 10-column table where you query 2 columns → you scan 20% of the data
- A `SELECT *` forces BigQuery to read all columns → always avoid it

### Capacitor — BigQuery's storage format

BigQuery stores data in its own proprietary columnar format called **Capacitor**. You never interact with it directly, but it does three important things:

1. **Encodes data efficiently** — integers are compressed, repeated strings are deduplicated
2. **Stores statistics** — min/max values per column per block, so BigQuery can skip entire blocks that can't possibly match your filter
3. **Handles nested/repeated fields** — unlike most SQL databases, BigQuery can store arrays and nested records natively (important for JSON-like data)

### Where data physically lives

Your BigQuery data lives in **Colossus** — Google's distributed file system (successor to GFS, which the famous 2003 Google paper described). It's the same storage system that stores Google Photos, Gmail, and YouTube.

- Data is replicated across multiple physical locations automatically
- You never manage disks, RAID, backups, or replication
- Storage is billed separately from compute at ~$0.02/GB/month

---

## Chapter 3: How BigQuery Executes Queries — The Dremel Engine

### The analogy: a library with 10,000 librarians

Imagine you walk into a library with 10,000 librarians and ask: *"How many books were published in Germany after 2010?"*

A single librarian would take weeks. But with 10,000:
- The collection is divided into 10,000 sections
- Each librarian searches their section simultaneously
- A supervisor collects all partial answers and adds them up
- Total time: roughly as long as it takes ONE librarian to search ONE section

This is exactly how BigQuery's query engine — **Dremel** — works.

### The Dremel execution tree

When you submit a SQL query, BigQuery builds an **execution tree**:

```
                      [ ROOT SERVER ]
                    (collects final result)
                   /         |          \
            [ MIX 1 ]    [ MIX 2 ]   [ MIX 3 ]
          (partial sums) (partial sums) (partial sums)
          /    |    \      /   |   \     /   |   \
        [L] [L] [L] [L] [L] [L]  [L] [L] [L]
         ↑   ↑   ↑   ↑   ↑   ↑    ↑   ↑   ↑
    Leaf servers — each reads a slice of the data from Colossus
```

- **Leaf servers** read raw data from Colossus (storage)
- **Mixer servers** aggregate partial results from leaves
- **Root server** produces the final answer

The number of leaf servers scales dynamically based on query complexity and data size. A query on 1 TB might use hundreds; a query on 1 PB might use thousands.

### What are "slots"?

A **slot** is one unit of BigQuery compute — roughly equivalent to one virtual CPU with associated memory.

- On-demand queries automatically get up to 2,000 slots
- The more slots, the more parallel work can happen simultaneously
- BigQuery **Editions** (capacity reservations) let you buy a fixed pool of slots that you control

Think of slots like taxi cabs:
- On-demand = hailing a taxi (available immediately, you pay per trip)
- Reservations = leasing a fleet of taxis (predictable capacity, fixed monthly cost)

### Query stages and the execution plan

Every BigQuery query is broken into **stages**. You can see these in the "Execution details" tab in the BigQuery UI.

```
Query: SELECT country, SUM(amount) FROM orders WHERE date >= '2026-01-01' GROUP BY country

Stage 1 (Read + Filter):
  - Read 'date' and 'country' and 'amount' columns from Colossus
  - Filter: only rows where date >= '2026-01-01'
  - Output: (country, amount) pairs → written to shuffle

Stage 2 (Aggregate):
  - Read shuffle output
  - GROUP BY country, compute SUM(amount)
  - Output: final result

Stage 3 (Output):
  - Write result to response or destination table
```

Each stage runs in parallel across many workers. The bottleneck is often the **shuffle** — moving data between stages across the network.

---

## Chapter 4: How Data Gets Into BigQuery

There are 5 main ingestion paths:

### Path 1: Batch load from Cloud Storage

Upload files (CSV, JSON, Avro, Parquet, ORC) to Cloud Storage, then load them into BigQuery.

```
CSV file in GCS → bq load command → BigQuery table
```

- **Best for:** bulk historical data loads, daily ETL batches
- **Cost:** free (loading is free in BigQuery)
- **Speed:** typically minutes for GB-scale data

### Path 2: Streaming inserts (Storage Write API)

Insert individual rows in real-time as events happen.

```
Application → BigQuery Storage Write API → BigQuery table (visible in seconds)
```

- **Best for:** real-time dashboards, live event tracking
- **Cost:** ~$0.01 per 200 MB of streamed data
- **Latency:** data visible within seconds

### Path 3: Pub/Sub → Dataflow → BigQuery

Events flow through a message queue, get transformed, and land in BigQuery.

```
Event producers → Pub/Sub → Dataflow pipeline → BigQuery
```

- **Best for:** high-volume streaming with transformations (cleansing, enrichment, routing)
- **Cost:** Pub/Sub + Dataflow + BigQuery streaming costs
- **Complexity:** higher, but most flexible

### Path 4: Query against external data (BigLake)

BigQuery can query files sitting in Cloud Storage, AWS S3, or Azure Blob directly — without copying the data in.

```
CSV files in GCS → BigLake external table → BigQuery SQL queries
```

- **Best for:** data you don't want to move, open format compatibility (Iceberg/Parquet)
- **Cost:** you pay for bytes scanned, same as regular tables

### Path 5: Data transfers (scheduled)

Automated transfers from common SaaS tools: Google Ads, YouTube, Campaign Manager, Amazon S3, Teradata, Redshift.

```
Google Ads → BigQuery Data Transfer Service → BigQuery dataset
```

- **Best for:** marketing analytics, migrating from other warehouses
- **Cost:** free for Google sources, varies for third-party

---

## Chapter 5: BigQuery Data Model

### Projects, Datasets, Tables

BigQuery organizes data in three levels:

```
Project (billing + IAM boundary)
└── Dataset (namespace + access control + region)
    ├── Table (actual data)
    ├── View (saved SQL query, no data stored)
    └── Materialized View (precomputed result, stored + auto-refreshed)
```

**Project:** Everything in GCP lives in a project. Billing, IAM permissions, and quotas are per-project.

**Dataset:** A container for tables. Defines the geographic region where data is stored (e.g., `US`, `EU`, `us-central1`). Access control is typically applied at the dataset level.

**Table:** Where data actually lives. Three types:
- **Native table** — data stored in BigQuery's Capacitor format
- **External table** — metadata only, data lives in GCS/S3/Azure
- **Materialized view** — precomputed query result, automatically refreshed

### Schemas — typed and strict

Every BigQuery table has a schema defining columns and their types:

| Type | Description | Example |
|------|-------------|---------|
| STRING | UTF-8 text | `"Berlin"` |
| INT64 | 64-bit integer | `42` |
| FLOAT64 | Floating point | `3.14159` |
| NUMERIC | Exact decimal (29 digits, 9 scale) | `450.99` |
| BOOL | True/False | `true` |
| DATE | Calendar date | `2026-01-15` |
| TIMESTAMP | Date + time + timezone | `2026-01-15 09:30:00 UTC` |
| ARRAY | Repeated values of one type | `[1, 2, 3]` |
| STRUCT | Nested record with named fields | `{city: "Berlin", zip: "10115"}` |
| JSON | Semi-structured JSON | `{"key": "value"}` |

### Nested and repeated fields (a BigQuery superpower)

Unlike traditional databases, BigQuery can store arrays and nested objects natively.

**Example: orders table with line items**
```json
{
  "order_id": "ORD-001",
  "customer": {
    "name": "Alice",
    "country": "DE"
  },
  "line_items": [
    {"product": "Widget A", "qty": 2, "price": 19.99},
    {"product": "Widget B", "qty": 1, "price": 49.99}
  ]
}
```

In a traditional database, you'd need 3 tables (orders, customers, line_items) with JOINs.  
In BigQuery, all of this is one row, zero JOINs, and queries are simpler and faster.

---

## Chapter 6: Writing SQL in BigQuery

BigQuery uses **GoogleSQL** (formerly called Standard SQL) — fully ANSI-compliant with extensions.

### The basics

```sql
-- Select specific columns (NEVER use SELECT *)
SELECT
  user_id,
  country,
  amount,
  event_date
FROM `my-project.analytics.orders`
WHERE event_date >= '2026-01-01'    -- Always filter on partition column
  AND country = 'DE'
LIMIT 100;
```

### Aggregations

```sql
-- Sales by country, last 30 days
SELECT
  country,
  COUNT(DISTINCT user_id)     AS unique_customers,
  SUM(amount)                 AS total_revenue,
  AVG(amount)                 AS avg_order_value,
  MAX(amount)                 AS largest_order
FROM `my-project.analytics.orders`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY country
ORDER BY total_revenue DESC;
```

### Window functions — running totals, rankings, lead/lag

Window functions do calculations across related rows without collapsing them into aggregates. This is one of BigQuery's strongest areas.

```sql
-- Rank customers by spend within each country
SELECT
  user_id,
  country,
  total_spend,
  RANK() OVER (PARTITION BY country ORDER BY total_spend DESC) AS rank_in_country,
  SUM(total_spend) OVER (PARTITION BY country)                 AS country_total,
  total_spend / SUM(total_spend) OVER (PARTITION BY country)  AS pct_of_country
FROM customer_summary;
```

```sql
-- Running total of daily revenue
SELECT
  event_date,
  daily_revenue,
  SUM(daily_revenue) OVER (ORDER BY event_date) AS cumulative_revenue
FROM daily_summary;
```

```sql
-- Day-over-day change
SELECT
  event_date,
  revenue,
  LAG(revenue, 1) OVER (ORDER BY event_date)  AS prev_day_revenue,
  revenue - LAG(revenue, 1) OVER (ORDER BY event_date) AS daily_change
FROM daily_summary;
```

### Querying nested/repeated data

```sql
-- Unnest line items from the orders table
SELECT
  order_id,
  item.product,
  item.qty,
  item.price,
  item.qty * item.price AS line_total
FROM `my-project.analytics.orders`,
UNNEST(line_items) AS item
WHERE event_date = '2026-01-15';
```

### WITH clauses (CTEs) — cleaner complex queries

```sql
-- Complex query using CTEs
WITH
  -- Step 1: Get active users in last 30 days
  active_users AS (
    SELECT DISTINCT user_id
    FROM `my-project.analytics.events`
    WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  ),
  -- Step 2: Get their total spend
  user_spend AS (
    SELECT
      o.user_id,
      SUM(o.amount) AS total_spend
    FROM `my-project.analytics.orders` o
    INNER JOIN active_users u USING (user_id)
    WHERE o.event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY o.user_id
  )
-- Final: Classify by spend tier
SELECT
  user_id,
  total_spend,
  CASE
    WHEN total_spend >= 1000 THEN 'VIP'
    WHEN total_spend >= 200  THEN 'Regular'
    ELSE 'Low-Value'
  END AS customer_tier
FROM user_spend
ORDER BY total_spend DESC;
```

---

## Chapter 7: Partitioning and Clustering — Explained Simply

### Partitioning: the filing cabinet metaphor

Imagine your 18 TB of orders data is in a filing cabinet with one drawer per day — 365 drawers for a year.

When someone asks *"show me Germany orders from last month"*, instead of opening every drawer, you open only the 31 drawers for that month. You've skipped 334 drawers.

**That's partitioning.** BigQuery stores data in physical segments (partitions). Queries that filter on the partition column skip entire partitions — they don't even read the data.

```sql
-- Create a partitioned table
CREATE TABLE `my-project.analytics.orders`
(
  order_id   STRING,
  user_id    INT64,
  country    STRING,
  amount     NUMERIC,
  event_date DATE      -- the partition column
)
PARTITION BY event_date
OPTIONS (require_partition_filter = TRUE);  -- Forces queries to specify a date range
```

```sql
-- This query PRUNES partitions (only reads Jan data)
SELECT SUM(amount) FROM orders WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31';

-- This query SCANS EVERYTHING (no partition filter) -- will be rejected if require_partition_filter=TRUE
SELECT SUM(amount) FROM orders WHERE country = 'DE';
```

**The critical mistake to avoid:**
```sql
-- BREAKS partition pruning -- wrapping partition column in a function
WHERE DATE(event_timestamp) = '2026-01-15'   -- BAD: BigQuery can't prune

-- CORRECT -- filter on the partition column directly
WHERE event_date = '2026-01-15'              -- GOOD: BigQuery prunes correctly
```

### Clustering: the index inside the drawer

Back to the filing cabinet. Within each drawer (partition), files are sorted alphabetically by country. When you ask for Germany files, you can skip straight to the "G" section.

**That's clustering.** Within each partition, data blocks are sorted by the cluster columns. BigQuery skips blocks that can't possibly match your filter.

```sql
-- Partitioned AND clustered table
CREATE TABLE `my-project.analytics.orders`
(
  order_id   STRING,
  user_id    INT64,
  country    STRING,
  campaign   STRING,
  amount     NUMERIC,
  event_date DATE
)
PARTITION BY event_date
CLUSTER BY country, campaign;   -- up to 4 clustering columns
```

```sql
-- This query benefits from BOTH partition pruning AND cluster pruning
SELECT SUM(amount)
FROM orders
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31'  -- partition pruning
  AND country = 'DE'                                      -- cluster pruning
  AND campaign = 'spring-sale';                           -- cluster pruning
```

**Choosing cluster columns:** Pick columns you filter or GROUP BY most often. High-cardinality columns (user_id, product_id) are better for clustering than low-cardinality (true/false flags).

### What does the savings look like?

| Table setup | Bytes scanned for "Germany last month" query |
|-------------|---------------------------------------------|
| No partitioning, no clustering | 18 TB (full scan) |
| Partition by date only | ~1.5 TB (30 days / 365 days = ~8%) |
| Partition by date + cluster by country | ~150 GB (Germany is ~10% of orders) |
| Improvement | **120x less data scanned** |

120x less data = 120x lower cost + roughly 120x faster.

---

## Chapter 8: Pricing — What You Actually Pay For

### On-demand pricing

You pay per byte of data scanned by your queries.

```
Price: $6.25 per TiB scanned (1 TiB = 1,024 GB)

Example query scans 100 GB:
  Cost = (100 / 1024) × $6.25 = $0.61

Example query scans 10 TB:
  Cost = (10 / 1024) × 1024 × $6.25 = $62.50
```

**What's free:**
- Loading data (batch loads from GCS = free)
- Exporting data (to GCS = free)
- Metadata operations (CREATE TABLE, DROP, etc.)
- Query result caching (same query within 24 hours = free)
- Storage for the first 10 GB/month

### BigQuery Editions (capacity pricing)

Instead of paying per byte, you buy a pool of **slots** (compute capacity). Your queries share the slot pool.

| Edition | Minimum commitment | Key features | Good for |
|---------|-------------------|--------------|----------|
| Standard | Per-second autoscale | Basic analytics | Occasional workloads |
| Enterprise | 1-year commitment | CMEK, 99.99% SLA | Production analytics |
| Enterprise+ | 1-year commitment | CMEK, Assured Workloads, cross-region DR | Regulated industries |

**When capacity pricing wins over on-demand:**
- You have predictable, heavy query volume
- Your team runs many queries daily
- You need cost predictability (no surprise bills)

**Rule of thumb:** If your monthly on-demand bill exceeds ~$2,000, evaluate capacity pricing.

### Storage pricing

```
Active storage:  $0.020 per GB per month
Long-term:       $0.010 per GB per month  (automatic after 90 days without modification)
```

A 10 TB table costs $200/month in active storage. After 90 days without changes, it drops to $100/month automatically.

---

## Chapter 9: Security and Access Control

### IAM — who can do what

BigQuery uses Google Cloud IAM (Identity and Access Management). Permissions are granted via roles:

| Role | What they can do |
|------|-----------------|
| `bigquery.admin` | Everything — create, delete, manage |
| `bigquery.dataEditor` | Read + write data, create tables |
| `bigquery.dataViewer` | Read data only |
| `bigquery.jobUser` | Run queries (needs dataViewer on the dataset too) |
| `bigquery.user` | Run queries, create their own datasets |

**Hierarchy:** Permissions can be set at project, dataset, or table level.

```
Project level → applies to ALL datasets in the project
  └── Dataset level → applies to ALL tables in the dataset
        └── Table level → applies to ONE specific table
```

### Column-level security

You can restrict access to specific columns using **column-level access policies** (policy tags).

```sql
-- Example: SSN column has a policy tag that restricts access
-- Only users with the 'PII Viewer' role can see the actual value
-- Others see NULL

SELECT customer_id, name, ssn  -- SSN appears as NULL for non-authorized users
FROM customers;
```

### Row-level security

Restrict which rows a user can see using **row-level access policies**.

```sql
-- Only EU team members see EU rows
CREATE ROW ACCESS POLICY europe_only
ON orders
GRANT TO ("group:eu-analytics@company.com")
FILTER USING (region = 'EU');
```

### Authorized views

A view that can access data in other datasets, without granting the viewer direct access to the underlying tables.

```sql
-- Create a view that masks PII
CREATE VIEW `my-project.public_views.safe_orders` AS
SELECT
  order_id,
  country,
  amount,
  SHA256(email) AS hashed_email  -- PII is masked
FROM `my-project.raw.orders`;
```

---

## Chapter 10: Key BigQuery Interview Concepts

### "What is BigQuery?" — 30-second answer

> "BigQuery is Google Cloud's fully managed, serverless data warehouse. It separates storage from compute — your data lives in Google's distributed storage (Colossus), and when you run a query, it spins up thousands of parallel workers (using the Dremel engine) to process it in seconds. You pay per byte scanned, and you never provision any infrastructure. It's designed for analytical workloads — aggregations, joins, and window functions on terabytes to petabytes of data."

### "How does partitioning work?" — 30-second answer

> "Partitioning divides a table into segments by a key — usually a date column. When a query has a filter on that partition key, BigQuery reads only the relevant partitions and skips the rest entirely. On a 1-year table of daily data, a 30-day query skips 90% of the data before the query even starts — so you save both cost and time."

### "Why not just use SELECT *?" — 30-second answer

> "Because BigQuery uses columnar storage. You pay per byte scanned, and each column you include in SELECT means more bytes read. A 10-column table where you only need 2 columns — SELECT * costs 5x more than selecting just those 2 columns. It also slows the query down proportionally."

### "What's the difference between slots and bytes scanned?"

> "Bytes scanned determines cost in on-demand pricing — it's about how much data you read from storage. Slots are compute units — they determine how fast the query runs. More slots = more parallel processing = faster query. With capacity reservations you control slots; with on-demand you control cost through scan reduction."

### The critical "when NOT to use BigQuery" answer

BigQuery is NOT the right choice for:
- **OLTP workloads** — high-QPS transactional writes/reads (use Cloud Spanner or Cloud SQL)
- **Sub-100ms query latency requirements** — BigQuery has seconds latency, not milliseconds
- **Updating individual rows frequently** — BigQuery is append-optimized; frequent DML (UPDATE/DELETE) is expensive
- **Small data** (< 10 GB) — the overhead of spinning up distributed compute isn't worth it

---

## Quick Reference Card

```
BigQuery Mental Model:
  Storage (Colossus, columnar, Capacitor format)
    ↓ read by
  Dremel Engine (leaf servers → mixers → root)
    ↑ fed by
  Slots (compute units — on-demand or reserved)

Cost drivers:
  On-demand → bytes scanned
  Capacity  → slot-hours committed

Optimization hierarchy:
  1. Partition (skip whole date ranges)
  2. Cluster (skip blocks within partitions)
  3. Query hygiene (SELECT only needed columns)
  4. Pricing model (on-demand vs reservations)

IAM hierarchy:
  Project → Dataset → Table → Column → Row

Data flows into BigQuery via:
  GCS batch load | Streaming Write API | Pub/Sub→Dataflow | BigLake external | Transfer Service
```
