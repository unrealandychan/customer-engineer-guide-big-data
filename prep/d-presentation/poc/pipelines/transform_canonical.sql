-- =============================================================
-- transform_canonical.sql
-- dbt-style SQL transformation: 3 brand raw schemas → canonical
--
-- This file can be run directly in the BigQuery console or
-- adapted into a dbt model (place in models/ directory and
-- remove the CREATE TABLE ... AS prefix).
--
-- Pipeline flow:
--   raw_brand_a.orders  ─┐
--   raw_brand_b.orders  ─┼── UNION ALL (with normalization) ──► canonical.order
--   raw_brand_c.orders  ─┘
--                                 ↓
--                       canonical.customer  (MERGE / dedup)
--                                 ↓
--                       mart.customer_360   (aggregated mart table)
--
-- Identity Resolution Strategy:
--   customer_key = TO_HEX(SHA256(CONCAT(brand_id, '|', source_customer_id)))
--   This is a DETERMINISTIC hash — same source identity always maps to
--   the same customer_key. No lookup table required. No UUID collisions.
-- =============================================================


-- ─────────────────────────────────────────────────────────────
-- STEP 1: Normalize each brand into a unified staging CTE
--
-- Produces columns: order_key, customer_key, brand_id, store_key,
--                   channel, event_date, event_ts, amount_usd, source_order_id
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE `{PROJECT_ID}.canonical.order` AS

WITH

-- Brand A normalization
-- - cust_id (INT64) → CAST to STRING before hashing
-- - discount_pct stored as fraction (0.10 = 10%), subtract from amount
-- - channel already 'PHYSICAL'/'DIGITAL' — matches canonical enum
brand_a AS (
  SELECT
    TO_HEX(SHA256(CONCAT('brand_a', '|', CAST(cust_id AS STRING)))) AS customer_key,
    TO_HEX(SHA256(CONCAT('brand_a', '|', order_id)))                AS order_key,
    'brand_a'                                                        AS brand_id,
    store_id                                                         AS store_key,
    channel,                                                         -- 'PHYSICAL' | 'DIGITAL'
    DATE(transaction_ts)                                             AS event_date,
    transaction_ts                                                   AS event_ts,
    ROUND(amount_usd * (1 - COALESCE(discount_pct, 0.0)), 2)        AS amount_usd,  -- post-discount net
    order_id                                                         AS source_order_id
  FROM `{PROJECT_ID}.raw_brand_a.orders`
),

-- Brand B normalization
-- - customer_uuid (STRING UUID) → use directly as source_customer_id
-- - txn_date is DATE only → event_ts will be NULL
-- - gross_amount vs net_amount: we use net_amount (post-tax) normalized to USD
-- - Brand B is brick-and-mortar only → channel = 'PHYSICAL'
-- - currency_code handled: multiply by 1.0 for USD, 0.74 for CAD (illustrative FX rate)
brand_b AS (
  SELECT
    TO_HEX(SHA256(CONCAT('brand_b', '|', customer_uuid)))           AS customer_key,
    TO_HEX(SHA256(CONCAT('brand_b', '|', ord_number)))              AS order_key,
    'brand_b'                                                        AS brand_id,
    location_code                                                    AS store_key,
    'PHYSICAL'                                                       AS channel,  -- B is brick-and-mortar only
    txn_date                                                         AS event_date,
    NULL                                                             AS event_ts, -- date-only source
    ROUND(
      net_amount * CASE currency_code
        WHEN 'USD' THEN 1.0
        WHEN 'CAD' THEN 0.74  -- approximate FX; production: join fx_rates table
        ELSE 1.0
      END, 2
    )                                                                AS amount_usd,
    ord_number                                                       AS source_order_id
  FROM `{PROJECT_ID}.raw_brand_b.orders`
),

-- Brand C normalization
-- - loyalty_number is NULL for ~30% of guest checkouts
--   → customer_key is NULL for guests; they can't be cross-brand matched in Phase 1
-- - subtotal_price EXCLUDES shipping/tax → use as-is (comparable to Brand A post-discount)
-- - All Brand C transactions are DIGITAL (Shopify/ecommerce)
-- - Multi-currency: USD, GBP, AUD. Use approximate FX rates (production: join fx_rates)
brand_c AS (
  SELECT
    CASE
      WHEN loyalty_number IS NOT NULL
        THEN TO_HEX(SHA256(CONCAT('brand_c', '|', loyalty_number)))
      ELSE NULL  -- Guest checkout: no deterministic identity in Phase 1
    END                                                              AS customer_key,
    TO_HEX(SHA256(CONCAT('brand_c', '|', transaction_id)))          AS order_key,
    'brand_c'                                                        AS brand_id,
    shop_id                                                          AS store_key,
    'DIGITAL'                                                        AS channel,  -- C is Shopify-only
    DATE(created_at)                                                 AS event_date,
    created_at                                                       AS event_ts,
    ROUND(
      subtotal_price * CASE currency
        WHEN 'USD' THEN 1.0
        WHEN 'GBP' THEN 1.27  -- approximate FX
        WHEN 'AUD' THEN 0.65  -- approximate FX
        ELSE 1.0
      END, 2
    )                                                                AS amount_usd,
    transaction_id                                                   AS source_order_id
  FROM `{PROJECT_ID}.raw_brand_c.orders`
),

-- ─────────────────────────────────────────────────────────────
-- STEP 2: Union all brands into a single canonical stream
-- ─────────────────────────────────────────────────────────────
unified AS (
  SELECT * FROM brand_a
  UNION ALL
  SELECT * FROM brand_b
  UNION ALL
  SELECT * FROM brand_c
)

-- Final SELECT — add pipeline metadata
SELECT
  order_key,
  customer_key,
  brand_id,
  store_key,
  channel,
  event_date,
  event_ts,
  amount_usd,
  source_order_id,
  CURRENT_TIMESTAMP() AS _ingestion_ts,
  'v1.0'              AS _pipeline_version
FROM unified
;


-- ─────────────────────────────────────────────────────────────
-- STEP 3: Canonical Customer Deduplication
--
-- canonical.customer should have ONE row per (brand_id, source_customer_id).
-- We derive it from canonical.order using MIN(event_date) as created_date.
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE `{PROJECT_ID}.canonical.customer` AS
SELECT
  customer_key,
  brand_id,
  -- Recover source_customer_id from canonical.order via the raw tables (join back)
  -- For simplicity here we derive it from the hash components:
  MIN(source_order_id)  AS sample_source_order,     -- illustrative — real pipeline joins raw tables
  'deterministic'       AS identity_method,
  MIN(event_date)       AS created_date,
  CURRENT_TIMESTAMP()   AS updated_ts,
  NULL                  AS email_hash,               -- Phase 2: populated by CRM API
  NULL                  AS country_code,
  NULL                  AS postal_code
FROM `{PROJECT_ID}.canonical.order`
WHERE customer_key IS NOT NULL  -- Exclude Brand C guest checkouts
GROUP BY customer_key, brand_id
;


-- ─────────────────────────────────────────────────────────────
-- STEP 4: customer_360 mart table
--
-- The key business output: per-customer cross-brand purchase summary.
-- This powers the Looker Studio dashboard.
--
-- cross_brand_flag = TRUE means the same customer has purchases in
-- more than one brand. This is the "golden record" for CIO reporting.
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE `{PROJECT_ID}.mart.customer_360` AS

WITH

per_brand_summary AS (
  SELECT
    customer_key,
    brand_id,
    COUNT(DISTINCT order_key)   AS total_orders,
    SUM(amount_usd)             AS total_spend_usd,
    MIN(event_date)             AS first_order_date,
    MAX(event_date)             AS last_order_date
  FROM `{PROJECT_ID}.canonical.order`
  WHERE customer_key IS NOT NULL
  GROUP BY customer_key, brand_id
),

brand_count_per_customer AS (
  SELECT
    customer_key,
    COUNT(DISTINCT brand_id) AS brands_count  -- >1 means cross-brand customer
  FROM per_brand_summary
  GROUP BY customer_key
)

SELECT
  pbs.customer_key,
  pbs.brand_id,
  pbs.total_orders,
  ROUND(pbs.total_spend_usd, 2)              AS total_spend_usd,
  pbs.first_order_date,
  pbs.last_order_date,
  (bcc.brands_count > 1)                     AS cross_brand_flag,  -- ← THE KEY METRIC
  bcc.brands_count                           AS total_brands_shopped,
  CURRENT_TIMESTAMP()                        AS _mart_refreshed_ts
FROM per_brand_summary pbs
JOIN brand_count_per_customer bcc USING (customer_key)
ORDER BY total_spend_usd DESC
;


-- ─────────────────────────────────────────────────────────────
-- VALIDATION QUERIES (run after transform to verify results)
-- ─────────────────────────────────────────────────────────────

-- Check row counts per brand
SELECT brand_id, COUNT(*) AS orders
FROM `{PROJECT_ID}.canonical.order`
GROUP BY brand_id;

-- Check cross-brand customer count
SELECT
  cross_brand_flag,
  COUNT(DISTINCT customer_key) AS customers,
  ROUND(SUM(total_spend_usd), 2) AS total_spend_usd
FROM `{PROJECT_ID}.mart.customer_360`
GROUP BY cross_brand_flag;

-- Sample cross-brand customers (the "golden record" moment for the demo)
SELECT *
FROM `{PROJECT_ID}.mart.customer_360`
WHERE cross_brand_flag = TRUE
LIMIT 10;
