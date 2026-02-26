# Lesson 06 — Pricing, Security & Operations

> **Official docs:** [pricing](https://cloud.google.com/bigquery/pricing) · [IAM](https://cloud.google.com/bigquery/docs/access-control) · [bq CLI](https://cloud.google.com/bigquery/docs/reference/bq-cli-reference) · [reservations](https://cloud.google.com/bigquery/docs/reservations-intro)  
> **Time:** ~30 minutes

---

## 6.1 The two things you pay for

BigQuery charges for two things separately:

```
Total Cost = Storage Cost + Compute Cost

Storage Cost = bytes stored × rate per GB/month
Compute Cost = bytes scanned by queries × rate per TiB  (on-demand)
            OR slot-hours reserved × rate per slot-hour (capacity pricing)
```

They are completely independent. A query that scans a lot of data but stores little will have low storage cost and high compute cost. A huge data warehouse that runs few queries will have high storage cost and low compute cost.

---

## 6.2 Storage pricing

### Logical storage billing (default)

| Type | Price |
|------|-------|
| Active storage | $0.020 per GB/month |
| Long-term storage | $0.010 per GB/month |

**Long-term storage** is automatic — any table or partition that hasn't been modified for **90 consecutive days** drops to the long-term rate. No action required. Inserting new rows or running `UPDATE`/`DELETE` resets the clock.

```
100 GB table, last modified 4 months ago:
  Active rate:    100 GB × $0.020 = $2.00/month
  Long-term rate: 100 GB × $0.010 = $1.00/month  ← automatic
```

### Physical storage billing (optional)

Pay for actual compressed bytes on disk instead of logical size. Also incurs:
- **Time travel storage:** Additional charge for the time travel window (default 7 days, configurable 2–7 days)
- **Fail-safe storage:** Additional 7-day window (fixed, not configurable, charged at active rate)

Physical billing is worth it when your data compresses well (Parquet-like repeated values). For random strings and floats, logical billing may be cheaper.

**Set at the dataset level:**
```bash
bq update --storage_billing_model=PHYSICAL my-project:analytics
```

---

## 6.3 Compute pricing — on-demand

You pay per byte scanned by your queries.

```
On-demand price: $6.25 per TiB scanned

Examples:
  Query scans 100 GB  → (100 / 1024) TiB × $6.25 = $0.61
  Query scans 1 TB    → $6.25
  Query scans 10 TB   → $62.50
```

**What's always free:**
- Batch loading data (from GCS, Drive, etc.)
- Exporting data to Cloud Storage
- Metadata operations (`CREATE TABLE`, `DROP`, schema changes)
- Cached query results (same query within 24 hours = $0)
- Queries on metadata (`INFORMATION_SCHEMA`)
- First 1 TiB of queries per month (free tier)
- First 10 GB of storage per month (free tier)

**What reduces cost:**
1. Partition pruning (scan less data)
2. Clustering (scan less data within partitions)
3. SELECT only needed columns (columnar = only read columns you select)
4. Set query results caching on (identical queries = $0)

---

## 6.4 Compute pricing — BigQuery Editions (capacity)

Instead of paying per byte, you can buy **slots** — units of compute capacity that your queries share. All queries run against your reserved slot pool.

### What is a slot?

A slot is roughly one virtual CPU. More slots = more parallel computation = faster queries. Complex queries on huge tables need thousands of slots to run in seconds.

### BigQuery Editions

From the official docs, there are three Editions as of 2026:

| Edition | Commitment | Key features |
|---------|-----------|--------------|
| **Standard** | Per-second auto-scale | Basic analytics, developer workloads |
| **Enterprise** | 1-year commitment | CMEK, 99.99% SLA, BI Engine included |
| **Enterprise+** | 1-year commitment | Everything in Enterprise + cross-region DR, Assured Workloads |

### On-demand vs Editions — when to use each

```
On-demand wins when:
  - Query volume is unpredictable or low
  - You're in development / testing
  - Monthly spend < ~$2,000
  - You want zero commitment

Editions win when:
  - Heavy, predictable daily query workload
  - Many analysts querying all day
  - Monthly on-demand bill > $2,000
  - You need cost predictability (no bill spikes)
  - You need SLA guarantees for production
```

### Custom quotas (cost control)

```bash
# Set a per-user or per-project daily limit on bytes billed
# Prevents a runaway query from scanning your entire data lake

bq mk --transfer_config \
  --project_id=my-project \
  --data_source=cross_region_copy \
  ...

# Or via Console: IAM → Quotas → Bytes billed per day
```

---

## 6.5 IAM — Identity and Access Management

BigQuery uses Google Cloud IAM for access control.

### Predefined BigQuery roles

| Role | What they can do |
|------|-----------------|
| `roles/bigquery.admin` | Full control — create/delete datasets, tables, jobs, manage others |
| `roles/bigquery.dataOwner` | Full CRUD on tables and datasets they own |
| `roles/bigquery.dataEditor` | Read + write data; create/update/delete tables |
| `roles/bigquery.dataViewer` | Read-only data access |
| `roles/bigquery.jobUser` | Run queries and jobs (needs dataViewer separately) |
| `roles/bigquery.user` | Run queries; create own datasets and jobs |
| `roles/bigquery.readSessionUser` | Use the Storage Read API |

> **Tip:** `bigquery.jobUser` + `bigquery.dataViewer` is the minimum needed to run queries and see results. `bigquery.user` is a slightly broader version that also allows creating datasets.

### IAM hierarchy — where to grant access

Access can be granted at multiple levels (more specific takes precedence):

```
Organization level
  └── Project level     ← most common for all-or-nothing access
        └── Dataset level ← most common for per-dataset access
              └── Table level ← fine-grained (specific tables)
                    └── Column level (policy tags)
                    └── Row level (row access policies)
```

**Grant access to a dataset:**
```bash
# Grant dataViewer to a user on one dataset
bq add-iam-policy-binding \
  --member="user:alice@company.com" \
  --role="roles/bigquery.dataViewer" \
  my-project:analytics
```

**Grant access to a specific table:**
```bash
bq add-iam-policy-binding \
  --member="serviceAccount:pipeline@my-project.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  my-project:analytics.orders
```

---

## 6.6 Column-level security (policy tags)

Hide specific columns (PII like SSN, email, credit card) from users who don't have the right role. Unauthorised users see `NULL` for those columns.

```
Setup in Data Catalog:
1. Create a taxonomy (e.g., "PII")
2. Create policy tags (e.g., "Sensitive", "Highly Sensitive")
3. Assign the policy tag to columns in BigQuery
4. Grant "Fine-Grained Reader" role to users/groups who need real values

Effect:
  user with Fine-Grained Reader → sees real SSN value
  user without it              → sees NULL
```

---

## 6.7 Row-level security

Restrict which rows a user can see using **row access policies**. Different users/groups see different subsets of the same table.

```sql
-- Create a row access policy: EU team only sees EU rows
CREATE ROW ACCESS POLICY eu_only
ON `project.analytics.orders`
GRANT TO ("group:eu-analytics@company.com")
FILTER USING (region = 'EU');

-- Create another: US team only sees US rows
CREATE ROW ACCESS POLICY us_only
ON `project.analytics.orders`
GRANT TO ("group:us-analytics@company.com")
FILTER USING (region = 'US');

-- Admin users (not in either group) need an "all rows" policy:
CREATE ROW ACCESS POLICY all_rows
ON `project.analytics.orders`
GRANT TO ("group:data-admins@company.com")
FILTER USING (TRUE);
```

> **Important:** If a table has row access policies, a user with **no matching policy sees zero rows** — not an error, just an empty result set. Always create an admin policy for super-users.

---

## 6.8 The bq command-line tool

The `bq` CLI is the most important tool for scripting and automation.

### Installation

Included with the **Google Cloud SDK** (`gcloud`). Install from [cloud.google.com/sdk](https://cloud.google.com/sdk).

```bash
gcloud auth login            # authenticate
gcloud config set project my-project
```

### Common bq commands

```bash
# Run a query
bq query --use_legacy_sql=false \
  'SELECT country, SUM(amount) FROM `my-project.analytics.orders`
   WHERE order_date = "2026-01-15" GROUP BY country'

# Dry run (estimate bytes without running)
bq query --dry_run --use_legacy_sql=false \
  'SELECT * FROM `my-project.analytics.orders` WHERE order_date = "2026-01-15"'

# List datasets in a project
bq ls my-project:

# List tables in a dataset
bq ls my-project:analytics

# Show table schema
bq show --schema my-project:analytics.orders

# Show table info (size, rows, creation time)
bq show my-project:analytics.orders

# Create a dataset
bq mk --dataset --location=US my-project:new_dataset

# Load CSV from GCS
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  my-project:analytics.orders \
  gs://my-bucket/orders.csv

# Export table to GCS
bq extract \
  --destination_format=PARQUET \
  my-project:analytics.orders \
  gs://my-bucket/exports/orders_*.parquet

# Copy a table
bq cp my-project:analytics.orders my-project:backup.orders_backup

# Delete a table
bq rm -f -t my-project:analytics.old_table

# Run a query and save results to a table
bq query --use_legacy_sql=false \
  --destination_table=my-project:analytics.results \
  --replace \
  'SELECT country, SUM(amount) FROM `my-project.analytics.orders`
   WHERE order_date >= "2026-01-01" GROUP BY country'
```

---

## 6.9 Jobs — how BigQuery tracks work

Every operation in BigQuery (query, load, export, copy) is a **Job**. Jobs are asynchronous — you submit them and BigQuery runs them. The Jobs API lets you track status, cancel jobs, and audit what happened.

```bash
# List recent jobs
bq ls -j --max_results=20 my-project

# Show details of a specific job (including bytes processed, duration)
bq show -j my-project:bqjob_r123456789_00001234

# Cancel a running job
bq cancel my-project:bqjob_r123456789_00001234
```

```sql
-- Query the jobs audit log via INFORMATION_SCHEMA
SELECT
  job_id,
  user_email,
  query,
  total_bytes_processed,
  total_bytes_billed,
  total_slot_ms,
  TIMESTAMP_DIFF(end_time, start_time, SECOND) AS duration_seconds,
  error_result.reason AS error,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE DATE(creation_time) = CURRENT_DATE()
  AND job_type = 'QUERY'
ORDER BY total_bytes_billed DESC
LIMIT 20;
```

---

## 6.10 Quick cost estimation cheatsheet

Before running a query:

```
1. Estimate partitions touched:
   - If 3-year table, daily partitioned, and query is "last 7 days" → 7/1095 = 0.6% of data

2. Estimate columns touched:
   - If 20-column table and query selects 4 columns → 4/20 = 20% of each partition

3. Estimate bytes:
   - Total table size × partition fraction × column fraction

4. Estimate cost:
   - bytes_in_TiB × $6.25

Example:
  Table: 10 TB, 20 columns, 3 years daily partitioned
  Query: SELECT 4 columns WHERE date = last 7 days AND country = 'DE'
  Partitions touched: 7/1095 = 64 GB
  Columns touched: 4/20 = 12.8 GB
  Country filter (cluster): ~10% of rows → 1.28 GB
  Cost: 1.28 GB / 1024 × $6.25 = $0.0078
```

---

## Summary: All 6 Lessons at a Glance

| Topic | Key takeaway |
|-------|-------------|
| **What is BigQuery** | Serverless OLAP warehouse: compute + storage separated, Dremel engine, pay per byte |
| **Storage** | Columnar format (Capacitor), 11 nines durability, logical vs physical billing, time travel |
| **Tables & Schema** | Projects → Datasets → Tables; NUMERIC for money; STRUCT/ARRAY for nested data |
| **Querying** | GoogleSQL: always SELECT specific columns; window functions; CTEs for readability |
| **Partitioning & Clustering** | Partition prunes whole partitions; cluster prunes blocks within; never wrap partition column in a function |
| **Pricing & Security** | On-demand = $6.25/TiB; Editions = slot-hours; IAM at every level; row/column security |

---

## Practice Exercise 06

**Final challenge — no code hints this time:**

You're a data engineer at an e-commerce company. You have:
- `orders` table: 5 TB, 15 columns, 3 years of daily data, ~500K rows/day
- Analysts query "last 30 days", always filter by `country`, often group by `campaign`
- The BI dashboard runs 200 queries/day, all the same structure
- Finance team should ONLY see their own region's data
- The `customer_email` column must be hidden from most analysts

Design the complete BigQuery setup:
1. What partitioning strategy?
2. What clustering columns?
3. On-demand or Editions? Why?
4. What IAM setup for finance team?
5. How to handle the `customer_email` restriction?
6. What BigQuery feature eliminates 200 identical dashboard queries?

<details>
<summary>Click to reveal answers</summary>

1. **Partition by `order_date` (daily)** — analysts always query by date, 30-day window → scans 30/1095 = 2.7% of data.

2. **Cluster by `country`, `campaign`** — both are common filters/group-by columns. Up to 4 columns allowed.

3. **Editions** — 200 queries/day from BI tools is heavy and predictable. On-demand would be expensive and unpredictable. Commit to Enterprise for SLA + CMEK.

4. **Row Access Policies** — one policy per region:
   ```sql
   CREATE ROW ACCESS POLICY finance_eu ON orders
   GRANT TO ("group:finance-eu@company.com")
   FILTER USING (region = 'EU');
   ```

5. **Column-level security with policy tags** — tag `customer_email` as "PII". Only users with the "Fine-Grained Reader" role see real values. Others see NULL.

6. **Materialized Views** — pre-compute the dashboard aggregation. BigQuery automatically rewrites matching queries to use the cached result, so 200 queries become effectively 0 scanned bytes after the first one.

</details>

---

## 🎉 Course Complete!

You've covered the entire BigQuery fundamentals track based on the official documentation.

**What to do next:**
1. **Practice in the sandbox:** [cloud.google.com/bigquery/docs/sandbox](https://cloud.google.com/bigquery/docs/sandbox) (free)
2. **Explore public datasets:** Query real data at `bigquery-public-data.*`
3. **Read your existing study doc:** `docs/11-bigquery-from-scratch.md` in this repo has deeper architectural detail
4. **Official reference SQL:** [cloud.google.com/bigquery/docs/reference/standard-sql/functions-all](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-all)
