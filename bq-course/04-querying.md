# Lesson 04 — Querying with GoogleSQL

> **Official docs:** [query syntax](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax) · [functions reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-all)  
> **Time:** ~35 minutes

---

## 4.1 GoogleSQL basics

BigQuery uses **GoogleSQL** — fully ANSI-standard SQL with extensions for arrays, structs, geography, ML, and AI functions.

### The query structure

```sql
SELECT   <expressions>         -- REQUIRED: what to return
FROM     <table>               -- REQUIRED: where to read from
WHERE    <filter condition>    -- optional: filter rows BEFORE grouping
GROUP BY <columns>             -- optional: aggregate
HAVING   <filter condition>    -- optional: filter rows AFTER grouping
ORDER BY <columns>             -- optional: sort
LIMIT    <n>                   -- optional: cap number of rows returned
```

### Your first query — public dataset

BigQuery provides free public datasets. This query runs at no cost (well under the 1 TB/month free tier):

```sql
-- Count trips by payment type in NYC taxi data
SELECT
  payment_type,
  COUNT(*)            AS trip_count,
  AVG(fare_amount)    AS avg_fare
FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022`
WHERE fare_amount > 0
GROUP BY payment_type
ORDER BY trip_count DESC;
```

---

## 4.2 Column selection — always be explicit

```sql
-- BAD: reads all columns, scans maximum data, costs more
SELECT * FROM `project.dataset.orders`;

-- GOOD: reads only what you need
SELECT order_id, country, amount
FROM `project.dataset.orders`;
```

**Why this matters:** BigQuery charges per byte scanned. `SELECT *` on a 10-column table costs 10x more than selecting 1 column. It also makes queries harder to understand.

---

## 4.3 Filtering with WHERE

```sql
-- Basic comparisons
SELECT * FROM orders WHERE country = 'DE';
SELECT * FROM orders WHERE amount > 100;
SELECT * FROM orders WHERE amount BETWEEN 100 AND 500;
SELECT * FROM orders WHERE order_date >= '2026-01-01';

-- Multiple conditions
SELECT * FROM orders
WHERE country = 'DE'
  AND amount > 100
  AND status IN ('COMPLETED', 'SHIPPED');

-- Pattern matching
SELECT * FROM orders WHERE order_id LIKE 'ORD-%';

-- NULL handling
SELECT * FROM orders WHERE campaign IS NULL;
SELECT * FROM orders WHERE campaign IS NOT NULL;

-- NOT
SELECT * FROM orders WHERE country NOT IN ('US', 'CA');
```

### Date filtering (important — affects partition pruning)

```sql
-- Good: filter on DATE column directly
WHERE order_date = '2026-01-15'
WHERE order_date BETWEEN '2026-01-01' AND '2026-01-31'
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)

-- Good: filter on TIMESTAMP column
WHERE created_at >= TIMESTAMP('2026-01-01')
WHERE DATE(created_at) = '2026-01-15'  -- OK for filtering, but breaks partition pruning if partitioned on created_at
```

---

## 4.4 Aggregation functions

```sql
SELECT
  country,
  COUNT(*)                    AS total_orders,
  COUNT(DISTINCT user_id)     AS unique_customers,
  SUM(amount)                 AS total_revenue,
  AVG(amount)                 AS avg_order_value,
  MIN(amount)                 AS smallest_order,
  MAX(amount)                 AS largest_order,
  APPROX_COUNT_DISTINCT(user_id) AS approx_users  -- faster for large tables
FROM `project.analytics.orders`
WHERE order_date >= '2026-01-01'
GROUP BY country
ORDER BY total_revenue DESC;
```

### HAVING — filter after grouping

```sql
-- Only show countries with more than 1000 orders
SELECT
  country,
  COUNT(*) AS order_count
FROM orders
GROUP BY country
HAVING COUNT(*) > 1000
ORDER BY order_count DESC;
```

### ROLLUP — subtotals and grand totals

```sql
-- Revenue by country, campaign, with subtotals per country and grand total
SELECT
  country,
  campaign,
  SUM(amount) AS revenue
FROM orders
WHERE order_date = '2026-01-15'
GROUP BY ROLLUP(country, campaign)
ORDER BY country, campaign;
-- Result includes:
--   country='DE', campaign='spring' → subtotal
--   country='DE', campaign=NULL    → all DE campaigns combined
--   country=NULL, campaign=NULL    → grand total
```

---

## 4.5 Joins

```sql
-- INNER JOIN: only matching rows from both tables
SELECT o.order_id, o.amount, u.email
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;

-- LEFT JOIN: all orders, NULL for users with no match
SELECT o.order_id, o.amount, u.email
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id;

-- Join on multiple columns
SELECT *
FROM orders o
JOIN shipments s
  ON o.order_id = s.order_id
  AND o.country = s.country;
```

### Cross join (cartesian product) — use carefully

```sql
-- Combine every product with every region
SELECT p.product_name, r.region_name
FROM products p
CROSS JOIN regions r;
```

---

## 4.6 Subqueries

```sql
-- Subquery in WHERE
SELECT *
FROM orders
WHERE user_id IN (
  SELECT user_id
  FROM users
  WHERE country = 'DE'
    AND signup_date >= '2025-01-01'
);

-- Subquery in FROM (derived table)
SELECT country, avg_amount
FROM (
  SELECT country, AVG(amount) AS avg_amount
  FROM orders
  GROUP BY country
) avg_by_country
WHERE avg_amount > 200;

-- Correlated subquery (runs once per outer row — use sparingly)
SELECT o.*
FROM orders o
WHERE o.amount > (
  SELECT AVG(amount)
  FROM orders
  WHERE country = o.country
);
```

---

## 4.7 CTEs — Common Table Expressions

CTEs make complex queries readable by breaking them into named steps.

```sql
WITH
  -- Step 1: active users in last 30 days
  active_users AS (
    SELECT DISTINCT user_id
    FROM events
    WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  ),

  -- Step 2: total spend per active user
  user_spend AS (
    SELECT
      o.user_id,
      SUM(o.amount) AS total_spend,
      COUNT(*)      AS order_count
    FROM orders o
    INNER JOIN active_users au USING (user_id)
    WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY o.user_id
  ),

  -- Step 3: classify users
  classified AS (
    SELECT
      user_id,
      total_spend,
      order_count,
      CASE
        WHEN total_spend >= 1000 THEN 'VIP'
        WHEN total_spend >= 200  THEN 'Regular'
        ELSE 'Low-Value'
      END AS tier
    FROM user_spend
  )

-- Final result
SELECT tier, COUNT(*) AS user_count, SUM(total_spend) AS tier_revenue
FROM classified
GROUP BY tier
ORDER BY tier_revenue DESC;
```

---

## 4.8 Window functions

Window functions compute values across a set of rows **without collapsing them** into a single aggregate row.

```
Analogy: GROUP BY is like asking "what's the total for each class?"
Window functions are like asking "what's each student's grade relative to their class average?"
Both results are in the same row.
```

### Syntax

```sql
FUNCTION() OVER (
  PARTITION BY <column>   -- which group (optional)
  ORDER BY <column>       -- within the group, in what order (optional)
  ROWS/RANGE BETWEEN ...  -- which rows to include (optional)
)
```

### Ranking functions

```sql
SELECT
  user_id,
  country,
  total_spend,

  -- RANK: ties get the same rank, next rank skips (1,2,2,4)
  RANK() OVER (PARTITION BY country ORDER BY total_spend DESC) AS rank_in_country,

  -- DENSE_RANK: ties get same rank, next rank doesn't skip (1,2,2,3)
  DENSE_RANK() OVER (PARTITION BY country ORDER BY total_spend DESC) AS dense_rank,

  -- ROW_NUMBER: unique sequential number, ties broken arbitrarily (1,2,3,4)
  ROW_NUMBER() OVER (PARTITION BY country ORDER BY total_spend DESC) AS row_num,

  -- NTILE: divide rows into N buckets (quartiles)
  NTILE(4) OVER (PARTITION BY country ORDER BY total_spend DESC) AS quartile

FROM user_summary;
```

### Aggregate window functions

```sql
SELECT
  order_date,
  country,
  daily_revenue,

  -- Running total (cumulative sum)
  SUM(daily_revenue) OVER (
    PARTITION BY country
    ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_revenue,

  -- 7-day moving average
  AVG(daily_revenue) OVER (
    PARTITION BY country
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS moving_avg_7d,

  -- Percentage of country total
  daily_revenue / SUM(daily_revenue) OVER (PARTITION BY country) AS pct_of_total

FROM daily_summary;
```

### LAG and LEAD — access adjacent rows

```sql
SELECT
  order_date,
  revenue,

  -- Previous day's revenue
  LAG(revenue, 1)  OVER (ORDER BY order_date) AS prev_day_revenue,

  -- Next day's revenue
  LEAD(revenue, 1) OVER (ORDER BY order_date) AS next_day_revenue,

  -- Day-over-day change
  revenue - LAG(revenue, 1) OVER (ORDER BY order_date) AS daily_delta,

  -- Day-over-day % change
  SAFE_DIVIDE(
    revenue - LAG(revenue, 1) OVER (ORDER BY order_date),
    LAG(revenue, 1) OVER (ORDER BY order_date)
  ) * 100 AS pct_change

FROM daily_revenue;
```

### FIRST_VALUE and LAST_VALUE

```sql
SELECT
  user_id,
  event_date,
  event_type,

  -- First event for this user
  FIRST_VALUE(event_type) OVER (
    PARTITION BY user_id
    ORDER BY event_date
  ) AS first_event,

  -- Most recent event for this user
  LAST_VALUE(event_type) OVER (
    PARTITION BY user_id
    ORDER BY event_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS last_event

FROM user_events;
```

---

## 4.9 Querying ARRAY and STRUCT columns

### Access STRUCT fields with dot notation

```sql
-- Table: orders with customer STRUCT
SELECT
  order_id,
  customer.name    AS customer_name,
  customer.country AS customer_country,
  customer.email   AS customer_email
FROM `project.analytics.orders`;
```

### UNNEST — flatten arrays into rows

When a column is an ARRAY, each element becomes its own row using `UNNEST`:

```sql
-- Table: orders with line_items ARRAY<STRUCT<product STRING, qty INT64, price NUMERIC>>
SELECT
  o.order_id,
  item.product,
  item.qty,
  item.price,
  item.qty * item.price AS line_total
FROM `project.analytics.orders` o,
UNNEST(o.line_items) AS item;

-- Result: one row per line item, not per order
```

```sql
-- UNNEST with offset (position in the array)
SELECT
  order_id,
  item_position,
  item.product
FROM orders,
UNNEST(line_items) AS item WITH OFFSET AS item_position
ORDER BY order_id, item_position;
```

---

## 4.10 Useful built-in functions

### String functions

```sql
SELECT
  UPPER(country)                        AS country_upper,
  LOWER(email)                          AS email_lower,
  LENGTH(description)                   AS desc_length,
  SUBSTR(order_id, 5)                   AS id_without_prefix,  -- "ORD-" removed
  CONCAT(first_name, ' ', last_name)    AS full_name,
  TRIM(raw_input)                       AS trimmed,
  REPLACE(phone, '-', '')               AS phone_digits,
  SPLIT(csv_column, ',')                AS as_array,           -- STRING → ARRAY<STRING>
  REGEXP_EXTRACT(url, r'/([^/]+)$')     AS last_path_segment
FROM my_table;
```

### Date functions

```sql
SELECT
  CURRENT_DATE()                                AS today,
  CURRENT_TIMESTAMP()                           AS now,
  DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)     AS thirty_days_ago,
  DATE_ADD(order_date, INTERVAL 14 DAY)         AS due_date,
  DATE_DIFF(end_date, start_date, DAY)          AS days_between,
  EXTRACT(YEAR FROM order_date)                 AS order_year,
  EXTRACT(MONTH FROM order_date)                AS order_month,
  FORMAT_DATE('%B %Y', order_date)              AS month_name,  -- "January 2026"
  DATE_TRUNC(order_date, MONTH)                 AS start_of_month,
  TIMESTAMP_TRUNC(created_at, HOUR)             AS hour_bucket
FROM orders;
```

### CASE expressions

```sql
SELECT
  order_id,
  amount,
  CASE
    WHEN amount >= 1000 THEN 'Large'
    WHEN amount >= 200  THEN 'Medium'
    WHEN amount >= 50   THEN 'Small'
    ELSE 'Micro'
  END AS order_size,

  -- CASE with equality
  CASE status
    WHEN 'COMPLETED' THEN 'Done'
    WHEN 'CANCELLED' THEN 'Cancelled'
    ELSE 'In Progress'
  END AS status_label

FROM orders;
```

### NULL-safe functions

```sql
SELECT
  COALESCE(discount, 0)                 AS discount_or_zero,   -- first non-null value
  IFNULL(campaign, 'direct')            AS campaign_or_direct,
  NULLIF(status, 'UNKNOWN')             AS null_if_unknown,     -- returns NULL if equal
  SAFE_DIVIDE(revenue, session_count)   AS revenue_per_session  -- NULL instead of error on /0
FROM orders;
```

---

## 4.11 EXPLAIN — understanding query cost before running

```bash
# Dry run: estimate bytes scanned without running the query
bq query --dry_run 'SELECT country, SUM(amount) FROM `project.analytics.orders` WHERE order_date = "2026-01-15" GROUP BY country'

# Output: "Query successfully validated. Assuming the tables are not modified, 
# running this query will process 1.23 GB of data."
```

In the Cloud Console, the **query validator** (top right of the editor) shows the bytes estimate in real time as you type.

---

## Practice Exercise 04

**Write SQL queries for the following. Use `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022` (free to query):**

1. Count total trips, average fare, and total revenue grouped by pickup hour (use `EXTRACT(HOUR FROM pickup_datetime)`). Order by pickup hour.

2. Using a window function, show each trip's `fare_amount` and the average `fare_amount` for trips that started in the same hour. Include the difference between the trip fare and the hourly average.

3. Write a CTE that first calculates daily total trips, then in the outer query calculates the 7-day rolling average using a window function.

**Answers:**

<details>
<summary>Click to reveal</summary>

1.
```sql
SELECT
  EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
  COUNT(*)                           AS total_trips,
  AVG(fare_amount)                   AS avg_fare,
  SUM(fare_amount)                   AS total_revenue
FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022`
WHERE fare_amount > 0
GROUP BY pickup_hour
ORDER BY pickup_hour;
```

2.
```sql
SELECT
  pickup_datetime,
  fare_amount,
  EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
  AVG(fare_amount) OVER (
    PARTITION BY EXTRACT(HOUR FROM pickup_datetime)
  ) AS hourly_avg_fare,
  fare_amount - AVG(fare_amount) OVER (
    PARTITION BY EXTRACT(HOUR FROM pickup_datetime)
  ) AS diff_from_avg
FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022`
WHERE fare_amount > 0
  AND DATE(pickup_datetime) = '2022-01-15'
LIMIT 1000;
```

3.
```sql
WITH daily_trips AS (
  SELECT
    DATE(pickup_datetime) AS trip_date,
    COUNT(*) AS daily_count
  FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022`
  WHERE EXTRACT(YEAR FROM pickup_datetime) = 2022
  GROUP BY trip_date
)
SELECT
  trip_date,
  daily_count,
  AVG(daily_count) OVER (
    ORDER BY trip_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rolling_avg_7d
FROM daily_trips
ORDER BY trip_date;
```

</details>

---

**Next:** [Lesson 05 — Partitioning & Clustering →](05-partitioning-and-clustering.md)
