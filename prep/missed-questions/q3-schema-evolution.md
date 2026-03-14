# Q3 Study Material — Schema Evolution & API Sink Resilience
**Study Day: Day 4 · 2h total**

---

## The Question (verbatim)
> "If there is an eCommerce API sinking data into a dashboard, but the schema can change on their side, how do you ensure my side doesn't crash?"

## What the Interviewer Wants
- Understanding of *where* in the pipeline to absorb schema change
-具体 defensive patterns: raw landing zone, schema registry, validation + DLQ, BigQuery schema modes
- The insight that **dashboards should read from a view/mart layer** — never directly from raw ingestion tables
- Awareness of both batch and streaming schema evolution scenarios

---

## Schema Change Taxonomy — Know These

| Change Type | Safe for Consumers? | Example |
|---|---|---|
| **Add optional field** | ✅ Backward compatible | New field `discount_code` appears |
| **Add required field** | ❌ Breaking (consumers don't send it) | New `vat_amount` required |
| **Remove field** | ❌ Breaking | `product_name` removed — your query crashes |
| **Rename field** | ❌ Breaking | `price` → `unit_price` |
| **Change data type** | ❌ Breaking | `quantity` INT → STRING |
| **Reorder fields** | ✅ Safe (if using named fields) | Order of JSON keys changed |
| **Nest previously flat field** | ❌ Breaking | `city` → `address.city` |

**The asymmetry**: adding fields is safe — you can ignore them. Removing or renaming is catastrophic — you can't reference a field that no longer exists.

---

## The Core Design Principle

```
The further downstream a schema change travels before being caught,
the more harm it causes.

Catch at Layer 1 (landing zone) → raw data safe, transform job fails → easy fix
Catch at Layer 4 (dashboard)   → dashboard crashes → users see errors → incident
```

**Defence in depth: absorb as close to the source as possible.**

---

## 4-Layer Defence Architecture

```
API (external — schema can change any time)
        │
        ▼
[Layer 1] GCS Landing Zone (raw JSON/Avro)
         ─ No schema enforcement
         ─ Raw bytes always land safely
         ─ "Schema shock absorber"
        │
        ▼
[Layer 2] Pub/Sub Schema Registry (streaming) OR manual schema diff check (batch)
         ─ Structural validation BEFORE processing
         ─ Invalid messages rejected or routed to DLQ
        │
        ▼
[Layer 3] Pipeline Schema Validation + DLQ Split
         ─ Required field presence check
         ─ Type coercion / validation
         ─ Alert on drift (new or missing fields)
         ─ Invalid rows → dead letter queue
        │
        ▼
[Layer 4] BigQuery — ALLOW_FIELD_ADDITION + `_raw_extras` column
         ─ New fields automatically accepted as nullable columns
         ─ Unknown fields stored as JSON string in _raw_extras
        │
        ▼
[View / Mart Layer] — THE CONTRACT WITH DASHBOARDS
         ─ Dashboard reads from this view, not from raw table
         ─ View selects only stable, named columns
         ─ Raw table schema can evolve; view doesn't change until you explicitly update it
        │
        ▼
[Dashboard / Looker Studio]
         ─ Sees a stable interface regardless of upstream changes
```

---

## Layer 1: GCS Landing Zone (Raw First)

**Never write API data directly into a typed, structured table. Always land raw first.**

```python
# Pipeline: API webhook → this Cloud Function → GCS (raw JSON)
import functions_framework
from google.cloud import storage
import json, datetime, uuid

@functions_framework.http
def receive_api_event(request):
    raw_body = request.get_data(as_text=True)  # Accept ANYTHING — no parsing
    
    # Write raw bytes to GCS — content unknown, schema unknown, doesn't matter
    client = storage.Client()
    bucket = client.bucket("your-project-portfolio-raw")
    
    today = datetime.date.today().isoformat()
    filename = f"api-events/{today}/{uuid.uuid4()}.json"
    blob = bucket.blob(filename)
    blob.upload_from_string(raw_body, content_type="application/json")
    
    return "OK", 200  # Always return 200 to the API — never reject at ingestion

# Why: If you parse and validate here and the schema changed, you return 500 to the API.
# The API producer retries, you get duplicates, and the data is lost during the incident.
# Landing raw means: data is ALWAYS safe. Only processing fails.
```

**Rule:** The landing zone is append-only, schema-free, forever. Data is never mutated here. Think of it as your "source of truth safety net."

---

## Layer 2: Pub/Sub Schema Registry (Streaming Path)

For real-time streaming (Pub/Sub producer), enforce schema at the topic level:

```bash
# Create Avro schema for the current API contract
cat > schema_v1.avsc << 'EOF'
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "order_id",     "type": "string"},
    {"name": "customer_id",  "type": "string"},
    {"name": "amount",       "type": "double"},
    {"name": "channel",      "type": "string"},
    {"name": "event_ts",     "type": "string"}
  ]
}
EOF

# Register schema with Pub/Sub
gcloud pubsub schemas create orders-schema-v1 \
  --type=avro \
  --definition-file=schema_v1.avsc

# Attach schema to topic
gcloud pubsub topics create api-orders \
  --schema=orders-schema-v1 \
  --message-encoding=json
```

**Schema evolution compatibility modes:**

| Mode | Rule | Use When |
|---|---|---|
| `BACKWARD` | New schema can read old data | You control the consumer, not the producer |
| `FORWARD` | Old schema can read new data | You control the producer, not the consumer |
| `FULL` | Both directions | You control neither — safest |
| `NONE` | No compatibility check | Experimenting only — never production |

**For your scenario (external API that changes):** You cannot enforce Pub/Sub schema on their side unless you control the Pub/Sub topic. If you own the webhook endpoint, use Layer 1 + Layer 3 instead.

---

## Layer 3: Pipeline Validation + Dead Letter Queue

The most important defensive layer you directly control:

```python
import jsonschema
from google.cloud import pubsub_v1

# ─── Define your expected schema ────────────────────────────
# additionalProperties: True  ← CRITICAL: allows new upstream fields without failing
# Required only list the fields you MUST have to process the record
EXPECTED_SCHEMA = {
    "type": "object",
    "required": ["order_id", "amount", "customer_id"],  # only what you truly need
    "properties": {
        "order_id":    {"type": "string"},
        "amount":      {"type": "number", "minimum": 0},
        "customer_id": {"type": "string"},
        "channel":     {"type": "string", "enum": ["PHYSICAL", "DIGITAL"]},
    },
    "additionalProperties": True,   # ← New fields from API silently accepted
}

def validate_and_route(raw_record: dict) -> tuple[str, dict]:
    """
    Returns ('valid', record) or ('dead_letter', error_record).
    
    Safe against:
    ✓ New fields added by API  → accepted (additionalProperties: True)
    ✓ Optional fields removed  → accepted (not in 'required')
    ✗ Required fields removed  → DLQ
    ✗ Type change (str→int)    → DLQ
    """
    try:
        jsonschema.validate(raw_record, EXPECTED_SCHEMA)
        return "valid", raw_record
    except jsonschema.ValidationError as e:
        return "dead_letter", {
            "raw_record":   str(raw_record),
            "error":        e.message,
            "failed_field": list(e.path),
            "received_ts":  datetime.utcnow().isoformat(),
        }
```

**Schema drift detection — proactive alerting:**

```python
KNOWN_FIELDS = {"order_id", "amount", "customer_id", "channel", "event_ts"}

def detect_and_alert_schema_drift(incoming_record: dict, table: str) -> None:
    incoming_fields = set(incoming_record.keys())
    
    new_fields     = incoming_fields - KNOWN_FIELDS  # API added something
    missing_fields = KNOWN_FIELDS - incoming_fields  # API removed something

    if missing_fields:
        # ⚠️ CRITICAL: fields we depend on are gone
        send_slack_alert(
            channel="#data-engineering",
            message=f"BREAKING SCHEMA CHANGE in {table}: removed fields {missing_fields}. "
                    f"Pipeline routing to DLQ.",
            severity="CRITICAL",
        )
    
    if new_fields:
        # ℹ️ INFO: new fields we don't know about yet
        log.info(f"Schema additive change in {table}: new fields {new_fields}. "
                 f"Storing in _raw_extras.")
        # Store new fields in the _raw_extras JSON column (see Layer 4)
```

---

## Layer 4: BigQuery Schema Evolution Modes

```python
from google.cloud import bigquery

# ─── Option A: Auto-add new columns ──────────────────────────
# When API adds a new field, BigQuery automatically adds a nullable column.
# This is the preferred option for controlled schema growth.
job_config = bigquery.LoadJobConfig(
    schema_update_options=[
        bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,    # new columns OK
        bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION,  # REQUIRED → NULLABLE OK
    ],
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
)

# ─── Option B: _raw_extras catch-all column ──────────────────
# Add a JSON STRING column to your BQ table called _raw_extras.
# Any unrecognized field from the API lands here as a JSON blob.
# You can promote it to a proper column later once you understand it.

def to_bq_row(record: dict) -> dict:
    known_cols = {"order_id", "amount", "customer_id", "channel", "event_ts"}
    row = {k: v for k, v in record.items() if k in known_cols}
    
    extras = {k: v for k, v in record.items() if k not in known_cols}
    row["_raw_extras"] = json.dumps(extras) if extras else None
    
    return row

# Later, when "discount_code" appears in _raw_extras for 2 weeks and you understand it:
# ALTER TABLE raw_orders ADD COLUMN discount_code STRING;
# Backfill: UPDATE raw_orders SET discount_code = JSON_VALUE(_raw_extras, '$.discount_code')
#           WHERE _raw_extras IS NOT NULL;
```

---

## The Views Are the Contract — Most Important Concept

```sql
-- Raw table: schema can evolve freely
-- raw_orders may have 50 columns and _raw_extras with random new fields

-- The VIEW is the contract that dashboards reference:
CREATE OR REPLACE VIEW mart.orders_dashboard AS
SELECT
  order_id,
  customer_id,
  amount,
  COALESCE(channel, 'UNKNOWN')       AS channel,  -- handle if channel goes missing
  DATE(event_ts)                     AS order_date,
  -- New field added to raw table that we've validated and promoted:
  JSON_VALUE(_raw_extras, '$.discount_code') AS discount_code
FROM raw_orders
WHERE amount > 0   -- basic quality filter at view level
;

-- Dashboard reads from mart.orders_dashboard — NEVER from raw_orders directly
-- When API changes: raw table absorbs the change. View stays stable.
-- You update the VIEW deliberately, with testing, not accidentally.
```

**dbt makes this pattern explicit:**
```sql
-- models/mart/orders_dashboard.sql
{{ config(materialized='view') }}

SELECT
  order_id,
  customer_id,
  amount,
  COALESCE(channel, 'UNKNOWN') AS channel,
  DATE(TIMESTAMP(event_ts))    AS order_date
FROM {{ ref('raw_orders') }}    -- ref() enforces DAG ordering
WHERE amount > 0
```

```yaml
# schema.yml — dbt tests protect the contract
models:
  - name: orders_dashboard
    columns:
      - name: order_id
        tests: [not_null, unique]
      - name: amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"
```

When the API schema breaks, `dbt test` fails in CI/CD → deployment blocked → engineer notified → dashboard never sees the broken data.

---

## Scenario: API Changes `price` from FLOAT to STRING

**Without defence:**
```
API → BigQuery WRITE APPEND → ERROR: type mismatch → pipeline crashes → no new data → dashboard goes stale
```

**With defence:**
```
API → GCS landing zone (raw JSON, always safe)
    → Pipeline reads JSON → validate_and_route:
        "amount": "149.99"  ← string, expected number → ValidationError → DLQ
    → Alert fires: "SCHEMA CHANGE: amount type mismatch"
    → Raw data in GCS is safe — not lost
    → Pipeline paused until engineer fixes the type coercion:
        amount = float(record["amount"])  # handle string→float
    → Backfill from GCS after fix
    → Dashboard reads view — shows slightly stale data but does NOT crash
```

---

## Alert Template

```python
def send_schema_alert(table: str, change_type: str, details: dict):
    """Called when schema drift is detected."""
    from google.cloud import monitoring_v3
    
    # Option 1: Custom Cloud Monitoring metric
    client = monitoring_v3.MetricServiceClient()
    # ... publish custom metric: "schema_drift/breaking_changes" count
    
    # Option 2: Direct Slack webhook (simpler for POC)
    import requests
    message = {
        "text": f"⚠️ Schema drift detected in `{table}`\n"
                f"Type: `{change_type}`\n"
                f"Details: `{details}`\n"
                f"Action: Check DLQ at `{DLQ_TABLE}` and GCS raw at `{GCS_PATH}`"
    }
    requests.post(SLACK_WEBHOOK_URL, json=message)
```

---

## Answer Skeleton (Memorize This)

```
"I'd build four layers of defence between the external API and the dashboard.

1. LANDING ZONE: All API data lands as raw JSON in GCS first — no schema enforcement.
   This means raw data is NEVER lost, even when the schema breaks.
   The pipeline can fail and recover without data loss.

2. SCHEMA VALIDATION IN THE PIPELINE: jsonschema validation with
   'additionalProperties: True' — new fields from the API are silently accepted.
   Only missing required fields or type mismatches fail validation.
   Failed records go to a dead letter queue; an alert fires immediately.

3. BIGQUERY ALLOW_FIELD_ADDITION + _raw_extras column:
   New API fields either auto-create nullable BQ columns or land in a catch-all
   JSON column until we understand them and officially promote them.

4. VIEWS AS THE CONTRACT: Dashboards NEVER query the raw table directly.
   They query a view in the mart layer. The view selects only stable, validated columns.
   When the API changes, the view stays unchanged until we deliberately update it.
   This is the most important isolation layer.

Proactive: I'd add schema drift detection — compare incoming fields to expected.
New fields → INFO log. Missing required fields → CRITICAL alert + DLQ.
The DLQ and GCS raw are always recoverable — once the schema is fixed, we reprocess."
```

---

## Flash Cards

| Question | Answer |
|---|---|
| Which schema change is safe? | Adding optional fields — consumers can ignore them |
| Which schema changes are breaking? | Remove field, rename field, change type — your queries break |
| What is `additionalProperties: True`? | jsonschema setting that allows unknown fields — critical for forward compatibility |
| What is a dead letter queue? | Where invalid messages go when validation fails — for later inspection and replay |
| Why land raw in GCS first? | If validation fails, raw data is not lost — you can reprocess once schema is fixed |
| What is the view contract principle? | Dashboard reads from a view, not raw table — view is the stable API for consumers |
| What is `ALLOW_FIELD_ADDITION` in BigQuery? | BigQuery option that auto-adds new columns as NULLABLE when loading new schema |
| What is `_raw_extras`? | A JSON STRING column in BQ that catches unknown fields until they're promoted |
| What is a Schema Registry? | Service that stores versioned schemas and enforces compatibility rules |
| What dbt feature enforces the contract? | `dbt test` — runs schema tests on each model; fails CI/CD if contract is broken |

---

## Practice Questions (6 Minutes Each)

1. **"The external API team emails you: 'We renamed `customer_id` to `user_id` tomorrow.' What's your response and action plan?"**
   → Rename is breaking. Plan: (1) Add coalesce in pipeline: `customer_id = record.get("customer_id") or record.get("user_id")`. (2) Update expected schema. (3) Ask API team to support both fields for a 2-week transition. (4) Coordinate cutover date.

2. **"Your pipeline processes 1M events/day. DLQ starts filling up at 30% of events. What do you investigate?"**
   → Check DLQ error messages: is it a type mismatch? Missing field? Check schema drift alert — API likely changed something. Compare oldest DLQ message timestamp to deployment timeline.

3. **"The dashboard shows stale data since 3am. Pipeline logs show no errors. What happened?"**
   → Dashboard is reading from a view. View might have a JOIN to a table that schema-changed and now returns 0 rows (filtering behavior changed). Check view definition. Also check: did the API stop sending data? Check GCS landing zone for new files.

4. **"How does dbt handle schema evolution differently from raw BigQuery writes?"**
   → dbt rebuilds models from SQL each run — column additions are transparent. Type changes fail at model build time (compile error). dbt tests catch missing nullable columns early in CI, before deployment.
