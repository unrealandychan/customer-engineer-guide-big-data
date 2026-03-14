# Study Plan — Missed Questions Recovery
**Based on Round A feedback · Target: Interview B/C/D**
**Start Date: March 12, 2026**

---

## Overview

| # | Topic | Weakness | Priority | Est. Hours |
|---|---|---|---|---|
| Q1 | DB burst handling + System Design (Black Friday) | System design depth | 🔴 HIGH | 4h |
| Q2 | PII discovery without patterns (GCP: DLP) | GCP-specific tooling | 🔴 HIGH | 2h |
| Q3 | Schema evolution — API sink resilience | Data engineering depth | 🟡 MED | 2h |
| Q4 | Data quality monitoring — cloud + on-site | Observability breadth | 🟡 MED | 3h |

**Total estimated study time: ~11 hours**

---

## Q1: Black Friday DB Burst — System Design

### The Question
> An eCommerce company faces Black Friday/Double Eleven traffic spikes. How do you handle the burst at the database and query level from a system design perspective?

### Why You Missed It
System design requires layered thinking: you need to cover *each layer* of the stack (client → API → cache → DB → analytics) and *trade-offs* at each layer. Single-layer answers lose points.

### The Full Framework (Layer by Layer)

```
Client / CDN
    ↓
API Gateway + Rate Limiting
    ↓
Application Tier (auto-scaled)
    ↓
Cache Layer (Redis / Memorystore)
    ↓
Message Queue (Pub/Sub / SQS)   ← absorbs write bursts
    ↓
Primary DB (read replicas, connection pooling)
    ↓
Analytics / DWH (BigQuery — separate from OLTP)
```

### Layer-by-Layer Strategies

#### 1. Client / CDN Layer
- **Static asset caching** via Cloud CDN / CloudFront — offloads product catalog pages
- **Browser-side rate limiting**: queue token bucket per user session
- **Virtual waiting room** (e.g., Queue-it) — regulated admission into checkout

#### 2. API Gateway
- **Rate limiting per client/IP**: Cloud Apigee or AWS API Gateway throttling policies
- **Circuit breaker pattern**: if downstream DB latency > threshold, return 503 early (fail fast) rather than piling up requests
- **Token bucket algorithm**: each user gets N requests/second; excess is queued or rejected

#### 3. Application Tier
- **Horizontal auto-scaling**: Cloud Run / GKE HPA scales app pods on CPU/latency metrics
- **Stateless services**: session state externalised to Redis so any pod can serve any request
- **Connection pool limits**: each app pod gets a fixed pool (e.g. 10 DB connections via PgBouncer) — prevents DB connection storm

#### 4. Cache Layer (CRITICAL for read-heavy spikes)
- **Read-through cache**: product catalog, prices, inventory counts served from Redis/Memorystore
- **Cache-aside pattern**: app checks cache first → on miss, hits DB → writes to cache
- **Cache stampede prevention**: use a lock or probabilistic early expiry to prevent N threads all missing cache simultaneously and hammering DB
- **TTL strategy**: inventory = 30s TTL (must be fresh), product description = 1h TTL
```
# GCP: Cloud Memorystore (Redis)
# AWS: ElastiCache
Pattern: CACHE_ASIDE
  1. Read(key) → cache HIT → return value
  2. Read(key) → cache MISS → read from DB → write(key, value, TTL) → return value
```

#### 5. Message Queue (Write Burst Decoupling — KEY INSIGHT)
- **Order writes go to Pub/Sub / SQS first**, not directly to DB
- Queue absorbs the burst spike; workers drain the queue at DB-sustainable rate
- **Benefit**: user sees "Order Placed ✓" immediately (queue ACK), actual DB write happens asynchronously
- **Dead-letter topic**: failed writes after N retries → DLQ for manual review
```
User → POST /order → API → Pub/Sub topic → ACK to user (instant)
                                ↓
                         Worker pool (scaled separately)
                                ↓
                           DB write (controlled rate)
```

#### 6. Database Layer
**Read Replicas**
- Route all SELECT queries to read replicas; only ORDER INSERT / UPDATE to primary
- GCP: Cloud SQL read replicas or AlloyDB read pool
- Rule: never run analytics queries on the OLTP primary during Black Friday

**Connection Pooling**
- PgBouncer (Postgres) or ProxySQL (MySQL) between app and DB
- Limits: 20 server connections per DB; pool of 200 app connections → reduces overhead by 10×

**Query Optimization for Spikes**
- Ensure all Black Friday queries hit indexes: `product_id`, `order_status`, `user_id`
- Avoid `SELECT *` — specify columns to reduce I/O
- Avoid table scans: pre-warm read replicas with `EXPLAIN ANALYZE` before the event
- Use **materialized views** for pre-aggregated inventory counts (refresh every 30s via CRON)

**OLTP vs OLAP Separation**
- Analytics dashboards MUST NOT query the OLTP DB during the event
- Route analytics to BigQuery (CDC via Datastream) or a read replica with query timeout limits

**Chaos Engineering Pre-Event**
- Run load tests at 2× expected peak traffic 1 week before (k6, Locust, JMeter)
- Validate autoscaling policies trigger correctly under load
- Test circuit breakers: simulate DB slowdown → verify API returns 503 within 2s

#### 7. BigQuery / Analytics Layer
- BigQuery is serverless — it auto-scales for query slots; no config needed
- Use **slot reservations** (Flex Slots) purchased ahead of Black Friday for guaranteed capacity
- **BI Engine**: in-memory cache for Looker Studio dashboards — dashboard doesn't hit BQ slots
- **Materialized views** in BQ: pre-aggregate hourly sales so dashboard reads don't scan full fact table

### GCP-Specific Services Summary

| Problem | GCP Service | AWS Equivalent |
|---|---|---|
| API rate limiting | Apigee / Cloud Endpoints | API Gateway |
| Queue burst absorption | Pub/Sub | SQS / Kinesis |
| Read caching | Memorystore (Redis) | ElastiCache |
| DB connection pooling | PgBouncer + Cloud SQL | RDS Proxy |
| OLTP auto-scaling | AlloyDB / Cloud SQL | Aurora |
| Analytics isolation | BigQuery + Datastream | Redshift |
| Load testing | Cloud Load Testing (k6) | AWS Load Testing |
| Auto-scaling app tier | Cloud Run / GKE HPA | ECS Fargate / EKS |

### Answer Skeleton (for follow-up in interviews)
```
1. Separate OLTP from OLAP — analytics never touches the order DB on event day
2. Write path: API → Pub/Sub (queue) → async DB worker (decoupled burst)
3. Read path: CDN → Cache → Read Replica (primary never hit for reads)
4. DB: connection pool + read replicas + index pre-warming
5. Pre-event: load test at 2× peak, buy BigQuery Flex Slots, set autoscaling
6. Monitoring: alert on p99 latency > 200ms, DB connection pool saturation > 80%
```

### Practice Questions
- "How would you handle inventory count accuracy when 10,000 users buy the last item simultaneously?" → (Pessimistic locking vs. optimistic locking + idempotency)
- "At what point would you migrate from Cloud SQL to Spanner?" → (Global consistency, millions of TPS, multi-region)
- "How do you prevent cache stampede on a popular product page?" → (Mutex lock + jitter TTL)

---

## Q2: PII Discovery Without Patterns (GCP DLP)

### The Question
> How do you identify PII in a database if there is no pattern? What is the GCP-native way to fix that?

### Why You Missed It
Most engineers know regex-based PII detection (emails, SSNs). The hard part is *unstructured / unknown PII* — and GCP Cloud DLP's ML-based infoType detection is the specific answer expected here.

### Taxonomy of PII Discovery Approaches

| Approach | How it Works | Limitation |
|---|---|---|
| **Regex / Pattern matching** | `\d{3}-\d{2}-\d{4}` for SSN | Only works for structured, known formats |
| **Dictionary matching** | Match against lists of known names, cities | High false positives |
| **ML-based InfoType detection** | Contextual ML model understands *meaning* | The GCP DLP approach — works on unstructured text |
| **Column name heuristics** | Flag columns named `email`, `phone`, `name` | Misses obfuscated column names |

### GCP Cloud DLP — The Right Answer

**What it is:** Cloud Data Loss Prevention (DLP) API — inspects text, structured data, images for 150+ built-in PII infoTypes using ML.

**Key differentiator:** DLP uses *contextual ML models*, not just regex. It understands that "John Smith can be reached at his home" implies a person's name even without a pattern.

#### Step 1: Scan BigQuery tables with DLP

```python
from google.cloud import dlp_v2

dlp = dlp_v2.DlpServiceClient()
project = "your-project-id"

# Define what to inspect
inspect_config = dlp_v2.InspectConfig(
    # Built-in InfoTypes — no pattern needed
    info_types=[
        {"name": "PERSON_NAME"},
        {"name": "EMAIL_ADDRESS"},
        {"name": "PHONE_NUMBER"},
        {"name": "CREDIT_CARD_NUMBER"},
        {"name": "DATE_OF_BIRTH"},
        {"name": "IP_ADDRESS"},
        {"name": "PASSPORT"},
        {"name": "STREET_ADDRESS"},
        # For unstructured free-text (comments, notes fields):
        {"name": "MEDICAL_RECORD_NUMBER"},
        {"name": "US_SOCIAL_SECURITY_NUMBER"},
    ],
    min_likelihood=dlp_v2.Likelihood.POSSIBLE,   # ← Lower threshold catches more
    include_quote=True,   # Show the actual matched text in results
)

# Target: BigQuery table
storage_config = dlp_v2.StorageConfig(
    big_query_options=dlp_v2.BigQueryOptions(
        table_reference=dlp_v2.BigQueryTable(
            project_id=project,
            dataset_id="raw_brand_a",
            table_id="orders",
        ),
        rows_limit=10000,   # Sample first; full scan for production
    )
)

# Run DLP inspection job (async)
job = dlp.create_dlp_job(
    parent=f"projects/{project}",
    inspect_job=dlp_v2.InspectJobConfig(
        storage_config=storage_config,
        inspect_config=inspect_config,
        actions=[
            dlp_v2.Action(
                save_findings=dlp_v2.Action.SaveFindings(
                    output_config=dlp_v2.OutputStorageConfig(
                        table=dlp_v2.BigQueryTable(
                            project_id=project,
                            dataset_id="security",
                            table_id="dlp_findings",  # findings land here
                        )
                    )
                )
            )
        ],
    ),
)
print(f"DLP job created: {job.name}")
```

#### Step 2: Handle "No Pattern" — Custom InfoTypes + Contextual Rules

When PII has no known pattern (e.g., internal employee ID that happens to be sensitive):

```python
# Custom InfoType: internal employee IDs that look like "EMP-XXXXX"
custom_info_type = dlp_v2.CustomInfoType(
    info_type={"name": "EMPLOYEE_ID"},
    regex=dlp_v2.CustomInfoType.Regex(pattern=r"EMP-\d{5}"),
    likelihood=dlp_v2.Likelihood.LIKELY,
)

# Context rule: if "employee" or "staff" appears near the value, increase likelihood
detection_rule = dlp_v2.CustomInfoType.DetectionRule(
    hotword_rule=dlp_v2.CustomInfoType.DetectionRule.HotwordRule(
        hotword_regex=dlp_v2.CustomInfoType.Regex(pattern=r"employee|staff|worker"),
        proximity=dlp_v2.CustomInfoType.DetectionRule.Proximity(
            window_before=10, window_after=10
        ),
        likelihood_adjustment=dlp_v2.CustomInfoType.DetectionRule.LikelihoodAdjustment(
            fixed_likelihood=dlp_v2.Likelihood.VERY_LIKELY
        ),
    )
)
```

#### Step 3: Remediation after Discovery

Once DLP identifies PII columns, apply transformations:

| Technique | When to Use | BigQuery DLP Method |
|---|---|---|
| **Tokenization** | Re-identification needed (join key) | `CryptoReplaceFfxFpeConfig` |
| **Pseudonymization** | Internal analytics, consistent token | `CryptoDeterministicConfig` |
| **Masking** | Display/reporting only | `CharacterMaskConfig` |
| **Bucketing** | Age ranges, salary bands | `BucketingConfig` |
| **Redaction** | Logs, free text — full removal | `ReplaceWithInfoTypeConfig` |

#### Step 4: Continuous PII Detection Pipeline

```
New data lands in GCS/BQ
        ↓
Cloud Function / Eventarc trigger
        ↓
DLP Inspection Job (async)
        ↓
Findings → security.dlp_findings BQ table
        ↓
Cloud Monitoring alert if HIGH LIKELIHOOD PII found in unexpected column
        ↓
Data Steward notified → column tagged in Dataplex (policy tag)
        ↓
BigQuery Column-Level Security: policy tag → IAM binding → access restricted
```

#### GCP Data Catalog + Policy Tags

After DLP finds PII:
```sql
-- Tag the column in BigQuery with a policy tag
-- This automatically enforces column-level IAM
-- Users without "Fine-Grained Reader" permission see NULL instead of the value

-- In BigQuery UI: Schema → column → Edit → Policy Tag → "PII/Sensitive"
-- IAM: roles/bigquery.fineGrainedReader → granted only to data stewards
```

### Non-GCP Approaches (for completeness)
- **AWS Macie**: S3-focused, ML-based PII discovery (equivalent to DLP for S3/RDS)
- **On-prem**: Immuta, Privacera, or Apache Atlas for column-level tagging
- **Open source**: Presidio (Microsoft) — NLP-based PII detection, runs anywhere

### Practice Questions
- "How would you detect PII in a free-text `order_notes` column?" → (DLP text inspection with PERSON_NAME + PHONE_NUMBER infoTypes, contextual rules)
- "What's the difference between tokenization and pseudonymization?" → (Tokenization: format-preserving, reversible with key. Pseudonymization: consistent hash, not easily reversible)
- "How do you prevent DLP scan costs from exploding on a 10TB table?" → (Row sampling, partition pruning, incremental scan on new partitions only)

---

## Q3: Schema Evolution — API Sink Resilience

### The Question
> An eCommerce API sinks data into your dashboard, but their schema can change any time. How do you ensure your side doesn't crash?

### Why You Missed It
Schema evolution is a classic data engineering problem. The answer requires knowing *where* to absorb schema changes — and the principle is: **absorb change as close to the source as possible, validate before it reaches downstream consumers**.

### Schema Change Taxonomy

| Change Type | Safe? | Example |
|---|---|---|
| Add optional field | ✅ Backward compatible | New field `discount_code` added |
| Remove field | ❌ Breaking | `product_name` removed — your query breaks |
| Rename field | ❌ Breaking | `price` → `unit_price` |
| Change data type | ❌ Breaking | `quantity` INT → STRING |
| Reorder fields | ✅ Safe (if using named fields) | Column order changed in CSV |

### Defense Architecture (4 Layers)

#### Layer 1: Landing Zone — Accept Raw, Validate Later
Never write raw API data directly into a typed (structured) table. Always land raw first.

```
API → GCS (raw JSON/Avro) → validate → BigQuery typed table → dashboard
         ↑
    "Schema shock absorber"
    Raw bytes always land here regardless of source schema
```

**GCS as landing zone:**
- API webhook/batch dumps raw JSON to `gs://bucket/raw/orders/YYYY-MM-DD/`
- Your pipeline reads raw, validates, then writes to canonical BigQuery table
- If schema breaks: raw is safe, only the transform step fails — raw data is never lost

#### Layer 2: Schema Registry (Confluent Schema Registry / Apicurio)
For streaming sources (Kafka, Pub/Sub):
```
Producer (API) → Schema Registry → registers Avro schema → Pub/Sub
Consumer (you) → Schema Registry → fetch schema by ID → deserialize safely

# Schema Registry enforces compatibility rules:
BACKWARD  → new schema can read old data (safe for consumers)
FORWARD   → old schema can read new data (safe for producers)
FULL      → both directions (strictest, recommended)
```

For Pub/Sub + Dataflow (GCP-native):
- Pub/Sub supports schema enforcement with Avro/Protocol Buffer schemas
- Define schema in Pub/Sub → any message violating schema is rejected at ingestion

```bash
# Create Pub/Sub topic with schema enforcement
gcloud pubsub schemas create orders-schema --type=avro \
  --definition-file=schemas/orders_v1.avsc

gcloud pubsub topics create orders-topic \
  --schema=orders-schema \
  --message-encoding=json
```

#### Layer 3: Schema Validation + Dead Letter Queue

In your Dataflow / Cloud Function pipeline:
```python
import jsonschema

EXPECTED_SCHEMA = {
    "type": "object",
    "required": ["order_id", "amount", "customer_id"],
    "properties": {
        "order_id":    {"type": "string"},
        "amount":      {"type": "number"},
        "customer_id": {"type": "string"},
    },
    "additionalProperties": True  # ← Key: allow extra fields (backward compat)
                                  # Never set to False — breaks on new fields
}

def validate_and_route(record: dict):
    try:
        jsonschema.validate(record, EXPECTED_SCHEMA)
        return "valid", record
    except jsonschema.ValidationError as e:
        return "dead_letter", {"raw": str(record), "error": str(e)}
```

**`additionalProperties: True`** is the key setting: new fields from the API are silently accepted and stored in raw, but don't break validation. Only *missing required fields* or *wrong types* fail validation.

#### Layer 4: BigQuery Schema Evolution Modes

```python
# BigQuery write disposition for schema evolution:

# Option A: SCHEMA_UPDATE_OPTION — automatically add new columns
job_config = bigquery.LoadJobConfig(
    schema_update_options=[
        bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,  # new columns OK
        bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION, # REQUIRED → NULLABLE OK
    ],
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
)

# Option B: Flexible column — store unknown fields as JSON STRING
# Add a `_raw_extras` JSON column to your BQ table:
# If API adds new fields, they land in _raw_extras until you promote them officially
```

#### Alerting on Schema Change (Proactive)
```python
# Before writing to BQ, compare incoming schema to expected
def detect_schema_drift(incoming_fields: set, expected_fields: set) -> None:
    new_fields     = incoming_fields - expected_fields
    missing_fields = expected_fields - incoming_fields
    
    if missing_fields:
        # CRITICAL: required fields are gone — alert immediately
        send_alert(f"BREAKING: fields removed from API: {missing_fields}")
    if new_fields:
        # INFO: new fields added — log and store in _raw_extras
        log_info(f"Schema additive change: new fields {new_fields}")
```

### Full Pattern Summary
```
API source schema changes
    ↓
[Layer 1] Raw land in GCS (JSON) — always safe, no schema enforcement
    ↓
[Layer 2] Pub/Sub schema registry — reject structurally invalid messages
    ↓
[Layer 3] Pipeline validates required fields → valid path / DLQ split
    ↓
[Layer 4] BigQuery ALLOW_FIELD_ADDITION + _raw_extras column
    ↓
Dashboard reads from canonical view (not raw table directly)
    ↓ ↑
Views are the contract — schema changes in raw don't break dashboards
```

**The critical insight:** Your **dashboard should always read from a VIEW or mart layer**, never directly from the raw ingestion table. Views are the schema contract. Raw tables can evolve freely.

### Practice Questions
- "Producer adds 50 new fields overnight. What happens to your pipeline?" → (All land safely due to additionalProperties + ALLOW_FIELD_ADDITION — log new fields, no crash)
- "Producer changes `price` from FLOAT to STRING. How do you catch it?" → (Schema validation catches type mismatch → DLQ → alert fires)
- "How does dbt handle schema evolution?" → (dbt models are SQL views/tables rebuilt each run; column additions are transparent, type changes fail compilation)

---

## Q4: Data Quality Monitoring — Cloud + On-Site

### The Question
> How do you maintain high data quality? Keep checking it with alarms and metrics. Give all implementations on cloud and on-site.

### Why You Missed It
Data quality requires a *systematic framework*, not a list of checks. The answer must cover: what dimensions to measure, how to alert, and where to implement (cloud + on-prem).

### The 6 Dimensions of Data Quality

| Dimension | Definition | Example Check |
|---|---|---|
| **Completeness** | No unexpected nulls | `COUNT(*) WHERE order_id IS NULL = 0` |
| **Uniqueness** | No duplicate primary keys | `COUNT(*) != COUNT(DISTINCT order_id)` → alert |
| **Validity** | Values within expected domain | `amount_usd > 0`, `channel IN ('PHYSICAL','DIGITAL')` |
| **Timeliness** | Data arrives within SLA | `MAX(event_ts) > NOW() - INTERVAL 1 HOUR` |
| **Consistency** | Same value across systems | Total orders in BQ = total orders in source API |
| **Accuracy** | Values reflect reality | Sum of line items = order total |

### Implementation: Cloud (GCP)

#### 1. BigQuery + Scheduled Queries (simplest, no extra tooling)

```sql
-- DQ Check: Run as a BigQuery scheduled query every hour
-- Write results to dq_results table; alert if any check fails

INSERT INTO `project.monitoring.dq_results`
SELECT
  CURRENT_TIMESTAMP()                       AS check_ts,
  'raw_brand_a.orders'                      AS table_name,
  'completeness_order_id'                   AS check_name,
  COUNTIF(order_id IS NULL)                 AS failed_rows,
  COUNT(*)                                  AS total_rows,
  ROUND(COUNTIF(order_id IS NULL) / COUNT(*) * 100, 4) AS failure_pct,
  IF(COUNTIF(order_id IS NULL) = 0, 'PASS', 'FAIL')    AS status
FROM `project.raw_brand_a.orders`
WHERE DATE(transaction_ts) = CURRENT_DATE()

UNION ALL

SELECT
  CURRENT_TIMESTAMP(),
  'raw_brand_a.orders',
  'uniqueness_order_id',
  COUNT(*) - COUNT(DISTINCT order_id),
  COUNT(*),
  ROUND((COUNT(*) - COUNT(DISTINCT order_id)) / COUNT(*) * 100, 4),
  IF(COUNT(*) = COUNT(DISTINCT order_id), 'PASS', 'FAIL')
FROM `project.raw_brand_a.orders`
WHERE DATE(transaction_ts) = CURRENT_DATE()

-- Add checks for: validity (amount > 0), timeliness (max ts recency), etc.
```

#### 2. Cloud Monitoring Alerts on DQ Results

```yaml
# alerting_policy.yaml — trigger if any DQ check FAILS
displayName: "Data Quality FAIL Alert"
conditions:
  - conditionThreshold:
      filter: |
        resource.type="bigquery_dataset"
        metric.type="logging.googleapis.com/user/dq_fail_count"
      comparison: COMPARISON_GT
      thresholdValue: 0
      duration: 0s   # alert immediately on first failure
notificationChannels:
  - projects/PROJECT_ID/notificationChannels/SLACK_CHANNEL_ID
  - projects/PROJECT_ID/notificationChannels/EMAIL_CHANNEL_ID
```

Trigger this by writing a custom metric from a Cloud Function that reads `dq_results`:
```python
from google.cloud import monitoring_v3

def publish_dq_metric(project_id, fail_count):
    client = monitoring_v3.MetricServiceClient()
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/dq/fail_count"
    point = series.points.add()
    point.value.int64_value = fail_count
    point.interval.end_time.GetCurrentTime()
    client.create_time_series(name=f"projects/{project_id}", time_series=[series])
```

#### 3. dbt Tests (Best Practice for SQL Transform Layer)

```yaml
# models/canonical/schema.yml
models:
  - name: customer_360
    columns:
      - name: customer_key
        tests:
          - not_null
          - unique
      - name: brand_id
        tests:
          - not_null
          - accepted_values:
              values: ['brand_a', 'brand_b', 'brand_c']
      - name: total_spend_usd
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      - name: first_order_date
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= last_order_date"
```

Run `dbt test` in CI/CD; block deployment if tests fail. Integrate with Cloud Build:
```yaml
# cloudbuild.yaml
steps:
  - name: 'python:3.11'
    entrypoint: 'bash'
    args: ['-c', 'pip install dbt-bigquery && dbt test --profiles-dir . --target prod']
```

#### 4. Dataplex Data Quality (GCP-native, no code)

Dataplex has a built-in Data Quality product (GA as of 2024):
```yaml
# dataplex_dq_spec.yaml
rules:
  - column: order_id
    rule_type: NOT_NULL
    dimension: COMPLETENESS

  - column: amount_usd
    rule_type: RANGE
    min_value: 0
    max_value: 100000
    dimension: VALIDITY

  - rule_type: ROW_CONDITION
    sql_expression: "amount_usd > 0 AND channel IN ('PHYSICAL', 'DIGITAL')"
    dimension: VALIDITY

  - rule_type: FRESHNESS
    column: transaction_ts
    staleness_threshold: "PT1H"   # alert if no data in last 1 hour
    dimension: TIMELINESS
```

Dataplex DQ writes results to BigQuery and integrates natively with Cloud Monitoring.

#### 5. Great Expectations (Open Source, Cloud-Compatible)

Great Expectations (GX) is the open-source standard — runs on GCP, AWS, Azure, on-prem:

```python
import great_expectations as gx

context = gx.get_context()

# Define expectations
validator = context.sources.add_or_update_spark("bigquery_source") \
    .add_or_update_asset("orders").get_batch()

validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_be_unique("order_id")
validator.expect_column_values_to_be_between("amount_usd", min_value=0, max_value=100000)
validator.expect_column_values_to_be_in_set("channel", ["PHYSICAL", "DIGITAL"])
validator.expect_column_pair_values_a_to_be_greater_than_b(
    column_A="last_order_date", column_B="first_order_date"
)

# Run validation
result = validator.validate()
# result.success → True/False
# result.statistics → n_checks, n_passed, n_failed
```

Integrate GX into Airflow DAG → if `result.success == False` → fail the DAG → PagerDuty alert.

### Implementation: On-Premises

#### 1. Apache Airflow DAG with Data Quality Operators

```python
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLCheckOperator, SQLValueCheckOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

with DAG("data_quality_checks", schedule_interval="@hourly", start_date=datetime(2026, 1, 1)) as dag:

    # Check: no null order_ids in last 24h
    check_no_nulls = SQLCheckOperator(
        task_id="check_order_id_not_null",
        conn_id="postgres_warehouse",
        sql="""
            SELECT COUNT(*) = 0
            FROM orders
            WHERE order_id IS NULL
              AND transaction_ts > NOW() - INTERVAL '24 hours'
        """,
    )

    # Check: uniqueness (returns count of duplicates = 0)
    check_uniqueness = SQLValueCheckOperator(
        task_id="check_order_id_unique",
        conn_id="postgres_warehouse",
        sql="SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE",
        pass_value=0,
    )

    # Check: freshness — last record within 1 hour
    check_freshness = SQLValueCheckOperator(
        task_id="check_data_freshness",
        conn_id="postgres_warehouse",
        sql="SELECT EXTRACT(EPOCH FROM (NOW() - MAX(transaction_ts))) / 3600",
        pass_value=1,         # must be < 1 hour old
        tolerance=0,
    )

    check_no_nulls >> check_uniqueness >> check_freshness
```

If any task fails → Airflow marks DAG as FAILED → Slack alert via `SlackWebhookOperator`.

#### 2. Prometheus + Grafana (On-Prem Observability Stack)

```python
# dq_exporter.py — runs as a sidecar service, exposes /metrics endpoint
from prometheus_client import Gauge, start_http_server
import psycopg2, time

DQ_NULL_COUNT = Gauge('dq_null_count', 'Null order_ids in last hour', ['table'])
DQ_DUPLICATE_COUNT = Gauge('dq_duplicate_count', 'Duplicate order_ids', ['table'])
DQ_FRESHNESS_SECONDS = Gauge('dq_freshness_seconds', 'Seconds since last record', ['table'])

def collect_metrics():
    conn = psycopg2.connect("postgresql://user:pass@localhost/db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM orders WHERE order_id IS NULL AND transaction_ts > NOW() - INTERVAL '1 hour'")
    DQ_NULL_COUNT.labels(table='orders').set(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE")
    DQ_DUPLICATE_COUNT.labels(table='orders').set(cur.fetchone()[0])

    cur.execute("SELECT EXTRACT(EPOCH FROM (NOW() - MAX(transaction_ts))) FROM orders")
    DQ_FRESHNESS_SECONDS.labels(table='orders').set(cur.fetchone()[0])
    conn.close()

if __name__ == "__main__":
    start_http_server(8080)
    while True:
        collect_metrics()
        time.sleep(60)
```

**Grafana alert rule:**
```yaml
# alert.yaml
- alert: DataQualityFreshnessViolation
  expr: dq_freshness_seconds{table="orders"} > 3600
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Orders table has no new data for over 1 hour"

- alert: DataQualityDuplicates
  expr: dq_duplicate_count{table="orders"} > 0
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Duplicate order_ids detected: {{ $value }} duplicates"
```

#### 3. Apache Atlas (On-Prem Data Catalog + Lineage)
- Tag columns with quality classifications: `PII`, `CRITICAL`, `DERIVED`
- Track lineage: if source table changes, downstream dependent tables are auto-identified
- Integrate with Ranger for fine-grained column access control (on-prem equivalent of BigQuery column-level security)

### Full DQ Implementation Reference

| Tool | Where | What It Covers |
|---|---|---|
| dbt tests | Cloud + On-prem | Transform layer DQ, integrated with CI/CD |
| Great Expectations | Cloud + On-prem | Batch DQ, profiles, HTML reports |
| Dataplex DQ | GCP only | No-code DQ, native BQ integration |
| Cloud Monitoring | GCP only | Custom metrics, alerting, dashboards |
| Airflow SQLCheckOperator | On-prem / any | Pipeline-integrated DQ gates |
| Prometheus + Grafana | On-prem | Real-time DQ metrics + alerting |
| Apache Atlas | On-prem | Data catalog, lineage, tagging |

### Practice Questions
- "Your pipeline runs hourly but data quality checks only run daily. How do you catch a completeness issue faster?" → (Row-count anomaly detection: if today's hourly row count deviates >20% from 4-week same-hour average → alert)
- "How do you set a DQ SLA?" → (Define thresholds: completeness ≥ 99.5%, uniqueness = 100%, freshness < 1h; tie SLA breach to on-call page)
- "What's the difference between data profiling and data validation?" → (Profiling: exploratory, discovers statistics and patterns. Validation: asserts specific expectations pass/fail)

---

## Study Schedule (11 hours over 1 week)

| Day | Topic | Hours | Activity |
|---|---|---|---|
| Day 1 (Thu Mar 12) | Q1: Black Friday System Design | 2h | Read framework above, draw the architecture diagram on paper |
| Day 2 (Fri Mar 13) | Q1 practice | 2h | Do 3 practice questions out loud, time yourself (8 min each) |
| Day 3 (Sat Mar 14) | Q2: PII / DLP | 2h | Read + run the DLP Python code locally in dry-run mode |
| Day 4 (Sun Mar 15) | Q3: Schema Evolution | 2h | Read + implement `validate_and_route` in a small Python script |
| Day 5 (Mon Mar 16) | Q4: Data Quality Cloud | 1.5h | Read Cloud section + write one dbt test yaml for `canonical.order` |
| Day 6 (Tue Mar 17) | Q4: Data Quality On-Site | 1h | Read on-prem section, sketch Prometheus + Airflow integration |
| Day 7 (Wed Mar 18) | Full review + mock answers | 0.5h | Answer all 4 questions out loud without notes — time each at 6 min |

**Daily review habit:** Each morning, re-read the "Answer Skeleton" or "Full Pattern Summary" box from the previous day's topic. 5 minutes. This cements retention.
