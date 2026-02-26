# Lesson 03 — Tables, Schemas & Datasets

> **Official docs:** [tables](https://cloud.google.com/bigquery/docs/tables) · [datasets](https://cloud.google.com/bigquery/docs/datasets-intro) · [resource hierarchy](https://cloud.google.com/bigquery/docs/resource-hierarchy)  
> **Time:** ~25 minutes

---

## 3.1 The resource hierarchy

BigQuery organises everything into three levels:

```
Google Cloud Organization
  └── Project  (billing, IAM, quotas)
        └── Dataset  (region, namespace, access control)
              ├── Table
              ├── View
              ├── Materialized View
              └── Routine (UDFs, stored procedures)
```

### Project
- The billing boundary — all BigQuery charges accumulate here
- The IAM boundary — project-level roles apply to all datasets inside
- Every resource in GCP lives in exactly one project

### Dataset
- A namespace for tables — like a schema/database in traditional SQL
- **Defines the geographic region** where data is physically stored (set at creation, cannot change)
- Access control is most commonly applied here
- You can share a dataset across projects

```sql
-- Create a dataset in EU region
CREATE SCHEMA `my-project.analytics`
OPTIONS (location = 'EU', default_table_expiration_days = 365);
```

### Table
- Where data actually lives
- Belongs to exactly one dataset
- Has a schema (column names + types)

---

## 3.2 Fully-qualified table names

BigQuery uses backtick-quoted, dot-separated names:

```sql
`project-id.dataset_name.table_name`

-- Examples:
`my-company.analytics.orders`
`my-company.raw_data.events_2026`
`bigquery-public-data.stackoverflow.posts_questions`  -- public dataset
```

**In queries, the project is optional if you're querying your own project:**

```sql
-- These are equivalent if you're in project "my-company":
SELECT * FROM `my-company.analytics.orders`
SELECT * FROM `analytics.orders`
```

---

## 3.3 Data types

BigQuery uses **GoogleSQL** types. Full reference: [cloud.google.com/bigquery/docs/reference/standard-sql/data-types](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types)

### Numeric types

| Type | Range / Precision | Use for |
|------|------------------|---------|
| `INT64` | -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 | IDs, counts |
| `FLOAT64` | 64-bit IEEE 754 floating point | Scientific data (approximate) |
| `NUMERIC` | 29 digits, 9 decimal places | Money, finance (exact) |
| `BIGNUMERIC` | 76 digits, 38 decimal places | High-precision finance |

> **Always use `NUMERIC` for money, never `FLOAT64`** — floating point can introduce tiny rounding errors.

### String and byte types

| Type | Notes |
|------|-------|
| `STRING` | Variable-length UTF-8 text, up to 16 MB |
| `BYTES` | Variable-length binary data, up to 16 MB |

### Date and time types

| Type | Format | Example |
|------|--------|---------|
| `DATE` | YYYY-MM-DD | `2026-01-15` |
| `TIME` | HH:MM:SS[.fraction] | `09:30:00` |
| `DATETIME` | DATE + TIME, no timezone | `2026-01-15T09:30:00` |
| `TIMESTAMP` | DATE + TIME + timezone (always UTC) | `2026-01-15 09:30:00 UTC` |

> **Use `TIMESTAMP` for event tracking** — it stores absolute time. Use `DATETIME` for things like "appointment at 9am" where the timezone isn't relevant.

### Complex types

| Type | Description | Example |
|------|-------------|---------|
| `BOOL` | true/false | `true` |
| `ARRAY<T>` | Ordered list of values of type T | `[1, 2, 3]` |
| `STRUCT<fields>` | Named record with typed fields (also called RECORD) | `STRUCT<city STRING, zip STRING>` |
| `JSON` | Semi-structured JSON value | `{"key": "val"}` |
| `GEOGRAPHY` | Geographic points, lines, polygons | Used for geospatial queries |

---

## 3.4 Creating tables

### DDL: CREATE TABLE

```sql
-- Basic table
CREATE TABLE `my-project.analytics.orders`
(
  order_id   STRING    NOT NULL,
  user_id    INT64     NOT NULL,
  country    STRING,
  amount     NUMERIC,
  status     STRING,
  created_at TIMESTAMP
);
```

### Column modes

Each column can have a mode:

| Mode | Meaning | Notes |
|------|---------|-------|
| `NULLABLE` | NULL values allowed | Default |
| `REQUIRED` | NULL not allowed | More efficient, enforces data quality |
| `REPEATED` | Array of values | Used for ARRAY columns |

```sql
CREATE TABLE `my-project.analytics.events`
(
  event_id    STRING    NOT NULL,  -- REQUIRED
  user_id     INT64,               -- NULLABLE (default)
  tags        ARRAY<STRING>,       -- REPEATED
  properties  JSON
);
```

### Nested and repeated fields (STRUCT + ARRAY)

This is a BigQuery superpower that traditional databases can't do natively:

```sql
CREATE TABLE `my-project.analytics.orders_nested`
(
  order_id  STRING NOT NULL,
  customer  STRUCT<
    name    STRING,
    email   STRING,
    country STRING
  >,
  line_items ARRAY<STRUCT<
    product_id STRING,
    product_name STRING,
    quantity   INT64,
    unit_price NUMERIC
  >>
);
```

This stores a full order (with customer and all line items) in a single row — no JOINs needed. Faster queries, simpler schema.

---

## 3.5 Loading data into a table

### From Cloud Storage (batch load)

```bash
# Load CSV file from GCS
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  my-project:analytics.orders \
  gs://my-bucket/orders/orders_2026_01.csv \
  order_id:STRING,user_id:INTEGER,country:STRING,amount:NUMERIC,created_at:TIMESTAMP
```

```bash
# Load Parquet (schema is inferred automatically)
bq load \
  --source_format=PARQUET \
  my-project:analytics.orders \
  gs://my-bucket/orders/*.parquet
```

### With Python client

```python
from google.cloud import bigquery

client = bigquery.Client(project="my-project")

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
)

with open("orders.parquet", "rb") as f:
    load_job = client.load_table_from_file(
        f,
        destination="my-project.analytics.orders",
        job_config=job_config,
    )

load_job.result()  # Wait for completion
print(f"Loaded {load_job.output_rows} rows")
```

### INSERT directly in SQL

```sql
-- Insert a single row
INSERT INTO `my-project.analytics.orders` (order_id, user_id, country, amount, created_at)
VALUES ('ORD-999', 12345, 'DE', 450.00, CURRENT_TIMESTAMP());

-- Insert results of a query
INSERT INTO `my-project.analytics.orders_archive`
SELECT * FROM `my-project.analytics.orders`
WHERE DATE(created_at) < '2025-01-01';
```

---

## 3.6 Modifying tables

### Add a column

```sql
ALTER TABLE `my-project.analytics.orders`
ADD COLUMN discount_pct FLOAT64;
```

### Rename a column (newer BigQuery feature)

```sql
ALTER TABLE `my-project.analytics.orders`
RENAME COLUMN discount_pct TO discount_percent;
```

### Delete rows

```sql
-- Delete old records (DML — can be expensive on large tables)
DELETE FROM `my-project.analytics.orders`
WHERE DATE(created_at) < '2024-01-01';
```

### Update values

```sql
UPDATE `my-project.analytics.orders`
SET status = 'CANCELLED'
WHERE order_id = 'ORD-001'
  AND DATE(created_at) = '2026-01-15';
```

> **Note:** BigQuery DML (UPDATE, DELETE, MERGE) is not free — it counts as data processed. Use it sparingly. BigQuery is optimised for appending new data and querying, not frequent row-level updates.

---

## 3.7 Views

A view is a saved SQL query. No data is stored — the query runs every time you query the view.

```sql
-- Create a view that exposes only non-PII columns
CREATE VIEW `my-project.analytics.orders_safe` AS
SELECT
  order_id,
  country,
  amount,
  DATE(created_at) AS order_date
FROM `my-project.analytics.orders`
WHERE status != 'CANCELLED';
```

**Authorized views** let a view access data in another dataset without granting the viewer direct access to the underlying tables — useful for data sharing with security.

---

## 3.8 INFORMATION_SCHEMA — metadata queries

BigQuery exposes metadata about tables, columns, jobs, and storage via `INFORMATION_SCHEMA` views:

```sql
-- List all tables in a dataset
SELECT table_name, table_type, creation_time, row_count, size_bytes
FROM `my-project.analytics.INFORMATION_SCHEMA.TABLES`;

-- List columns for a specific table
SELECT column_name, data_type, is_nullable
FROM `my-project.analytics.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders';

-- See recent queries and their costs
SELECT
  job_id,
  user_email,
  total_bytes_processed,
  total_bytes_billed,
  creation_time,
  query
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE DATE(creation_time) = CURRENT_DATE()
ORDER BY creation_time DESC
LIMIT 20;
```

---

## Practice Exercise 03

**Write the SQL for these tasks:**

1. Create a table called `campaigns` in dataset `marketing` with columns: `campaign_id` (STRING, required), `name` (STRING), `country` (STRING), `budget` (NUMERIC), `start_date` (DATE), `end_date` (DATE), `is_active` (BOOL).

2. Write a query to list all tables in the `analytics` dataset and their row counts.

3. The `orders` table has a STRUCT column `customer` with fields `name` (STRING) and `country` (STRING). Write a query that selects `order_id`, `customer.name`, and `customer.country` from the table.

4. Add a new column `channel` (STRING) to the `campaigns` table.

**Answers:**

<details>
<summary>Click to reveal</summary>

1.
```sql
CREATE TABLE `my-project.marketing.campaigns`
(
  campaign_id STRING NOT NULL,
  name        STRING,
  country     STRING,
  budget      NUMERIC,
  start_date  DATE,
  end_date    DATE,
  is_active   BOOL
);
```

2.
```sql
SELECT table_name, row_count, size_bytes
FROM `my-project.analytics.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name;
```

3.
```sql
SELECT
  order_id,
  customer.name    AS customer_name,
  customer.country AS customer_country
FROM `my-project.analytics.orders`;
```

4.
```sql
ALTER TABLE `my-project.marketing.campaigns`
ADD COLUMN channel STRING;
```

</details>

---

**Next:** [Lesson 04 — Querying with GoogleSQL →](04-querying.md)
