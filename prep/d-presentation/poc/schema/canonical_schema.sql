-- =============================================================
-- Canonical Schema — Unified Data Model
-- Dataset: canonical (BigQuery)
--
-- Design Principles:
--   1. Brand-agnostic: every table carries brand_id so a single
--      query can span all three brands without UNIONs
--   2. Synthetic keys: customer_key = SHA-256(brand_id | source_id)
--      — deterministic, no lookup table required, privacy-safe
--   3. Partitioned by event/created date for cost-efficient scans
--   4. Clustered by brand_id + customer_key for typical join patterns
--   5. Append-only raw layer; updates handled via MERGE in mart layer
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- TABLE: canonical.customer
--
-- One row per source customer per brand.
-- customer_key is the cross-brand join handle for mart queries.
-- identity_method records HOW we resolved identity (deterministic
-- vs. probabilistic — Phase 2 will add ML-based email matching).
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.canonical.customer` (
  -- Synthetic primary key: SHA-256(brand_id || '|' || source_customer_id)
  -- Example: SHA-256("brand_a|101") → hex string
  -- DETERMINISTIC — same input always produces same key.
  -- Can join this key across canonical.order without a lookup table.
  customer_key        STRING    NOT NULL,

  brand_id            STRING    NOT NULL,   -- 'brand_a' | 'brand_b' | 'brand_c'
  source_customer_id  STRING    NOT NULL,   -- Raw ID from source (cast to STRING for uniformity)
                                            -- Brand A: CAST(cust_id AS STRING)
                                            -- Brand B: customer_uuid
                                            -- Brand C: loyalty_number

  identity_method     STRING,               -- 'deterministic' (Phase 1) | 'email_match' (Phase 2)
                                            -- | 'probabilistic' (Phase 2 ML)

  created_date        DATE      NOT NULL,   -- First order date (used for partition)
  updated_ts          TIMESTAMP,            -- Last time this record was refreshed

  -- Optional enrichment fields (populated via Brand CRM APIs in Phase 2)
  email_hash          STRING,               -- SHA-256(normalized_email) — for probabilistic matching
  country_code        STRING,               -- ISO 3166-1 alpha-2
  postal_code         STRING
)
-- Partition by first order date — most cross-brand queries filter by cohort date
PARTITION BY created_date
-- Cluster by brand_id first (frequent WHERE brand_id = 'brand_a'), then customer_key
-- for JOIN patterns (canonical.order JOIN canonical.customer ON customer_key)
CLUSTER BY brand_id, customer_key
OPTIONS (
  description = "Canonical customer entity. One row per source customer per brand. customer_key is deterministic SHA-256 hash — use for cross-brand JOINs."
);


-- ─────────────────────────────────────────────────────────────
-- TABLE: canonical.order
--
-- Unified order table — all 3 brands in one partition.
-- All monetary values normalized to USD at time of transaction.
-- event_date is the canonical transaction date (normalizes
-- Brand B's DATE-only column and Brand C's Shopify timestamp).
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.canonical.order` (
  order_key           STRING    NOT NULL,   -- SHA-256(brand_id || '|' || source_order_id)
  customer_key        STRING    NOT NULL,   -- FK → canonical.customer.customer_key
                                            -- NULL if Brand C guest checkout (loyalty_number IS NULL)
  brand_id            STRING    NOT NULL,   -- 'brand_a' | 'brand_b' | 'brand_c'
  store_key           STRING,               -- Normalized store identifier (NULL for online)
  channel             STRING,               -- 'PHYSICAL' | 'DIGITAL' | 'UNKNOWN'
                                            -- Brand B has no channel → 'PHYSICAL' (brick-and-mortar)
                                            -- Brand C has no channel → 'DIGITAL' (Shopify)

  event_date          DATE      NOT NULL,   -- Canonical transaction date (used for partition)
                                            -- Brand A: DATE(transaction_ts)
                                            -- Brand B: txn_date (already DATE)
                                            -- Brand C: DATE(created_at)

  event_ts            TIMESTAMP,            -- Full timestamp where available (NULL for Brand B)

  amount_usd          NUMERIC   NOT NULL,   -- Normalized transaction value in USD
                                            -- Brand A: amount_usd * (1 - discount_pct)    [post-discount]
                                            -- Brand B: net_amount * fx_rate_to_usd        [post-tax, FX-adjusted]
                                            -- Brand C: subtotal_price * fx_rate_to_usd   [FX-adjusted]

  source_order_id     STRING    NOT NULL,   -- Original order ID from source system

  _ingestion_ts       TIMESTAMP,            -- When this record entered canonical layer
  _pipeline_version   STRING                -- Pipeline version tag for lineage
)
PARTITION BY event_date
-- Cluster by brand_id + customer_key for:
--   (a) single-brand queries: WHERE brand_id = 'brand_a'
--   (b) cross-brand join: JOIN canonical.customer USING (customer_key)
CLUSTER BY brand_id, customer_key
OPTIONS (
  description = "Canonical order fact table. All 3 brands unified. Amounts normalized to USD. Partitioned by event_date, clustered by brand_id, customer_key."
);


-- ─────────────────────────────────────────────────────────────
-- TABLE: canonical.product
--
-- Product master — cross-brand. SKU alignment is Phase 1 scope
-- (name/category inference from source data). True cross-brand
-- product matching is a Phase 2 effort using ML classification.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.canonical.product` (
  product_key         STRING    NOT NULL,   -- SHA-256(brand_id || '|' || source_sku)
  brand_id            STRING    NOT NULL,   -- 'brand_a' | 'brand_b' | 'brand_c'
  source_sku          STRING    NOT NULL,   -- Raw SKU from source system
  name                STRING,               -- Product name (from source catalog or API)
  category            STRING,               -- Top-level category (normalized)
  subcategory         STRING,               -- Sub-category

  -- Phase 2: cross-brand product matching
  cross_brand_product_key STRING,           -- NULL in Phase 1 — populated by ML classifier in Phase 2

  created_date        DATE
)
PARTITION BY created_date
CLUSTER BY brand_id, category
OPTIONS (
  description = "Canonical product dimension. Phase 1: per-brand records only. Phase 2: cross_brand_product_key populated by ML-based product matching."
);


-- =============================================================
-- CUSTOMER KEY GENERATION EXAMPLE
-- (Use this logic in transform_canonical.sql and Dataflow pipeline)
-- =============================================================
/*
-- Brand A: source_customer_id = CAST(cust_id AS STRING)
SELECT
  TO_HEX(SHA256(CONCAT('brand_a', '|', CAST(cust_id AS STRING)))) AS customer_key,
  'brand_a'                                                        AS brand_id,
  CAST(cust_id AS STRING)                                          AS source_customer_id
FROM `{PROJECT_ID}.raw_brand_a.orders`

-- Brand B
SELECT
  TO_HEX(SHA256(CONCAT('brand_b', '|', customer_uuid))) AS customer_key,
  'brand_b'                                              AS brand_id,
  customer_uuid                                          AS source_customer_id
FROM `{PROJECT_ID}.raw_brand_b.orders`

-- Brand C (filter out guest checkouts for deterministic identity)
SELECT
  TO_HEX(SHA256(CONCAT('brand_c', '|', loyalty_number))) AS customer_key,
  'brand_c'                                               AS brand_id,
  loyalty_number                                          AS source_customer_id
FROM `{PROJECT_ID}.raw_brand_c.orders`
WHERE loyalty_number IS NOT NULL  -- Guest checkouts handled separately in Phase 2
*/
