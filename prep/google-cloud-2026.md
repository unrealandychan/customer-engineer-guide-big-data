# Google Cloud 2025–2026: What's New That Matters for Your Interviews

**Source:** Google Cloud Next '25 (April 2025) + ongoing releases
**Last updated:** March 2026
**Priority:** HIGH — William (HM) will be impressed if you name these unprompted. Gene will recognize current knowledge.

---

## The Big Strategic Frame: BigQuery is No Longer Just a Warehouse

Google officially repositioned BigQuery at Cloud Next '25 as an **"autonomous data-to-AI platform"** — not a data warehouse. This matters for your presentation because:

- The 1-year AI activation mandate the CIO has is now more credible to deliver: BigQuery can be the **single platform** for ingestion, storage, SQL analytics, ML training, AI inference, governance, AND natural language querying
- The "AI activation for business analysts" story works out of the box — Gemini in BigQuery means analysts, not just data engineers, can query data in natural language  
- Saying "BigQuery" in your presentation now means the same as saying "the whole data + AI platform" — use that intentionally

---

## What to Know Cold (by Interview Round)

### 1. Gemini in BigQuery (GA — General Availability)

**What it is:** AI assistance embedded directly into the BigQuery console and APIs.

**Key capabilities you can name:**
- **Gemini code assist:** Natural language → SQL or Python. Usage grew **350%** in 9 months with >60% code acceptance rate. This is not experimental — it's production.
- **Data canvas:** Natural language → multi-step SQL exploration with visual interface. Great for business analysts who can't write SQL.
- **Gemini-assisted data preparation (GA):** Low-code pipeline builder with intelligent suggestions for data enrichment and quality fixes.
- **Automated metadata generation (preview):** Gemini generates column/table descriptions automatically — huge for governance at scale.
- **SQL translation assistance (GA):** AI-powered SQL migration tool. Critical for migrating Brand B's Oracle SQL or Brand A's Redshift DDL to BigQuery-compatible syntax.

**How to use it in your interview:**
> "One of the key enablers for the 12-month AI activation mandate is Gemini in BigQuery. Brand analysts at each brand can self-serve using natural language queries from day one after migration — they don't need to wait for a data engineering team to write SQL for them. That's how you scale AI activation across 3 brands without tripling the data team."

---

### 2. BigQuery Continuous Queries (GA — Major for Streaming)

**What it is:** SQL-based real-time stream processing — you write standard SQL that runs continuously against a BigQuery table as new rows arrive. Launched GA at Cloud Next '25.

**Why this matters for your presentation:**
- This is a **simpler alternative to Dataflow** for straight-through stream processing that doesn't need complex windowing
- For POS transaction streaming (no complex joins or stateful aggregations needed), Continuous Queries may be the right answer
- Supports slot autoscaling and Cloud Monitoring out of the box

**The nuance — know when to use each:**
| Use Case | Right Tool |
|---|---|
| Simple filter, transform, write (POS events to analytics table) | **BigQuery Continuous Queries** |
| Complex stateful streaming (sessionization, 2-hour windows, late data, cross-stream joins) | **Dataflow / Apache Beam** |
| Batch orchestration (nightly dbt, scheduled loads) | **Cloud Composer (Airflow) + dbt** |

**How to use it in your interview:**
> "For the POS streaming use case — retail orders flowing in real-time — I'd evaluate BigQuery Continuous Queries as the simpler option before defaulting to Dataflow. Continuous Queries can filter, transform, and write POS events to the canonical BigQuery table in SQL, with autoscaling. I'd reserve Dataflow for the more complex streaming that requires stateful processing across a 2+ minute watermark."

**If William probes:** "Why not just use Continuous Queries for everything?"
> "Continuous Queries doesn't support stateful windowing across events — for example, a sessionization that needs to join a customer's active session across 20 events over 30 minutes requires Dataflow's stateful processing model. But for the bulk of the POS streaming in this scenario, Continuous Queries is a cleaner architecture."

---

### 3. TimesFM — Google's Pretrained Time-Series Model (Preview)

**What it is:** Google Research's pretrained foundation model for time-series forecasting. Available directly in BigQuery ML.

**Why this matters:**
- For the demand forecasting use case in your presentation, **TimesFM outperforms ARIMA_PLUS** because:
  1. TimesFM is a pretrained foundation model — it learned patterns from a massive time-series corpus
  2. No need to tune seasonal parameters — it handles heterogeneous series (different brands with different seasonalities) natively
  3. Available directly in BigQuery ML with SQL — same zero-infrastructure advantage as ARIMA_PLUS

**How to reference it in your presentation:**
> "For demand forecasting, I've architected this with BigQuery ML. In Phase 1, we'd start with ARIMA_PLUS — it's stable, GA, and the data team can explain it to the business. In Phase 2, I'd migrate the forecasting to BigQuery ML's TimesFM model — Google Research's pretrained time-series foundation model. It handles cross-brand heterogeneous seasonalities (each brand has different holiday patterns, regional patterns) without per-series parameter tuning. Better accuracy, simpler maintenance."

**If probed:** "What's the difference vs ARIMA_PLUS?"
> "ARIMA_PLUS trains a separate model per time series — 10,000 SKUs × 3 brands = 30,000 individual ARIMA models trained and maintained. TimesFM is a single pretrained foundation model that does zero-shot forecasting on new series without retraining. It's not always better for every series, but at scale it dramatically reduces maintenance overhead."

---

### 4. BigQuery Universal Catalog (GA — Governance Rebranding)

**What it is:** Google unified and rebranded the governance layer at Cloud Next '25. Dataplex Catalog is now **BigQuery universal catalog** — your single metadata, lineage, governance, and discovery system across BQ and GCS.

**The governance stack you should now describe:**
```
BigQuery universal catalog
├── Data catalog (metadata, discovery, search)
├── Business glossary (shared terminology — new GA feature)
├── Policy tags (column-level security)
├── Data lineage (auto-tracked through Dataflow + BQ jobs)
├── DataScan jobs → data quality rules
└── BigQuery metastore (cross-engine Iceberg catalog — Spark, Flink, BQ unified)
```

**New capabilities to reference:**
- **Business glossary (GA):** Define company-wide data terms (e.g., "loyal customer" = 3+ purchases in 90 days), attach them to columns, enforce shared understanding across brands. This is critical for the 3-brand merger where Brand A, B, and C have different definitions of "customer" and "revenue."
- **Automated metadata generation:** Gemini generates column descriptions automatically at scale — important when migrating hundreds of tables from 3 brands.
- **BigQuery metastore (GA):** Unified Iceberg catalog so Spark (Dataproc), Flink, and BigQuery all see the same metadata. Relevant if any brand's existing team runs Spark jobs.

---

### 5. BigQuery Vector Search (GA — for AI Recommendations)

**What it is:** Native vector search inside BigQuery — generate, store, and search embeddings without moving data to a separate vector database.

**Why this matters for your architecture:**
> "The product recommendation engine in Phase 2 runs on top of BigQuery vector search. Customer and product embeddings are generated using Vertex AI Embeddings and stored directly in BigQuery. A SQL query with `VECTOR_SEARCH()` finds the nearest-neighbor product embeddings for each customer — no separate vector database required (no Pinecone, no Weaviate). This keeps the entire recommendation stack in BigQuery, reducing operational complexity and eliminating data movement latency."

**New index type:** ScaNN-based index (GA) — faster, more cost-efficient than flat vector search for large embedding sets. Mention this if probed.

---

### 6. BigQuery Iceberg Tables (Preview)

**What it is:** Native Iceberg table format in BigQuery — open lakehouse capabilities with BigQuery's performance and governance.

**When to use it in your answer:**
- If Brand A or B has an existing Databricks or Spark-based lakehouse, Iceberg tables let you access their data from BigQuery without full migration
- Frame this as the **open lakehouse on-ramp** for brands that can't do a big-bang migration

> "If Brand C's data team is already running Spark on Databricks or Dataproc, we don't need to force a hard cutover. BigQuery Iceberg tables let us register their existing Iceberg data directly in BigQuery — same catalog, same SQL interface, same governance. They migrate at their own pace."

---

### 7. Managed BigQuery Disaster Recovery (GA)

**What it is:** Built-in, managed DR for BigQuery — automatic failover, continuous near-real-time replication to a secondary region.

**For the presentation:** Upgrades your DR story significantly from the current file which uses manual snapshots.

> "For the canonical tier, BigQuery's managed DR replicates the warehouse automatically to a secondary region with sub-minute RPO. No manual snapshot scheduling required. For a board-mandated data platform, that's table stakes — I want to say it's built-in, not bolted-on."

---

### 8. Google Agentspace + Vertex AI Agents (for AI Activation Framing)

**What it is:** Google's enterprise AI agent platform — pre-built agents for enterprise workflows, powered by Gemini, integrated with Google Workspace and BigQuery.

**How to frame "AI activation" using agents:**
> "When the CIO says 'AI activation in 12 months,' one of the most accessible use cases isn't custom ML — it's natural language business intelligence through Vertex AI Agents. An agent grounded in the BigQuery canonical layer can answer business questions like 'Which brand had the highest margin SKU last week in the Northeast?' without any SQL or dashboard navigation. You can give CPG partners or brand GMs access to a chat interface over your data — and THAT is data monetization in its simplest, fastest-to-deploy form."

---

## Quick GCP Competitive Positioning (for probes from Gene or William)

### BigQuery vs Snowflake (Updated)
| Factor | BigQuery | Snowflake |
|---|---|---|
| Compute model | Serverless + slots | Virtual Warehouse (cluster) |
| Streaming | Native continuous queries + Dataflow | Snowpipe Streaming (add-on) |
| ML/AI | Gemini in BQ, Vertex AI, TimesFM — native SQL | Cortex + partner integrations |
| Governance | Universal catalog (native, GA) | Polaris catalog (newer, open source) |
| Open lakehouse | Apache Iceberg (BQ native + metastore) | Apache Iceberg (Polaris) |
| Multimodal | ObjectRef data type, unstructured-native | More structured-data focused |

**Closing argument for this scenario:**
> "For a migration where data volumes are unknown and will grow as 3 brands merge, BigQuery's serverless model means we never have to size a warehouse. With Snowflake, we're picking a Virtual Warehouse size before we know peak load. In a migration context, that's a significant operational risk."

### BigQuery vs Databricks
- Databricks = Spark-native, best for complex ML pipelines and large-scale data transformations
- BigQuery = SQL-native, best for analytic workloads, BI, and now unified AI platform
- **Coexistence story:** "If the customer has Databricks investment, BQ Iceberg tables let them query the same data from both engines. We're not asking them to abandon existing investment."

### Cloud Composer (Airflow) vs Databricks Workflows vs AWS MWAA
> "Cloud Composer is Google's managed Airflow. For this architecture, it orchestrates dbt runs and triggers Dataflow batch jobs. It's not the streaming engine — it's the orchestration layer. Customers coming from Databricks Workflows or MWAA will find the concepts identical; only the managed layer differs."

---

## The Product Update You Should PROACTIVELY Mention

In the presentation Q&A, if there's a natural opening, say:

> "One thing worth noting for the AI activation timeline: Google just repositioned BigQuery as an autonomous data-to-AI platform, with Gemini natively embedded, continuous SQL queries for streaming, and TimesFM for time-series forecasting. What this means for your 12-month mandate is that the AI activation layer doesn't require a separate infrastructure build. The moment the data is in BigQuery canonical, your analysts can query it in natural language, and your data scientists can train ML models in SQL. That changes the timeline math significantly."

This signals you're current, you've read beyond the product docs, and you're thinking about the customer's problem — not just the architecture.
