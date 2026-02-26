# Lesson 05 — Partitioning & Clustering

> **Official docs:** [partitioned tables](https://cloud.google.com/bigquery/docs/partitioned-tables) · [clustered tables](https://cloud.google.com/bigquery/docs/clustered-tables)  
> **Time:** ~30 minutes

---

## 5.1 Why they exist

Without partitioning and clustering, every query scans the entire table — all rows, all bytes, full cost.

```
Table: 18 TB of daily orders (3 years of data, one million rows/day)

Query: "Show me Germany orders from last week"
  Without optimization → scans 18 TB   → costs $112.50
  With partitioning    → scans ~250 GB  → costs $1.56
  With both            → scans ~25 GB   → costs $0.16
```

These two techniques are the **highest-ROI optimisations** in BigQuery.

---

## 5.2 Partitioning

### What it is

A partitioned table is divided into segments (**partitions**) based on a column's value. Each partition is stored as a separate physical block.

From the official docs:
> *"If a query uses a qualifying filter on the value of the partitioning column, BigQuery can scan the partitions that match the filter and skip the remaining partitions. This process is called pruning."*

```
Without partitioning:
  [ all 18 TB in one block — every query touches everything ]

With DATE partitioning:
  [ Jan 1 partition ]  [ Jan 2 partition ]  ... [ Dec 31 partition ]
  
  Query WHERE date = '2026-01-15' → only reads the Jan 15 partition
  The other 364 partitions are never touched
```

### The 3 types of partitioning

#### Type 1: Time-unit column partitioning (most common)

Partition by a `DATE`, `TIMESTAMP`, or `DATETIME` column that exists in your table.

```sql
CREATE TABLE `project.analytics.orders`
(
  order_id   STRING NOT NULL,
  user_id    INT64,
  country    STRING,
  amount     NUMERIC,
  order_date DATE              -- this column becomes the partition key
)
PARTITION BY order_date;       -- daily partitions by default
```

Granularity options:
- `PARTITION BY DATE_TRUNC(order_date, HOUR)` — hourly (use for high-volume, short date ranges)
- `PARTITION BY order_date` — daily (default, most common)
- `PARTITION BY DATE_TRUNC(order_date, MONTH)` — monthly (use for sparse data or wide date ranges)
- `PARTITION BY DATE_TRUNC(order_date, YEAR)` — yearly

From the docs:
> *"Choose hourly partitioning if your tables have a high volume of data that spans a short date range — typically less than six months of timestamp values."*
> *"Choose monthly or yearly partitioning if your tables have a relatively small amount of data for each day, but span a wide date range."*

#### Type 2: Ingestion-time partitioning

BigQuery automatically assigns each row to a partition based on when the row was loaded into the table. You don't need a date column.

```sql
CREATE TABLE `project.analytics.events`
(
  event_id  STRING,
  user_id   INT64,
  data      JSON
)
PARTITION BY _PARTITIONDATE;   -- special pseudocolumn
```

Query using the pseudocolumn:
```sql
SELECT *
FROM `project.analytics.events`
WHERE _PARTITIONDATE = '2026-01-15';
```

Use this when your source data doesn't have a reliable timestamp column.

#### Type 3: Integer range partitioning

Partition by an INTEGER column divided into ranges.

```sql
CREATE TABLE `project.analytics.customers`
(
  customer_id  INT64 NOT NULL,
  name         STRING,
  country      STRING
)
PARTITION BY RANGE_BUCKET(customer_id, GENERATE_ARRAY(0, 1000000, 10000));
-- Creates partitions: 0-9999, 10000-19999, 20000-29999, ..., 990000-999999
```

Use for sharding by user ID, account ID, or other integer identifiers.

---

## 5.3 Working with partitioned tables

### Require partition filters (cost guardrail)

```sql
CREATE TABLE `project.analytics.orders`
(...)
PARTITION BY order_date
OPTIONS (require_partition_filter = TRUE);
-- Any query without a partition filter will fail with an error
-- Protects against accidental full-table scans
```

### Set partition expiry (automatic cleanup)

```sql
CREATE TABLE `project.analytics.raw_events`
(...)
PARTITION BY _PARTITIONDATE
OPTIONS (partition_expiration_days = 90);
-- Partitions older than 90 days are automatically deleted
-- Great for raw data that doesn't need to be kept forever
```

### Query specific partitions

```sql
-- Filter on the partition column → BigQuery prunes automatically
SELECT * FROM orders WHERE order_date = '2026-01-15';

-- Range of partitions
SELECT * FROM orders WHERE order_date BETWEEN '2026-01-01' AND '2026-01-31';

-- Partition decorator: directly address a partition in bq CLI
bq head 'my_dataset.orders$20260115'

-- Load data into a specific partition
bq load --time_partitioning_field=order_date \
  'project:analytics.orders$20260115' \
  gs://bucket/orders_jan15.csv
```

### THE MOST IMPORTANT RULE: never wrap the partition column in a function

```sql
-- ❌ WRONG — BigQuery cannot prune; full table scan
WHERE DATE(created_at) = '2026-01-15'
WHERE FORMAT_DATE('%Y-%m', order_date) = '2026-01'
WHERE EXTRACT(YEAR FROM order_date) = 2026

-- ✅ CORRECT — partition pruning works
WHERE created_at BETWEEN '2026-01-15 00:00:00' AND '2026-01-15 23:59:59'
WHERE order_date = '2026-01-15'
WHERE order_date BETWEEN '2026-01-01' AND '2026-01-31'
WHERE DATE_TRUNC(order_date, MONTH) = '2026-01-01'  -- this one is OK (BQ optimises it)
```

---

## 5.4 Clustering

### What it is

Clustering sorts data within each partition (or within the whole table) by the values of up to **4 clustering columns**. BigQuery stores the sorted data in blocks and records min/max values for each block.

When a query filters on a clustering column, BigQuery skips blocks that can't match — without reading them.

From the official docs:
> *"When you run a query that filters by the clustered column, BigQuery only scans the relevant blocks based on the clustered columns instead of the entire table or table partition."*

```
Partition: Jan 15, 2026 (250 GB)
  Without clustering:  all 250 GB mixed together
  With CLUSTER BY country, campaign:
    [ Block 1: DE/spring-sale ]  [ Block 2: DE/winter-promo ]
    [ Block 3: FR/spring-sale ]  [ Block 4: US/summer ]  ...
    
  Query WHERE country='DE' AND campaign='spring-sale'
    → reads only Block 1 (maybe 5 GB), skips rest
```

### Creating a clustered table

```sql
-- Partitioned AND clustered (the standard pattern)
CREATE TABLE `project.analytics.orders`
(
  order_id   STRING NOT NULL,
  user_id    INT64,
  country    STRING,
  campaign   STRING,
  category   STRING,
  amount     NUMERIC,
  order_date DATE
)
PARTITION BY order_date        -- partition first (by date)
CLUSTER BY country, campaign;  -- then sort within partitions (up to 4 columns)
```

### Cluster-only table (no partition)

```sql
-- When table is small (<10 GB) or doesn't have a natural date column
CREATE TABLE `project.analytics.products`
(
  product_id   STRING NOT NULL,
  category     STRING,
  brand        STRING,
  price        NUMERIC
)
CLUSTER BY category, brand;
```

### Choosing clustering columns

Order matters — the first column is sorted first:

```sql
CLUSTER BY country, campaign, category
```

- Filter on `country` alone → cluster pruning works ✅
- Filter on `country` AND `campaign` → cluster pruning works even better ✅
- Filter on `campaign` alone (no `country`) → cluster pruning is less effective ⚠️

**Good clustering columns:**
- Columns you frequently filter on in `WHERE`
- Columns you frequently `GROUP BY`
- High-cardinality columns (many distinct values = better block elimination)

**Bad clustering columns:**
- Boolean flags (only 2 values — blocks would be huge)
- Columns you never filter on

---

## 5.5 Partitioning vs Clustering — when to use which

From the official docs:

> *"Consider clustering a table instead of partitioning a table in the following circumstances:*
> - *You need more granularity than partitioning allows*
> - *Your queries commonly use filters or aggregation against multiple columns*
> - *The cardinality of the number of values in a column or group of columns is large*
> - *You don't need strict cost estimates before query execution"*

| Situation | Solution |
|-----------|----------|
| You always filter by date | Partition by date |
| You always filter by date AND country | Partition by date + cluster by country |
| You filter by user_id (millions of users) | Cluster by user_id (too many partitions for partitioning) |
| Table < 1 GB | Neither — overhead not worth it |
| You need cost estimate before running | Partitioning (clustering doesn't enable dry-run cost estimation) |
| Many DML operations per day | Clustering (partitioning has modification quotas) |

### Partitioning vs sharding (table naming)

From the official docs:
> *"Table sharding is the practice of storing data in multiple tables, using a naming prefix such as `[PREFIX]_YYYYMMDD`. Partitioning is recommended over table sharding, because partitioned tables perform better."*

```sql
-- ❌ OLD WAY: separate tables per day (sharding)
orders_20260115
orders_20260116
orders_20260117
-- Problem: BigQuery must load metadata/permissions for each table in a JOIN

-- ✅ NEW WAY: one partitioned table
orders  (PARTITION BY order_date)
-- Better performance, simpler schema, single permission grant
```

---

## 5.6 Practical cost savings example

Setup: 3 years of daily e-commerce orders, 10 TB total, 10 columns.

| Configuration | Bytes scanned for "Germany last week" | Monthly query cost (100 runs/day) |
|--------------|---------------------------------------|----------------------------------|
| No partition, no cluster | 10 TB × 100% = 10 TB | $62.50/day → $1,875/month |
| Partition by day | 10 TB × (7/1095) = 64 GB | $0.40/day → $12/month |
| Partition + cluster by country | 64 GB × ~10% = 6.4 GB | $0.04/day → $1.20/month |
| **Savings** | **1,560x less data** | **$1,874 → $1.20/month** |

---

## 5.7 Monitoring partition and cluster effectiveness

```sql
-- Check if your query used partition pruning
-- After running a query, go to "Execution details" in the console
-- Look for "partitions read" vs "total partitions"

-- Check how many partitions a table has
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes
FROM `project.analytics.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'orders'
ORDER BY partition_id DESC;

-- Check clustering columns for a table
SELECT
  table_name,
  clustering_ordinal_position,
  column_name
FROM `project.analytics.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders'
  AND clustering_ordinal_position IS NOT NULL
ORDER BY clustering_ordinal_position;
```

---

## Practice Exercise 05

**Tasks:**

1. Write the `CREATE TABLE` DDL for a `page_views` table with these columns: `session_id` (STRING), `user_id` (INT64), `country` (STRING), `page_url` (STRING), `referrer` (STRING), `view_timestamp` (TIMESTAMP). Partition by day (using the timestamp column) and cluster by country, then page_url.

2. You have the partitioned+clustered `page_views` table. Which of these queries will benefit from partition pruning AND cluster pruning? Which won't?

   a. `WHERE DATE(view_timestamp) = '2026-01-15' AND country = 'DE'`  
   b. `WHERE view_timestamp BETWEEN '2026-01-15 00:00:00' AND '2026-01-15 23:59:59' AND country = 'DE'`  
   c. `WHERE country = 'DE'`  
   d. `WHERE page_url = '/checkout'`

3. You have 500 million rows per day but you only ever query the last 7 days. What `OPTIONS` would you add to the table to automatically clean up old partitions?

**Answers:**

<details>
<summary>Click to reveal</summary>

1.
```sql
CREATE TABLE `project.analytics.page_views`
(
  session_id     STRING NOT NULL,
  user_id        INT64,
  country        STRING,
  page_url       STRING,
  referrer       STRING,
  view_timestamp TIMESTAMP
)
PARTITION BY DATE(view_timestamp)
CLUSTER BY country, page_url;
```

2.
- a. ❌ `DATE(view_timestamp)` wraps the partition column in a function — **no partition pruning**. But cluster pruning on `country` works.
- b. ✅ Direct TIMESTAMP range filter — **partition pruning works**. Cluster pruning on `country` also works. Best option.
- c. ⚠️ No partition filter — full table scan across all days. Cluster pruning on `country` works within each partition, but you still read all partitions.
- d. ⚠️ No partition filter, and `page_url` is the *second* clustering column. Without filtering on `country` first, cluster pruning on `page_url` is less effective.

3.
```sql
OPTIONS (partition_expiration_days = 7)
-- Partitions older than 7 days are automatically deleted
```

</details>

---

**Next:** [Lesson 06 — Pricing, Security & Operations →](06-pricing-security-and-operations.md)
