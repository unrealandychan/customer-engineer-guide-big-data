# Lesson 02 — How BigQuery Stores Data

> **Official doc:** [cloud.google.com/bigquery/docs/storage_overview](https://cloud.google.com/bigquery/docs/storage_overview)  
> **Time:** ~25 minutes

---

## 2.1 Columnar storage — the core idea

The official docs state:

> *"Many traditional database systems store their data in row-oriented format, meaning rows are stored together, with the fields in each row appearing sequentially on disk. BigQuery stores table data in columnar format, meaning it stores each column separately."*

**Visualised:**

```
Your table:
  order_id | country | amount  | date
  ---------|---------|---------|----------
  ORD-001  | DE      | 450.00  | 2026-01-15
  ORD-002  | US      | 120.00  | 2026-01-15
  ORD-003  | DE      | 890.00  | 2026-01-16
  ORD-004  | FR      | 230.00  | 2026-01-16

ROW storage (traditional DB):
  disk: [ORD-001, DE, 450.00, 2026-01-15] [ORD-002, US, 120.00, 2026-01-15] ...
  Query "SUM(amount) WHERE country='DE'" → must read ALL 4 columns for ALL rows

COLUMNAR storage (BigQuery):
  disk: country_col: [DE, US, DE, FR]
        amount_col:  [450.00, 120.00, 890.00, 230.00]
        order_id_col:[ORD-001, ORD-002, ORD-003, ORD-004]  ← not read
        date_col:    [2026-01-15, 2026-01-15, 2026-01-16, 2026-01-16] ← not read
  Query "SUM(amount) WHERE country='DE'" → reads ONLY country + amount columns
```

**Result:** For a 10-column table where your query needs 2 columns, BigQuery reads 20% of the data a row-oriented database would read.

### Why columns compress better

Another advantage from the docs:
> *"Data within a column typically has more redundancy than data across a row. This characteristic allows for greater data compression by using techniques such as run-length encoding."*

Example: `country` column = `["DE","DE","DE","DE","US","US","DE","DE"]`  
Run-length encoded: `[DE×4, US×2, DE×2]` — stores 3 values instead of 8. Dramatic space savings.

---

## 2.2 The Capacitor format

BigQuery uses its own proprietary columnar storage format called **Capacitor** (documented in Google's engineering blog). Key properties:

- Each column stored as independent file blocks
- Each block has **min/max statistics** — BigQuery uses these to skip blocks that can't match a filter without reading any data
- Handles **nested and repeated fields** natively (ARRAY, STRUCT types)
- **Automatically compressed** — you pay for physical bytes, not raw logical bytes

You never create Capacitor files directly — BigQuery manages this automatically.

---

## 2.3 Where data lives: Colossus

The official docs confirm:
> *"BigQuery storage is designed for 99.999999999% (11 9's) annual durability. BigQuery replicates your data across multiple availability zones to protect from data loss."*

This storage runs on **Colossus** — Google's global distributed filesystem (successor to the Google File System described in the 2003 Google paper). You never interact with it directly. Key facts:

- Data is automatically replicated (you don't configure this)
- Encrypted at rest automatically
- Available across regions (you choose the region when creating a dataset)
- Storage is billed separately from compute

---

## 2.4 Types of table storage

From the official docs, BigQuery has several types of stored resources:

### Standard tables
The main table type. Data stored in Capacitor columnar format in Colossus. Supports all SQL operations. You pay for storage.

### Table clones
A lightweight, writable copy of a standard table. BigQuery stores only the **delta** (differences) between the clone and the base table — not a full copy. Cost-effective for creating test datasets from production data.

```sql
CREATE TABLE `project.dataset.orders_clone`
CLONE `project.dataset.orders`;
```

### Table snapshots
A point-in-time, read-only copy. BigQuery stores only the delta from the base table. Use for backups or auditing historical states.

```sql
CREATE SNAPSHOT TABLE `project.dataset.orders_snapshot_jan`
CLONE `project.dataset.orders`
FOR SYSTEM_TIME AS OF '2026-01-31 23:59:59 UTC';
```

### Materialized views
A precomputed result of a SQL query, stored and automatically refreshed when the base table changes. Queries that can use the materialized view are rewritten to use it automatically — dramatically faster for dashboards.

```sql
CREATE MATERIALIZED VIEW `project.dataset.daily_revenue_mv` AS
SELECT
  DATE(order_timestamp) AS order_date,
  country,
  SUM(amount) AS daily_revenue
FROM `project.dataset.orders`
GROUP BY order_date, country;
```

### External tables (BigLake)
Metadata only stored in BigQuery — actual data lives in Cloud Storage, Amazon S3, or Azure Blob. You can query it with SQL without copying it into BigQuery.

```sql
CREATE EXTERNAL TABLE `project.dataset.raw_logs`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://my-bucket/logs/year=2026/*.parquet']
);
```

---

## 2.5 Storage billing models

The official docs explain two billing models you set **per dataset**:

### Logical storage billing (default)
You pay for the uncompressed logical size of your data.

```
Pricing (as of 2026):
  Active storage:    $0.020 per GB / month
  Long-term storage: $0.010 per GB / month  (auto after 90 days without modification)
```

**Long-term storage:** Any table or partition that hasn't been modified for 90 consecutive days automatically moves to the long-term rate — 50% cheaper. No action required.

### Physical storage billing
You pay for the actual compressed bytes on disk (Capacitor compression means physical < logical). Also includes separate charges for **time travel** and **fail-safe** storage.

- **Time travel:** Stores all versions of your data for a configurable window (default 7 days). Lets you query data from the past with `FOR SYSTEM_TIME AS OF`.
- **Fail-safe:** An additional 7-day window after time travel where Google retains data for disaster recovery (not queryable by you, not configurable).

**Choosing between them:**

| Scenario | Recommendation |
|----------|----------------|
| Well-compressed data (Parquet, repeated values) | Physical billing (you pay less) |
| Poorly compressed data (unique strings, floats) | Logical billing may be cheaper |
| Want simplicity | Logical billing (default, no surprises) |
| Large time travel window | Check both — time travel cost appears in physical billing |

---

## 2.6 How data gets in and out

### Loading data (ingestion)

From the official docs:
- **Batch load:** Load files from Cloud Storage (CSV, JSON, Avro, Parquet, ORC) or local files. Free for loading.
- **Streaming:** Continually stream rows using the Storage Write API. Data available in near-real-time.
- **Generated data:** INSERT statements or query results written to a table.

### Reading data

| Method | Use case |
|--------|----------|
| SQL query | Analytics — the most common method |
| BigQuery Storage Read API | High-throughput reads by ML pipelines, Spark, Dataflow |
| Export to Cloud Storage | Bulk export (Avro, Parquet, CSV) — free |
| Copy job | Copy a table within BigQuery |

From the docs:
> *"The BigQuery API is the least efficient method and shouldn't be used for high volume reads. If you need to export more than 50 TB of data per day, use the EXPORT DATA statement or the BigQuery Storage API."*

---

## 2.7 Time travel — querying historical data

BigQuery keeps historical versions of all data for up to 7 days (configurable). You can query a past state using `FOR SYSTEM_TIME AS OF`:

```sql
-- What did this table look like 3 hours ago?
SELECT *
FROM `project.dataset.orders`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
WHERE country = 'DE';

-- Restore accidentally deleted rows
INSERT INTO `project.dataset.orders`
SELECT *
FROM `project.dataset.orders`
FOR SYSTEM_TIME AS OF '2026-01-15 09:00:00 UTC'
WHERE order_id NOT IN (SELECT order_id FROM `project.dataset.orders`);
```

---

## Practice Exercise 02

**Try these in the BigQuery sandbox** (or answer conceptually):

1. You have a 10-column table. Your most common query uses `WHERE date = today AND country = 'DE'` and selects `SUM(amount)`. Which 3 columns does BigQuery actually read? What happens to the other 7?

2. You have a `products` table that was last updated 4 months ago. What storage rate does it automatically get charged at?

3. You want a snapshot of your `orders` table every month for compliance. Which table type is most cost-efficient and why?

4. Write the SQL to create an external table pointing to Parquet files at `gs://my-data-bucket/events/year=2026/`.

**Answers:**

<details>
<summary>Click to reveal</summary>

1. BigQuery reads: `date`, `country`, `amount` (3 columns). The other 7 are not read from storage at all — they are skipped entirely because columnar storage keeps each column in separate blocks.

2. Long-term storage rate ($0.010/GB/month instead of $0.020/GB/month). Tables auto-transition after 90 days without modification.

3. Table snapshots — they store only the delta from the base table, not a full copy. If the table is mostly static, each monthly snapshot is very small.

4.
```sql
CREATE EXTERNAL TABLE `project.dataset.events_2026`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://my-data-bucket/events/year=2026/*.parquet']
);
```

</details>

---

**Next:** [Lesson 03 — Tables, Schemas & Datasets →](03-tables-and-schema.md)
