# Technology Depth Recovery Plan
**Addressing the Round A Feedback: "Gaps in Technology Depth"**
**Start date: March 12, 2026**

---

## What the Feedback Actually Means

The Round A interviewer flagged "technology depth" — this almost certainly means one or more of:

1. **GCP-specific knowledge**: You know the AWS equivalents but couldn't fluently describe GCP-native behavior, pricing model, or configuration details
2. **Data engineering depth**: Architecture concepts were correct but lacked technical precision (e.g., couldn't explain exactly-once semantics, watermark strategies, BigQuery partitioning tradeoffs)
3. **System design layering**: Answered with 1–2 layers when a "depth" question expects 5–7 layers (see `missed-questions/q1-black-friday-burst.md`)
4. **Hands-on confidence gap**: Could describe what a service does without having configured/used it recently

**What this is NOT:** A fundamental knowledge problem. The depth is there — it needs to be accessible and confident under interview pressure.

---

## The 3 Depth Gaps Most Likely to Resurface

### Gap 1 — GCP Native Configuration Details
*"I know what it does, but got fuzzy on HOW to configure it correctly."*

**Highest-risk GCP services for Interviews B + D:**

#### BigQuery — Must Be Able to Say:
```sql
-- Table design decisions you can defend:
-- Partition by event_date → filters reduce slot cost on time-bounded queries
-- Cluster by brand_id + customer_key → reduces data scanned on most join patterns
-- Reservation vs On-demand: On-demand = $5/TB; Reservations for predictable workloads
-- BigQuery ML ARIMA_PLUS runs inside BQ — no cluster, no Python runtime, no movement

-- Partitioning syntax:
CREATE TABLE `project.canonical.order`
PARTITION BY DATE(event_date)
CLUSTER BY brand_id, customer_key
OPTIONS (partition_expiration_days = 395)  -- 13-month rolling
AS SELECT ...;
```

**You should be able to answer without hesitation:**
- "Why partition instead of just using WHERE?" → Eliminates slot cost for out-of-range partitions; WHERE on non-partitioned table scans everything
- "When would you NOT cluster?" → Low-cardinality columns with few distinct values don't benefit; adds minor write overhead
- "How does BigQuery billing work?" → On-demand: per TB scanned; Flex Slots: per-slot-hour; BI Engine: memory cache that avoids BQ slot consumption

#### Pub/Sub — Must Be Able to Say:
- **Serverless, no shards** — this IS the key differentiator vs Kinesis. Say it boldly.
- **Delivery guarantee**: At-least-once. Dataflow achieves exactly-once RESULTS through deduplication at the runner level.
- **Retention**: 7 days by default. If Dataflow falls behind, messages replay up to 7 days.
- **Dead-letter topic (DLQ)**: Messages that fail N times → published to DLQ topic for inspection
- **Schema enforcement**: Pub/Sub supports Avro or Protocol Buffer schema — rejects non-conforming messages at source

#### Dataflow / Apache Beam — Must Be Able to Say:
- **Fixed vs sliding windows**: Fixed = non-overlapping (5-min aggregations); Sliding = overlapping (10-min rolling average)
- **Watermark**: The point in event-time below which no more late data is expected. Events later than watermark → dead-letter.
- **Exactly-once semantics**: Beam shuffle-based guarantee. The runner deduplicates by record ID before writing output. NOT Pub/Sub delivery guarantee.
- **Autoscaling**: Workers scale on backlog size. `maxWorkers` caps the ceiling (important for cost control during Black Friday).
- **Unified model**: Same Apache Beam code runs on Dataflow (managed) OR Spark (BYOC) OR Flink. This is the key portability story.

#### Dataplex — Must Be Able to Say:
- **What it is**: Unified data management (governance, quality, lineage, discovery) across GCS + BigQuery
- **Lake → Zone → Asset hierarchy**: Lake = overall domain; Zone = raw zone (GCS) or curated zone (BQ); Asset = individual table/bucket
- **DataScan jobs**: Scheduled data quality rules (NOT_NULL, RANGE, ROW_CONDITION, FRESHNESS) — run nightly, output to BQ `data_quality_scan_results` table
- **Policy tags**: Attached to BQ columns via Dataplex or Data Catalog; IAM binding enforces column-level access (Fine-Grained Reader role)
- **Lineage tracking**: Automatically tracks transformations through Dataflow and BigQuery jobs

#### dbt — Must Be Able to Say:
- **Model types**: View, Table, Incremental, Ephemeral. Incremental = only processes new/updated rows in each run — critical for cost at scale.
- **Tests**: `not_null`, `unique`, `accepted_values`, `relationships` (referential integrity), custom `dbt_utils.expression_is_true`
- **Ref function**: `ref('model_name')` creates dependency graph; dbt runs models in correct order automatically
- **Materializations**: `dbt run` = rebuild models according to materialization config; `dbt test` = run all tests; `dbt build` = run + test in dependency order
- **Schema.yml**: Defines tests and documentation; `meta` properties for policy tags, custom metadata

---

### Gap 2 — System Design Layering (The "Depth" Problem)
*"I answered with the correct architecture but only described 2–3 layers when they expected 5–7."*

**The rule:** Every system design answer must touch at least 5 layers. State the layers before diving into any.

**For any data system question:**
```
Layer 1: Client / Edge (CDN, rate limiting, waiting room)
Layer 2: API / Ingestion layer (schema validation, dead-letter, retry)
Layer 3: Processing / Transformation (streaming vs batch, windowing, joins)
Layer 4: Storage (lake vs warehouse, partition/cluster strategy, retention)
Layer 5: Serving (BI vs ML, latency requirements, access patterns)
Layer 6: Governance (PII, access control, data quality, lineage)
Layer 7: Observability (monitoring, alerting, SLAs, incident response)
```

You don't need to go deep on all 7 — but you need to **name all 7** upfront, then go deep on 2–3 that are most relevant.

**Practice drill:** For any system design question, spend 30 seconds naming all layers before diving into any one. This is the structural move that signals depth.

---

### Gap 3 — Technical Precision Under Follow-Up Probes
*"The architecture was right, but I got fuzzy when follow-ups probed specific mechanisms."*

**The 10 mechanism questions most likely to surface in Interviews B and D:**

| Question | Crisp Answer (memorize the structure, not word-for-word) |
|---|---|
| "How does exactly-once work?" | Pub/Sub = at-least-once; Dataflow runner = deduplication by record ID; BigQuery insertId = idempotent. Result = exactly-once OUTPUT even if multiple deliveries. |
| "What's a watermark?" | The event-time point below which no late data is expected. After watermark passes, window emits and closes. Data after watermark → dead-letter. |
| "How does BigQuery partition pruning work?" | BQ skips entire partition files for queries that filter on the partition column. No partition filter = full table scan. That's why event_date partition matters for time-bounded queries. |
| "How does dbt handle incremental models?" | On first run: full table build. Subsequent runs: only rows passing `is_incremental()` filter are processed and upserted/appended. |
| "How does identity resolution work at scale?" | Deterministic: SHA-256(brand_id + source_id) = canonical_key. Probabilistic: normalized email/phone hash comparison for cross-brand joins. Lives in dbt int model. |
| "What is a dead-letter queue?" | A sink for messages/records that fail processing after N retries. Preserved for investigation and manual replay. Prevents one bad record from blocking the pipeline. |
| "How does Dataplex data quality work?" | DataScan jobs run natively against BQ or GCS assets on schedule. Each rule (NOT_NULL, RANGE, etc.) produces a pass/fail per row; summary written to BQ table; alert if pass rate drops below threshold. |
| "How would you handle a Black Friday streaming spike?" | Pub/Sub absorbs burst (virtually unlimited ingest). Dataflow autoscales workers to maxWorkers ceiling. Pre-scale to 2× expected workers at midnight BF-eve. DLQ handles processing failures. Cloud Monitoring alert on oldest_unacked_message_age. |
| "What's the difference between Dataplex and Data Catalog?" | Data Catalog = metadata/discovery layer. Dataplex = full governance layer built ON TOP of Data Catalog — adds zones, data quality, policy enforcement, lineage. |
| "Why Dataflow over Cloud Composer for streaming?" | Cloud Composer (Airflow) is an orchestrator for batch pipelines. Dataflow is the execution engine. They're not alternatives — Composer orchestrates dbt runs; Dataflow runs streaming jobs. |

---

## The 5-Day Depth Drill

### Day 1 — BigQuery Deep Dive (45 min)
1. Re-read the BigQuery section of `architecture.md` (Layer 2 — your partition/cluster table)
2. Open BigQuery console → navigate to the canonical schema you created for the POC
3. Run: `SELECT * FROM INFORMATION_SCHEMA.PARTITIONS WHERE table_name = 'order'` → confirm partition layout
4. Write out (by hand, no looking): the trade-off rationale for each BigQuery table decision in the architecture
5. Practice saying: "I chose to partition by event_date AND cluster by brand_id + customer_key because..." out loud without notes

### Day 2 — Streaming Deep Dive (45 min)
1. Re-read `poc/pipelines/streaming_pipeline.py` — trace the data flow from source to BigQuery write
2. Identify in the code: where is schema validation? Where is windowing? Where is the dead-letter path?
3. Write out the exactly-once semantics answer in your own words (no looking at notes)
4. Practice answering: "Walk me through what happens when a message arrives 3 minutes after the watermark closes"

### Day 3 — GCP Service Cross-Examination (45 min)
1. Read the `aws-gcp-mapping.md` deep comparison section
2. For each GCP service (Pub/Sub, Dataflow, BigQuery, Dataplex): answer out loud: "When would you choose AWS over GCP for this workload?" (forces you to know both well)
3. Practice the bridging script: "On AWS, I'd use X. On GCP, the equivalent is Y. The key difference is Z."

### Day 4 — System Design Layering Practice (45 min)
1. Read `missed-questions/q1-black-friday-burst.md` one more time
2. Answer the Black Friday question OUT LOUD with a whiteboard/paper — draw all 7 layers first, then go deep on 2
3. Time it: target 8 minutes. Name a trade-off at each layer.
4. Then answer this new question out loud: "Design the data pipeline for a healthcare company with HIPAA compliance requirements." Same 7-layer structure.

### Day 5 — Follow-Up Probe Gauntlet (45 min)
1. Go through the 10 mechanism questions above
2. For each: answer out loud WITHOUT looking at the answer — then compare to the crisp answer
3. Flag any where your answer was different or vague — those are your residual gaps
4. Focus the last 15 minutes on those flagged ones

---

## In-Interview Depth Signals

These are phrases that signal depth to the interviewer — use them naturally:

| Signal | Example |
|---|---|
| Naming the trade-off explicitly | "I chose on-demand pricing over flex slots for Phase 1 because data volumes are uncertain during migration." |
| Naming when you'd choose differently | "If the customer has existing Snowflake contracts and migration cost > benefit, I'd adapt this to use Snowflake as the warehouse." |
| Referencing exact configuration | "The table is partitioned by event_date, clustered by brand_id and customer_key — let me explain why that specific combination..." |
| Showing failure mode awareness | "The edge case here is late data — events that arrive after the 2-minute watermark go to the dead-letter table for async reprocessing." |
| Citing the ordering of concerns | "I'd address identity resolution first — everything downstream depends on getting the customer_key right." |
| Using GCP-native terminology correctly | "Dataplex auto-discovery scans new GCS objects and registers them in Data Catalog — I didn't have to build a custom metadata pipeline." |

---

## The Signal for "Good Enough" Depth

You're at the right depth level when you can:
1. Answer a follow-up probe on any layer of your architecture without hesitation
2. Name what changes if a specific constraint changes (e.g., "if it needs sub-second latency instead of 5-minute windows, here's what I'd change")
3. State a configuration detail (partition key, window size, watermark, retention period) and explain why you chose that specific value
4. Pivot fluently between AWS and GCP for equivalent services with one key differentiation named

If you can do all four for every layer in your Presentation architecture → you're good.
