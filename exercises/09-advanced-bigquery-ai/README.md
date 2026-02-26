# 🏋️ Exercise Category 9: Advanced BigQuery AI & 2026 Topics

> **New in this category:** Based on Google Cloud blog (Jan–Feb 2026), official BigQuery docs,
> and the Google Research papers HR asked you to study.

## What You'll Practice

| Exercise | Topic | Key Concept |
|----------|-------|-------------|
| `ex01_bigquery_ai_2026.py` | AI Functions | `AI.GENERATE`, `AI.EMBED`, `AI.SIMILARITY`, `AI.SEARCH`, Autonomous Embeddings |
| `ex02_dremel_concepts.py` | Dremel Deep Dive | Columnar storage, slots, partition pruning, execution plans |

---

## Prerequisites

```bash
pip install google-cloud-bigquery google-cloud-aiplatform

# Set your GCP project
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Authenticate
gcloud auth application-default login

# Grant yourself Vertex AI User role (for AI functions with EUC)
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="user:you@company.com" \
  --role="roles/aiplatform.user"
```

---

## Exercise 1: BigQuery AI Functions (2026)

**File:** `ex01_bigquery_ai_2026.py`

### What's Covered

#### 1a. `AI.GENERATE` — Multi-Task Analysis (GA)
```sql
SELECT AI.GENERATE(
  'Analyze: ' || article_text,
  model => 'gemini-2.0-flash',
  output_schema => STRUCT(
    topic STRING,
    sentiment STRING,
    summary STRING
  )
) FROM my_table;
```
One SQL call → entity extraction + sentiment + translation + summarization simultaneously.

#### 1b. Autonomous Embedding Columns (Preview, Feb 2026)
```sql
-- BigQuery manages embeddings automatically — no pipeline needed
ALTER TABLE my_products
ADD COLUMN desc_embedding FLOAT64[]
  OPTIONS (embedding_column = TRUE, source_column = 'description');
```
When source data changes → BigQuery re-generates embeddings in the background.

#### 1c. `AI.SIMILARITY` — Semantic Duplicate Detection
```sql
SELECT AI.SIMILARITY(
  'How do I cancel my subscription?',
  'What is the process to end my account?'
);
-- Returns: ~0.92 (semantically very similar)
```

#### 1d. Global Queries (Preview, Feb 18 2026)
```sql
SET @@location = 'US';
SELECT * FROM `eu_dataset.table` JOIN `asia_dataset.table` USING (id);
-- Queries data in EU + APAC from a single US-executed SQL statement
```

#### 1e. Continuous Queries (Enterprise Edition)
```sql
-- Streams data as it arrives — no Dataflow cluster needed
EXPORT DATA OPTIONS(uri='pubsub://...', format='JSON')
AS SELECT * FROM APPENDS(TABLE transactions, NULL, NULL) WHERE amount > 10000;
```

### Run It
```bash
python ex01_bigquery_ai_2026.py        # shows all exercises
python ex01_bigquery_ai_2026.py 1      # AI.GENERATE multi-task
python ex01_bigquery_ai_2026.py 2      # Autonomous embeddings + semantic search
python ex01_bigquery_ai_2026.py 3      # AI.SIMILARITY duplicate detection
python ex01_bigquery_ai_2026.py 4      # Global queries demo
python ex01_bigquery_ai_2026.py 5      # Continuous queries
python ex01_bigquery_ai_2026.py 6      # Editions decision tree
```

---

## Exercise 2: Dremel Concepts

**File:** `ex02_dremel_concepts.py`

### Why This Matters

HR said to read the Google whitepapers. Dremel (2010) is BigQuery's engine.
Understanding Dremel lets you answer the deep technical questions:
- *"Why does BigQuery charge by bytes scanned?"* → Dremel's columnar I/O is the bottleneck
- *"Why is SELECT * expensive?"* → Reads every column file from Colossus
- *"What is a slot?"* → A Dremel leaf/mixer worker node
- *"Why is my query slow?"* → Read the execution plan (multi-level tree)

### What's Covered

#### 2a. Columnar Storage Impact
```bash
# Dry-run: compare bytes scanned for SELECT * vs SELECT id
python ex02_dremel_concepts.py 1
```
Expected: SELECT id scans ~50x fewer bytes than SELECT * on the same table.

#### 2b. Nested Records (Repetition/Definition Levels)
```sql
-- Dremel encodes nested arrays using r (repetition) and d (definition) levels
SELECT order_id, item.sku, item.quantity
FROM orders, UNNEST(line_items) AS item;
```
Understanding this is how you answer: *"How does BigQuery handle ARRAY and STRUCT columns?"*

#### 2c. Slot Usage Analysis via INFORMATION_SCHEMA
```sql
-- Find your most expensive queries in the last 7 days
SELECT job_id, total_slot_ms, total_bytes_processed
FROM INFORMATION_SCHEMA.JOBS
ORDER BY total_slot_ms DESC LIMIT 20;
```

#### 2d. Partition Pruning
```sql
-- BAD:  Full scan (no partition filter) → reads 90 days of Colossus files
SELECT * FROM events WHERE event_type = 'purchase';

-- GOOD: Partition filter → reads only 7 partition directories
SELECT * FROM events
WHERE event_time >= '2025-02-19' AND event_time < '2025-02-26'
  AND event_type = 'purchase';
```

#### 2e. Execution Plan
```bash
python ex02_dremel_concepts.py 5
# Shows: how to read BigQuery's multi-stage execution plan
# Maps to: Dremel's leaf → mixer → root server architecture
```

### Run It
```bash
python ex02_dremel_concepts.py        # all exercises
python ex02_dremel_concepts.py 1      # columnar storage impact
python ex02_dremel_concepts.py 2      # nested records
python ex02_dremel_concepts.py 3      # slot analysis
python ex02_dremel_concepts.py 4      # partition pruning
python ex02_dremel_concepts.py 5      # execution plan
```

---

## Key Concepts Summary — For the Interview

### Dremel in 30 Seconds
> "BigQuery's engine is Dremel. It stores data as separate column files — including nested arrays — using repetition and definition levels. A query touching 3 of 200 columns reads 1.5% of the stored data. Thousands of leaf workers read shards in parallel, aggregating up through mixer nodes to a root server. That's how you query a trillion rows in seconds."

### AI Functions Pitch (30 Seconds)
> "BigQuery now has `AI.GENERATE` in GA — one SQL call does entity extraction, sentiment analysis, translation, and summarization simultaneously. `AI.EMBED` and `AI.SIMILARITY` let you do semantic search. Autonomous embeddings keep vector columns in sync automatically — no pipeline. This makes BigQuery an AI-native analytics platform, not just a data warehouse."

### Global Queries Pitch (30 Seconds)
> "Global queries — Preview since February 2026 — let you join data stored in EU, APAC, and US regions in a single SQL statement. No ETL pipeline to centralize data. BigQuery decomposes the query, runs sub-queries in each region, moves only the aggregated results, and assembles the final answer. Governance controls prevent data crossing VPC boundaries."

---

## Further Reading

| Topic | Link |
|-------|------|
| AI.GENERATE docs | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate |
| Autonomous embeddings | https://cloud.google.com/bigquery/docs/autonomous-embedding-generation |
| Global queries | https://cloud.google.com/bigquery/docs/global-queries |
| Continuous queries | https://cloud.google.com/bigquery/docs/continuous-queries |
| Dremel paper (2010) | https://research.google/pubs/pub36632/ |
| Dremel 2.0 paper (2020) | https://research.google/pubs/pub49489/ |
| BigQuery Editions | https://cloud.google.com/bigquery/docs/editions-intro |
| INFORMATION_SCHEMA | https://cloud.google.com/bigquery/docs/information-schema-jobs |
