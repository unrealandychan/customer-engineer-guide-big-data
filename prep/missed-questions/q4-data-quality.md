# Q4 Study Material — Data Quality Monitoring (Cloud + On-Site)
**Study Days: Day 5 (Cloud, 1.5h) + Day 6 (On-Site, 1h)**

---

## The Question (verbatim)
> "How do you maintain high data quality? And keep checking that, with alarm and metric? Give all the implementation on cloud and on-site."

## What the Interviewer Wants
- A structured framework (not a random list of checks)
- Specific tooling on GCP (native) vs. on-premises
- Monitoring + alerting, not just one-off checks
- The pipeline: check → metric → alert → action

---

## The 6 Dimensions of Data Quality

Always open with this framework — it shows structured thinking.

| Dimension | "Is the data..." | Example SQL Check |
|---|---|---|
| **Completeness** | All expected records and fields present? | `COUNT(*) WHERE order_id IS NULL = 0` |
| **Uniqueness** | No duplicate primary keys? | `COUNT(*) = COUNT(DISTINCT order_id)` |
| **Validity** | Values within allowed domain/range? | `amount_usd > 0 AND channel IN ('PHYSICAL','DIGITAL')` |
| **Timeliness** | Data arrives within SLA? | `MAX(event_ts) > NOW() - INTERVAL '1 HOUR'` |
| **Consistency** | Same figures across systems? | BQ order count = source API order count |
| **Accuracy** | Values reflect real-world truth? | Sum of line items = order total (cross-field check) |

**Rule:** For each table you own, define at least one check per dimension. Partial coverage = partial quality.

---

## DQ Implementation: Cloud (GCP)

### Option 1: BigQuery Scheduled Queries (No Extra Tooling — Start Here)

Write DQ checks as SQL. Schedule them in BigQuery. Write results to a `monitoring.dq_results` table. Alert on failures.

**Step 1 — Create the results table:**
```sql
CREATE TABLE IF NOT EXISTS `project.monitoring.dq_results` (
  check_ts       TIMESTAMP NOT NULL,
  table_name     STRING    NOT NULL,
  check_name     STRING    NOT NULL,   -- e.g., "completeness_order_id"
  dimension      STRING    NOT NULL,   -- COMPLETENESS | UNIQUENESS | VALIDITY | TIMELINESS
  failed_rows    INT64     NOT NULL,
  total_rows     INT64     NOT NULL,
  failure_pct    FLOAT64,
  status         STRING    NOT NULL,   -- 'PASS' | 'FAIL'
  threshold_pct  FLOAT64               -- configured acceptable failure rate
)
PARTITION BY DATE(check_ts);
```

**Step 2 — Write DQ check SQL (runs as hourly scheduled query):**
```sql
INSERT INTO `project.monitoring.dq_results`

-- ── COMPLETENESS: no null order_ids ──────────────────────────
SELECT
  CURRENT_TIMESTAMP()                           AS check_ts,
  'raw_brand_a.orders'                          AS table_name,
  'completeness_order_id'                       AS check_name,
  'COMPLETENESS'                                AS dimension,
  COUNTIF(order_id IS NULL)                     AS failed_rows,
  COUNT(*)                                      AS total_rows,
  SAFE_DIVIDE(COUNTIF(order_id IS NULL), COUNT(*)) * 100  AS failure_pct,
  IF(COUNTIF(order_id IS NULL) = 0, 'PASS', 'FAIL')       AS status,
  0.0                                           AS threshold_pct   -- zero tolerance
FROM `project.raw_brand_a.orders`
WHERE DATE(transaction_ts) = CURRENT_DATE()

UNION ALL

-- ── UNIQUENESS: no duplicate orders ──────────────────────────
SELECT
  CURRENT_TIMESTAMP(),
  'raw_brand_a.orders',
  'uniqueness_order_id',
  'UNIQUENESS',
  COUNT(*) - COUNT(DISTINCT order_id),
  COUNT(*),
  SAFE_DIVIDE(COUNT(*) - COUNT(DISTINCT order_id), COUNT(*)) * 100,
  IF(COUNT(*) = COUNT(DISTINCT order_id), 'PASS', 'FAIL'),
  0.0
FROM `project.raw_brand_a.orders`
WHERE DATE(transaction_ts) = CURRENT_DATE()

UNION ALL

-- ── VALIDITY: amount must be positive, channel must be known ─
SELECT
  CURRENT_TIMESTAMP(),
  'raw_brand_a.orders',
  'validity_amount_and_channel',
  'VALIDITY',
  COUNTIF(amount_usd <= 0 OR channel NOT IN ('PHYSICAL', 'DIGITAL')),
  COUNT(*),
  SAFE_DIVIDE(COUNTIF(amount_usd <= 0 OR channel NOT IN ('PHYSICAL', 'DIGITAL')), COUNT(*)) * 100,
  IF(COUNTIF(amount_usd <= 0 OR channel NOT IN ('PHYSICAL', 'DIGITAL')) = 0, 'PASS', 'FAIL'),
  0.5   -- up to 0.5% invalid rows tolerated (data entry errors)
FROM `project.raw_brand_a.orders`
WHERE DATE(transaction_ts) = CURRENT_DATE()

UNION ALL

-- ── TIMELINESS: last record must be within 1 hour ────────────
SELECT
  CURRENT_TIMESTAMP(),
  'raw_brand_a.orders',
  'timeliness_freshness',
  'TIMELINESS',
  IF(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(transaction_ts), HOUR) > 1, 1, 0),
  1,
  NULL,
  IF(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(transaction_ts), HOUR) <= 1, 'PASS', 'FAIL'),
  NULL
FROM `project.raw_brand_a.orders`

UNION ALL

-- ── CONSISTENCY: row count matches yesterday's average ────────
SELECT
  CURRENT_TIMESTAMP(),
  'raw_brand_a.orders',
  'consistency_row_volume',
  'CONSISTENCY',
  CASE WHEN ABS(today_count - avg_count) / NULLIF(avg_count, 0) > 0.30
       THEN 1 ELSE 0 END,
  1,
  ABS(today_count - avg_count) / NULLIF(avg_count, 0) * 100,
  CASE WHEN ABS(today_count - avg_count) / NULLIF(avg_count, 0) <= 0.30
       THEN 'PASS' ELSE 'FAIL' END,
  30.0  -- alert if volume deviates > 30% from 7-day average
FROM (
  SELECT
    COUNTIF(DATE(transaction_ts) = CURRENT_DATE())   AS today_count,
    AVG(COUNTIF(DATE(transaction_ts) = day))
      OVER ()                                         AS avg_count
  FROM `project.raw_brand_a.orders`,
       UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY),
                                  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))) AS day
  GROUP BY day
) LIMIT 1
;
```

**Step 3 — Alert on FAIL rows using Cloud Monitoring:**
```python
# cloud_function/dq_alerter.py — triggered by BQ scheduled query completion
# or by a Cloud Scheduler cron → HTTP Cloud Function

from google.cloud import bigquery, monitoring_v3
import json, time

def check_and_alert(request):
    bq = bigquery.Client()
    
    # Find any FAILs in the last 2 hours
    sql = """
        SELECT check_name, table_name, dimension, failed_rows, failure_pct
        FROM `project.monitoring.dq_results`
        WHERE status = 'FAIL'
          AND check_ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
          AND failure_pct > threshold_pct
    """
    fails = list(bq.query(sql).result())
    
    if fails:
        # Publish custom metric
        publish_dq_metric(project="your-project", fail_count=len(fails))
        
        # Detailed Slack alert
        for row in fails:
            send_slack_alert(f"""
🚨 *Data Quality FAIL*
• Table: `{row.table_name}`
• Check: `{row.check_name}` ({row.dimension})
• Failed rows: {row.failed_rows:,} ({row.failure_pct:.2f}%)
• Action: Check `monitoring.dq_results` for details
            """)
    
    return f"Checked {len(fails)} fails", 200

def publish_dq_metric(project, fail_count):
    client = monitoring_v3.MetricServiceClient()
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/data_quality/fail_count"
    series.metric.labels["project"] = project
    series.resource.type = "global"
    
    point = monitoring_v3.Point()
    point.value.int64_value = fail_count
    now = time.time()
    point.interval.end_time.seconds = int(now)
    series.points = [point]
    
    client.create_time_series(
        name=f"projects/{project}", time_series=[series]
    )
```

---

### Option 2: dbt Tests (Best Practice for Transform Layer)

dbt runs DQ tests automatically as part of every pipeline run. Fail = block deployment.

```yaml
# models/canonical/schema.yml
version: 2

models:
  - name: customer_360
    description: "Unified canonical customer with cross-brand metrics."
    columns:
      - name: customer_key
        description: "SHA-256 deterministic hash of brand_id|source_id"
        tests:
          - not_null              # built-in: no nulls
          - unique                # built-in: no duplicates

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
              # first order must not be after last order
              expression: "<= last_order_date"

      - name: total_orders
        tests:
          - dbt_utils.expression_is_true:
              expression: "> 0"

      - name: cross_brand_flag
        tests:
          - not_null
          - accepted_values:
              values: [true, false]

  # Source freshness check (timeliness)
sources:
  - name: raw_brand_a
    database: project
    tables:
      - name: orders
        freshness:
          warn_after: {count: 1, period: hour}   # warn at 1h
          error_after: {count: 3, period: hour}  # fail at 3h
        loaded_at_field: transaction_ts
```

**Run dbt tests in CI/CD (Cloud Build):**
```yaml
# cloudbuild.yaml
steps:
  - name: 'python:3.11'
    entrypoint: bash
    args:
      - -c
      - |
        pip install dbt-bigquery dbt-utils --quiet
        dbt deps
        dbt test --target prod --select canonical --store-failures
        # --store-failures: failing rows are written to BQ for inspection
options:
  logging: CLOUD_LOGGING_ONLY
```

If `dbt test` fails → `cloudbuild` step fails → Cloud Build triggers PubSub → alert fires → deployment blocked.

---

### Option 3: Dataplex Data Quality (GCP Native, No Code)

**What it is:** Dataplex has a built-in DQ service (GA). You define rules in YAML, Dataplex scans your BQ tables, writes results to BigQuery, integrates with Cloud Monitoring.

```yaml
# dataplex_dq_spec.yaml — upload to Cloud Storage, reference in Dataplex DQ task
rules:
  - column: order_id
    rule_type: NOT_NULL
    dimension: COMPLETENESS

  - column: order_id
    rule_type: UNIQUENESS
    dimension: UNIQUENESS

  - column: amount_usd
    rule_type: RANGE
    min_value: 0.01
    max_value: 100000
    dimension: VALIDITY

  - column: channel
    rule_type: REGEX
    regex: "PHYSICAL|DIGITAL"
    dimension: VALIDITY

  - rule_type: ROW_CONDITION
    sql_expression: "amount_usd > 0 AND order_id IS NOT NULL AND channel IS NOT NULL"
    dimension: VALIDITY
    threshold: 0.995   # 99.5% of rows must pass

  - rule_type: FRESHNESS
    column: transaction_ts
    staleness_threshold: "PT1H"   # ISO 8601 duration: 1 hour
    dimension: TIMELINESS
```

```bash
# Create Dataplex DQ task
gcloud dataplex tasks create dq-orders-hourly \
  --lake=retail-lake \
  --location=us-central1 \
  --trigger-type=RECURRING \
  --trigger-schedule="0 * * * *" \   # every hour
  --execution-service-account=dq-runner@project.iam.gserviceaccount.com \
  --data-scan-id=orders-dq-scan
```

Results auto-write to BigQuery + appear in Dataplex UI. **Integrates natively with Cloud Monitoring** — no custom metric code needed.

---

### Option 4: Great Expectations (Open Source — Cloud + On-Prem)

Great Expectations (GX) runs anywhere and is the industry-standard open-source DQ tool:

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

# Initialize context (can be file-based or cloud-based with GX Cloud)
context = gx.get_context()

# Connect to BigQuery datasource
datasource = context.sources.add_or_update_bigquery(
    name="bigquery_source",
    project="your-project-id",
    dataset="raw_brand_a",
)

batch_request = datasource.get_asset("orders").build_batch_request()
validator = context.get_validator(batch_request=batch_request)

# ─── Define expectations (the DQ rules) ──────────────────────
validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_be_unique("order_id")

validator.expect_column_values_to_be_between(
    "amount_usd", min_value=0.01, max_value=100_000
)

validator.expect_column_values_to_be_in_set(
    "channel", {"PHYSICAL", "DIGITAL"}
)

validator.expect_column_pair_values_a_to_be_greater_than_b(
    column_A="last_order_date",
    column_B="first_order_date",
    or_equal=True,
)

# Freshness: max transaction_ts must be within 1 hour
validator.expect_column_max_to_be_between(
    "transaction_ts",
    min_value=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
    max_value=datetime.utcnow().isoformat(),
)

# ─── Run validation ───────────────────────────────────────────
results = validator.validate()

if not results.success:
    failed = [r for r in results.results if not r.success]
    for f in failed:
        print(f"FAIL: {f.expectation_config.expectation_type} on {f.expectation_config.kwargs}")
    
    # Send alert and optionally fail the pipeline
    raise ValueError(f"Data quality validation failed: {len(failed)} checks failed")

# GX generates an HTML Data Docs report automatically:
context.build_data_docs()
# → Open file://local/great_expectations/uncommitted/data_docs/local_site/index.html
```

**Key advantage of GX:** Generates **Data Docs** — a human-readable HTML report of all expectations + pass/fail results. Share with stakeholders as a DQ report.

---

## DQ Implementation: On-Premises

### Option 1: Airflow Data Quality Operators

Run DQ checks as Airflow tasks. If a check fails, the task fails → DAG marked failed → alert fires. This integrates DQ natively into the pipeline.

```python
from airflow import DAG
from airflow.providers.common.sql.operators.sql import (
    SQLCheckOperator,     # runs SQL, fails if result is falsy
    SQLValueCheckOperator,# runs SQL, fails if result != expected value
    SQLThresholdCheckOperator,  # fails if result outside min/max bounds
)
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from datetime import datetime, timedelta

DEFAULT_ARGS = {
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": lambda ctx: alert_on_failure(ctx),
}

with DAG(
    dag_id="dq_checks_hourly",
    schedule_interval="@hourly",
    start_date=datetime(2026, 1, 1),
    default_args=DEFAULT_ARGS,
    catchup=False,
) as dag:

    # ── COMPLETENESS: no null order_ids ──
    check_no_nulls = SQLCheckOperator(
        task_id="check_completeness_order_id",
        conn_id="postgres_warehouse",
        sql="""
            SELECT CASE
              WHEN COUNTIF(order_id IS NULL) = 0 THEN TRUE
              ELSE FALSE
            END AS is_valid
            FROM orders
            WHERE DATE(transaction_ts) = CURRENT_DATE
        """,
    )

    # ── UNIQUENESS: zero duplicate order_ids ──
    check_uniqueness = SQLValueCheckOperator(
        task_id="check_uniqueness_order_id",
        conn_id="postgres_warehouse",
        sql="""
            SELECT COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_count
            FROM orders
            WHERE DATE(transaction_ts) = CURRENT_DATE
        """,
        pass_value=0,         # must be zero
        tolerance=0,          # zero tolerance
    )

    # ── VALIDITY: amount within bounds ──
    check_amount_validity = SQLThresholdCheckOperator(
        task_id="check_validity_amount",
        conn_id="postgres_warehouse",
        sql="""
            SELECT COUNTIF(amount_usd <= 0 OR amount_usd > 100000) / COUNT(*) * 100
            FROM orders
            WHERE DATE(transaction_ts) = CURRENT_DATE
        """,
        min_threshold=0,      # failure rate between 0% and 0.5%
        max_threshold=0.5,
    )

    # ── TIMELINESS: last record within 1 hour ──
    check_freshness = SQLCheckOperator(
        task_id="check_timeliness_freshness",
        conn_id="postgres_warehouse",
        sql="""
            SELECT EXTRACT(EPOCH FROM (NOW() - MAX(transaction_ts))) / 3600 < 1
            FROM orders
        """,
    )

    # ── CONSISTENCY: volume anomaly detection ──
    check_volume_anomaly = SQLCheckOperator(
        task_id="check_consistency_volume",
        conn_id="postgres_warehouse",
        sql="""
            WITH today AS (
              SELECT COUNT(*) AS cnt FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE
            ),
            avg_7d AS (
              SELECT AVG(daily_count) AS avg_cnt
              FROM (
                SELECT DATE(transaction_ts), COUNT(*) AS daily_count
                FROM orders
                WHERE transaction_ts >= NOW() - INTERVAL '7 days'
                  AND DATE(transaction_ts) < CURRENT_DATE
                GROUP BY 1
              ) sub
            )
            SELECT ABS(today.cnt - avg_7d.avg_cnt) / NULLIF(avg_7d.avg_cnt, 0) < 0.30
            FROM today, avg_7d
        """,
    )

    # ── DQ Gate: all checks must pass before downstream tasks ──
    [check_no_nulls, check_uniqueness, check_amount_validity,
     check_freshness, check_volume_anomaly]
```

**On-failure callback that sends Slack alert:**
```python
def alert_on_failure(context):
    from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
    
    dag_id  = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    exec_dt = context['execution_date']
    log_url = context['task_instance'].log_url
    
    SlackWebhookHook(
        slack_webhook_conn_id="slack_webhook_dq",
    ).send(
        text=f"🚨 *DQ Check Failed*\n"
             f"• DAG: `{dag_id}`\n"
             f"• Task: `{task_id}`\n"
             f"• Execution: {exec_dt}\n"
             f"• Logs: {log_url}"
    )
```

---

### Option 2: Prometheus + Grafana (Real-Time Metrics)

Export DQ metrics as Prometheus metrics → Grafana dashboard → Grafana alerts to PagerDuty/Slack.

```python
# dq_exporter.py — runs as a sidecar service on port 8080, scraped by Prometheus every 60s
from prometheus_client import start_http_server, Gauge, Counter
import psycopg2, time, logging

# ── Define Prometheus metrics ─────────────────────────────────
DQ_NULL_COUNT        = Gauge("dq_null_count",        "Null primary keys",       ["table", "column"])
DQ_DUPLICATE_COUNT   = Gauge("dq_duplicate_count",   "Duplicate primary keys",  ["table", "column"])
DQ_INVALID_COUNT     = Gauge("dq_invalid_count",     "Invalid value rows",      ["table", "check"])
DQ_FRESHNESS_SECONDS = Gauge("dq_freshness_seconds", "Seconds since last row",  ["table"])
DQ_ROW_COUNT         = Gauge("dq_row_count",         "Total rows (today)",      ["table"])

def collect_metrics():
    conn = psycopg2.connect("postgresql://analyst:pass@localhost:5432/warehouse")
    cur  = conn.cursor()
    
    # Completeness
    cur.execute("SELECT COUNT(*) FROM orders WHERE order_id IS NULL AND DATE(transaction_ts) = CURRENT_DATE")
    DQ_NULL_COUNT.labels(table="orders", column="order_id").set(cur.fetchone()[0])
    
    # Uniqueness
    cur.execute("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE")
    DQ_DUPLICATE_COUNT.labels(table="orders", column="order_id").set(cur.fetchone()[0])
    
    # Validity
    cur.execute("SELECT COUNTIF(amount_usd <= 0 OR channel NOT IN ('PHYSICAL','DIGITAL')) FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE")
    DQ_INVALID_COUNT.labels(table="orders", check="amount_and_channel").set(cur.fetchone()[0])
    
    # Timeliness
    cur.execute("SELECT EXTRACT(EPOCH FROM (NOW() - MAX(transaction_ts))) FROM orders")
    DQ_FRESHNESS_SECONDS.labels(table="orders").set(cur.fetchone()[0] or 99999)
    
    # Row volume
    cur.execute("SELECT COUNT(*) FROM orders WHERE DATE(transaction_ts) = CURRENT_DATE")
    DQ_ROW_COUNT.labels(table="orders").set(cur.fetchone()[0])
    
    conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_http_server(8080)                    # Prometheus scrapes :8080/metrics
    logging.info("DQ Exporter running on :8080")
    while True:
        collect_metrics()
        time.sleep(60)
```

**Grafana Alert Rules (`alert_rules.yaml`):**
```yaml
groups:
  - name: data_quality
    interval: 1m
    rules:

      - alert: DQNullsDetected
        expr: dq_null_count{table="orders"} > 0
        for: 5m
        labels:
          severity: critical
          team: data-engineering
        annotations:
          summary: "NULL primary keys detected in {{ $labels.table }}.{{ $labels.column }}"
          description: "{{ $value }} null order_ids found. Check ingestion pipeline."

      - alert: DQDuplicatesDetected
        expr: dq_duplicate_count{table="orders"} > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Duplicate order_ids: {{ $value }} duplicates in orders"

      - alert: DQFreshnessViolation
        expr: dq_freshness_seconds{table="orders"} > 3600
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "orders table stale: no new data for {{ humanizeDuration $value }}"

      - alert: DQVolumeAnomaly
        # >30% drop vs 7-day average calculated by recording rule
        expr: |
          abs(dq_row_count - dq_row_count_7d_avg) / dq_row_count_7d_avg > 0.30
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Volume anomaly: today's count deviates >30% from 7-day average"
```

**Prometheus scrape config (`prometheus.yml`):**
```yaml
scrape_configs:
  - job_name: 'data_quality_exporter'
    static_configs:
      - targets: ['dq-exporter-host:8080']
    scrape_interval: 60s
```

---

### Option 3: Apache Atlas (On-Prem Data Catalog + Lineage)

```
Atlas use cases for DQ:
1. Tag columns as PII / Critical / Derived
2. Track lineage: "table X comes from tables A and B"
   → If A has a DQ issue, Atlas shows all downstream tables affected
3. Classify tables by DQ tier: BRONZE (raw, no checks), SILVER (validated), GOLD (curated)
4. Integrate with Apache Ranger: enforce column access based on Atlas classification
```

---

## DQ SLA Definition

Before implementing anything, define your SLAs explicitly:

| Metric | SLA Threshold | Alert | Escalation |
|---|---|---|---|
| Completeness (order_id) | 100% — zero nulls | Immediate Slack | PagerDuty if >1h unresolved |
| Uniqueness (order_id) | 100% — zero dupes | Immediate Slack | PagerDuty if >1h |
| Validity (amount, channel) | ≥ 99.5% valid | Slack within 15m | PagerDuty if >20% invalid |
| Timeliness (freshness) | Max 1h stale | Immediate Slack at 1h | PagerDuty at 2h |
| Consistency (volume) | Within ±30% of 7d avg | Slack (warning) | PagerDuty if >50% |

---

## Full Tool Comparison

| Tool | Cloud / On-Prem | Complexity | Best For |
|---|---|---|---|
| BigQuery Scheduled Queries | GCP only | Low | Quick wins, no extra tooling |
| dbt tests | Both | Low–Med | Transform layer, CI/CD integration |
| Dataplex DQ | GCP only | Low | No-code, native BQ, Dataplex users |
| Great Expectations | Both | Med | Batch DQ, stakeholder Data Docs reports |
| Airflow SQLCheckOperator | Both | Low | Pipeline-integrated DQ gates |
| Prometheus + Grafana | On-prem / any | High | Real-time metrics, existing Grafana stack |
| Apache Atlas | On-prem | High | Governance, lineage, classification |

**Recommended stack for a GCP-first company:**
`dbt tests` (daily pipeline) + `Dataplex DQ` (hourly) + `Cloud Monitoring alerts`

**Recommended stack for on-prem / hybrid:**
`Airflow SQLCheckOperator` (pipeline gates) + `Great Expectations` (batch profiling) + `Prometheus + Grafana` (real-time metrics)

---

## Answer Skeleton (Memorize This)

```
"I'd approach data quality across three concerns: what to check, how to surface it, and how to act on it.

WHAT TO CHECK — 6 Dimensions:
Completeness (no unexpected nulls), Uniqueness (no duplicate keys),
Validity (values within domain), Timeliness (data not stale),
Consistency (figures match across systems), Accuracy (cross-field sanity checks).
For each table I own, I define at least one check per dimension.

HOW TO IMPLEMENT — depends on the environment:

On GCP:
  - dbt tests on the transform layer — runs every pipeline execution, blocks deployment on failure
  - BigQuery scheduled queries writing to dq_results table — hourly, all 6 dimensions in SQL
  - Dataplex DQ for no-code continuous scanning with native BQ integration
  - Cloud Monitoring custom metric from dq_results → alert policy fires to Slack/PagerDuty

On-premises:
  - Airflow SQLCheckOperator — DQ checks as pipeline tasks, fail → DAG fails → alert
  - Prometheus exporter — DQ metrics scraped every 60s by Prometheus → Grafana dashboard + alert rules
  - Great Expectations — expectation suite with Data Docs report shared with stakeholders

HOW TO ACT:
  CRITICAL fails (nulls, duplicates, freshness > 2h) → PagerDuty → on-call
  WARNING fails (volume anomaly, validity > 0.5%) → Slack #data-engineering
  All fails → DQ results table → linkable in incident post-mortem
  SLA: define threshold per dimension per table, review monthly"
```

---

## Flash Cards

| Question | Answer |
|---|---|
| What are the 6 DQ dimensions? | Completeness, Uniqueness, Validity, Timeliness, Consistency, Accuracy |
| What does `SQLCheckOperator` do? | Runs a SQL query in Airflow; fails the task if result is falsy |
| What is a dbt `source freshness` check? | Checks that `loaded_at_field` is within a defined time window (warn/error threshold) |
| What is `--store-failures` in dbt test? | Writes failing rows to a BQ table so you can inspect what failed |
| How does Great Expectations generate reports? | `context.build_data_docs()` → HTML site showing all expectations + pass/fail |
| What Prometheus metric type for row counts? | `Gauge` — can go up or down (unlike Counter which only increases) |
| What is a DQ SLA? | Defined threshold per check: e.g., freshness < 1h, uniqueness = 100%, validity ≥ 99.5% |
| What is the volume anomaly detection pattern? | Compare today's row count to 7-day rolling average; alert if deviation > 30% |
| What does Dataplex DQ do that BQ SQL can't? | Native lineage tracking, auto Cloud Monitoring integration, no-code UI spec |
| What is the pipeline gate pattern? | DQ check as a task before downstream tasks — downstream only runs if checks pass |

---

## Practice Questions (6 Minutes Each)

1. **"Your pipeline runs hourly, but your data quality checks only run daily. How do you catch an issue faster?"**
   → Row-count anomaly per hour: if this-hour count < 20% of same-hour last week → alert. Timeliness check (freshness) runs every 15 min via Cloud Monitoring metric on `MAX(transaction_ts)`.

2. **"How do you set meaningful DQ thresholds? What's the process?"**
   → Baseline first: run DQ checks in observe-only mode for 2 weeks to establish natural variation (failure_pct distribution). Then set SLA at 2× standard deviation above normal. Review monthly.

3. **"A developer says 'we can't afford to fail the pipeline on every DQ issue.' How do you respond?"**
   → Separate hard gates (uniqueness = 100%, nulls = 0% on primary keys — truly data-corrupting) from soft alerts (validity 0.5% tolerance — pipeline continues, Slack alert fires). Not all DQ issues should block the pipeline.

4. **"How do you show data quality to non-technical stakeholders?"**
   → Great Expectations Data Docs (HTML report, shareable link). Alternatively: a Looker Studio dashboard reading from `monitoring.dq_results` — green/red status tiles per table, trend charts, SLA compliance %.
