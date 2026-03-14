# Interview D — Presentation: 5-Layer Target Architecture

Full narrative for the technical deep-dive section. Use this to build Slide 5–8 content and to prepare for Gene's technical probes.

---

## The Problem Context (Specialist Blocker)

**Why this isn't solved by an off-the-shelf tool:**

Three retail brands have merged. Each has built their data infrastructure independently:
- **Brand A:** AWS-based, Redshift data warehouse, Kinesis for POS streaming, Salesforce CRM
- **Brand B:** On-premise Oracle DW, SAP ERP, no streaming layer, manual nightly exports
- **Brand C:** Snowflake on Azure, Shopify for eCommerce, some Databricks jobs

The CIO is chartered to deliver a 1-year AI activation + data monetization plan for the combined portfolio.

**The 4 reasons an off-the-shelf tool fails here:**

1. **Identity Resolution Problem**
   - Brand A: `cust_id` (internal integer key)
   - Brand B: `customer_uuid` (UUID from SAP)
   - Brand C: `loyalty_number` (retailer loyalty program ID)
   - No cross-brand customer identifier exists. A customer who shops at all 3 brands appears as 3 unrelated records. Portfolio-level analytics and personalization are impossible without solving this first.

2. **Schema Heterogeneity**
   - Product taxonomies are different per brand (Brand A uses style/color/size, Brand B uses SKU hierarchies only, Brand C has product variants)
   - Transaction data has different timestamp formats, currency fields, discount models
   - You cannot union 3 `orders` tables without a canonical schema layer

3. **Batch + Streaming Duality**
   - Physical stores generate real-time POS events (need streaming ingest: Pub/Sub)
   - eCommerce platforms generate batch order exports (need batch ingest: GCS landing)
   - Both must land in the same canonical warehouse — most tools handle one or the other, not both cleanly

4. **1-Year Mandate = Phased Approach Required**
   - A big-bang cutover of 3 legacy data stacks is a 2–3 year project
   - The board requires ROI within 12 months — so the architecture must deliver value incrementally, per phase, without requiring full migration completion before value is realized

---

## The 5-Layer Target Architecture

### Layer 1: Ingestion & Integration

**Purpose:** Bring all data from 3 brands, 2 modalities (batch + streaming), into a common landing zone.

**Streaming path (real-time POS + eCommerce events):**
- Source systems publish events to **Google Pub/Sub** topics (one topic per brand)
  - Brand A: port existing Kinesis producers to Pub/Sub via the connector, or replicate via Datastream
  - Brand B: add a lightweight event emitter to the POS system (REST → Pub/Sub)
  - Brand C: Shopify webhook → Cloud Functions → Pub/Sub
- Dataflow subscribes to all 3 topics and applies first-level schema normalization

**Batch path (nightly ERP/CRM/legacy DB loads):**
- Source systems export to brand-namespaced **GCS buckets** (`gs://portfolio-raw/brand-a/`, `brand-b/`, `brand-c/`)
- Supported ingest patterns:
  - S3 → GCS: Storage Transfer Service (automated, scheduled)
  - On-prem → GCS: gsutil or Storage Transfer Agent
  - Snowflake (Brand C): BigQuery Data Transfer Service
  - Oracle/SAP: Datastream (CDC) or scheduled export + GCS upload

**Key design decision:** One GCS bucket namespace with brand-level prefixes. Enables unified governance in Dataplex without separate access control systems per brand.

---

### Layer 2: Central Data Lake + Warehouse

**Purpose:** Single source of truth for all 3 brands, in both raw (lake) and curated (warehouse) forms.

**GCS Data Lake (Raw Zone):**
- Brand-namespaced raw zones: `gs://portfolio-raw/brand-{a,b,c}/{domain}/{date}/`
- Format: Parquet (columnar, efficient for BigQuery external tables)
- Retention: 13-month rolling window for raw events
- Data Classification tags applied at landing (via Dataplex auto-tagging)

**BigQuery Canonical Warehouse:**
- **`raw` dataset per brand** → tables mirror source structure exactly (no transformation yet)
- **`canonical` dataset** → brand-agnostic schema: `customer`, `order`, `order_item`, `product`, `store`, `channel`
- **`mart` dataset per use case** → `sales_performance`, `customer_360`, `inventory`, `cross_brand_journey`

**BigQuery Configuration Choices:**

| Table | Partition | Cluster | Rationale |
|---|---|---|---|
| `canonical.order` | `event_date` (DATE) | `brand_id, customer_key` | Most queries filter by date + brand. Clustering on both columns reduces scan cost. |
| `canonical.customer` | `created_date` | `brand_id` | Customer creation queries are time-bounded; brand isolation is common. |
| `mart.customer_360` | `snapshot_date` | `brand_id, segment` | Repeated segment analysis across brands is the primary access pattern. |
| `streaming.streaming_orders` | `event_date` (ingestion-time) | `brand_id` | Streaming data partitioned by ingestion-time for cost control; clustered for efficient brand queries. |

**Why BigQuery over Snowflake (for this scenario):**
- Serverless: no cluster to size during a migration where data volumes are uncertain
- Native streaming: Dataflow → BigQuery is a first-class managed pattern; no Snowflake equivalent
- BigQuery ML: train demand forecast directly where data lives — no data movement
- Multi-dataset IAM: isolate each brand's data access at the dataset level natively

---

### Layer 3: Processing & Feature Pipelines

**Purpose:** Transform raw data into canonical schema (dbt), build real-time feature pipelines (Dataflow), and prepare feature tables for ML (Vertex AI Feature Store).

**Batch Transformation (dbt on BigQuery):**
- `stg_brand_a_orders.sql`, `stg_brand_b_orders.sql`, `stg_brand_c_orders.sql` → staging models per brand
- `int_canonical_orders.sql` → union + normalize across all 3 brands, resolve customer_key
- `mart_customer_360.sql` → final customer 360 table: lifetime value, purchase frequency, cross-brand activity, recency
- dbt tests: not_null on `customer_key`, accepted_values on `brand_id`, row count reconciliation against source

**Streaming Transformation (Dataflow Apache Beam):**
- Pipeline: Pub/Sub subscription → validate → canonicalize → windowed aggregation → BigQuery streaming insert
- Window strategy: 5-minute fixed windows for near-real-time aggregations (sales-by-store-by-15-min)
- Late data: 2-minute watermark — events arriving late are accepted and reprocessed in the window; beyond watermark they fall into a dead-letter table for manual review
- Exactly-once semantics: Beam's shuffle-based guarantee (not Pub/Sub delivery guarantee — the distinction matters)
- Schema enforcement: Beam's `Schema.fromClass()` validates event structure before insert; malformed events → Pub/Sub dead-letter topic

**Feature Engineering (for ML):**
- Batch feature computation pipeline (nightly): recency, frequency, monetary (RFM) per customer per brand; cross-brand purchase rate; product affinity vectors
- These features land in **Vertex AI Feature Store** for low-latency serving to both online (recommendation API) and offline (model training) workloads

---

### Layer 4: Serving Layer

**Purpose:** Deliver data to two consumer types — business analysts (BI) and ML models (AI).

**BI — Looker Studio (POC) → Looker (Production):**
- POC: Looker Studio (free) connected directly to BigQuery `mart` dataset
  - Cross-brand sales dashboard: daily revenue by brand, store, channel, product category
  - Customer 360 summary: top segments by brand, cross-brand overlap, LTV distribution
- Production: Looker with LookML semantic layer
  - Centralized business logic (revenue definition is the same across all 3 brand reports)
  - Row-level security: a brand's regional manager sees only their brand's data

**ML/AI — Vertex AI:**
- **BigQuery ML** (for accessible AI): `ARIMA_PLUS` demand forecasting directly in BigQuery SQL — no data movement, accessible to SQL-proficient analysts, instantly deployable
- **Vertex AI Custom Training** (for advanced models): recommendation system using matrix factorization on the cross-brand purchase graph
- **Vertex AI Pipelines**: orchestrate the full ML cycle — feature → train → evaluate → deploy — with reproducibility and lineage tracking

---

### Layer 5: Governance & Security

**Purpose:** Ensure every brand's data is appropriately isolated, catalogued, quality-checked, and auditable — meeting both the new CIO's needs and any brand-specific compliance requirements.

**Dataplex (Unified Governance):**
- One Dataplex Lake spans all 3 brand zones and BigQuery datasets
- Zones: `raw-zone` (GCS landing), `curated-zone` (BigQuery canonical)
- Auto-discovery: Dataplex scans new GCS objects and BigQuery tables, registers them in Data Catalog automatically
- Data quality rules: row count checks, null rate checks, referential integrity (every `order.customer_key` must resolve in `customer` table) — run nightly as Dataplex DataScan jobs

**Data Catalog (Metadata):**
- Every table tagged with: brand_id, data_domain, sensitivity_class (PII / non-PII), data_owner, refresh_frequency
- PII columns tagged at column level: customer_name, email, loyalty_number → encrypted at rest + masked in non-prod environments

**IAM Design (Brand Isolation):**
- GCP folder hierarchy: `portfolio-org → brand-a-project, brand-b-project, brand-c-project, shared-platform-project`
- Brand engineers: read access to their own raw zone + canonical tables for their brand_id partition
- Portfolio analysts: read access to cross-brand mart datasets only
- Data platform team: write access to all zones, admin of transformation pipelines
- Audit logging: Cloud Audit Logs captures all BigQuery data access; alerts on cross-brand reads by non-authorized accounts

**PII / Compliance:**
- Encryption at rest: default Google-managed encryption key (CMEK available for regulated data)
- Dynamic data masking: non-prod environments use BigQuery column-level security to mask PII fields
- Right to erasure: customer deletion propagated via scheduled dbt job that nullifies PII columns by `customer_key` + triggers downstream mart refresh

---

## Key Technical Points to Defend Live

1. **"Why not just use a lakehouse (Databricks) instead of this multi-product stack?"**
   - Databricks Lakehouse is a strong option if the team is Spark-native. For this scenario, we optimize for: (1) no cluster management during a chaotic migration, (2) SQL-native BI and ML so business analysts can self-serve, (3) native GCP integration for streaming. BigQuery + Dataflow achieves this without Spark expertise.

2. **"How would you handle Brand B's on-premise Oracle with no streaming capability?"**
   - **Datastream** (Google's CDC product) connects directly to Oracle and streams changes to GCS or BigQuery. Alternatively, start with scheduled CSV exports to GCS → batch pipeline → establish Datastream in Phase 2 once connectivity is proven.

3. **"What's your strategy for schema evolution — what if Brand A adds a new field?"**
   - dbt schema version contracts: staging models declare expected columns. If Brand A adds a field, the staging model test flags it without breaking downstream. New fields are evaluated for promotion to canonical schema in the next sprint.

4. **"How do you handle data quality failures in the streaming pipeline?"**
   - Malformed events → Pub/Sub dead-letter topic (separate subscription, monitored separately)
   - Dataplex DataScan flags anomalies in BigQuery (null spikes, row count drops)
   - dbt tests catch referential integrity failures in the curated layer
   - Alerting: Cloud Monitoring dashboards + PagerDuty integration for P1 data freshness SLAs
