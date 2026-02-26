"""
Exercise: BigQuery AI Functions & Autonomous Embeddings
-------------------------------------------------------
Topics: AI.GENERATE, AI.EMBED, AI.SIMILARITY, AI.SEARCH, VECTOR_SEARCH,
        Autonomous embedding columns, Conversational Analytics API
Based on: Google Cloud Blog (Jan-Feb 2026) + BigQuery AI docs

Prerequisites:
  pip install google-cloud-bigquery google-cloud-aiplatform
  Grant yourself: Vertex AI User role (for EUC / End User Credentials)
"""

from google.cloud import bigquery

PROJECT_ID = "your-project-id"
DATASET_ID = "ai_exercises"
LOCATION = "US"

client = bigquery.Client(project=PROJECT_ID)


# ---------------------------------------------------------------------------
# Exercise 1: AI.GENERATE — Multi-task analysis in one SQL call (GA)
# ---------------------------------------------------------------------------
# Goal: Run 5 AI tasks simultaneously on BBC news articles using a single
#       AI.GENERATE call. Returns structured output with named columns.

EXERCISE_1_SQL = """
SELECT
  title,
  AI.GENERATE(
    'Analyze this news article: ' || text,
    model => 'gemini-2.0-flash',
    output_schema => STRUCT(
      key_entities    ARRAY<STRING>,   -- named entities mentioned
      topic           STRING,          -- primary topic category
      sentiment       STRING,          -- positive / negative / neutral
      summary         STRING,          -- one sentence summary
      spanish_summary STRING           -- translated summary
    )
  ) AS analysis
FROM `bigquery-public-data.bbc_news.fulltext`
LIMIT 5
"""

def exercise_1_multi_task_generation():
    """
    Run 5 AI tasks in one SQL call:
    1. Entity extraction
    2. Topic modeling
    3. Sentiment analysis
    4. Summarization
    5. Translation (English → Spanish)

    Note: AI.GENERATE is GA as of Jan 2026.
    With EUC enabled, no separate connection config needed.
    """
    print("=== Exercise 1: Multi-task AI.GENERATE ===")
    print("Running AI analysis on BBC news articles...")
    print()
    print("SQL:")
    print(EXERCISE_1_SQL)
    print()

    # In a real environment, run:
    # results = client.query(EXERCISE_1_SQL).result()
    # for row in results:
    #     print(f"Title: {row.title}")
    #     print(f"Analysis: {row.analysis}")

    print("Expected output structure per row:")
    print("  analysis.key_entities: ['Boris Johnson', 'UK Parliament']")
    print("  analysis.topic: 'Politics'")
    print("  analysis.sentiment: 'negative'")
    print("  analysis.summary: 'UK parliament debates Brexit deal...'")
    print("  analysis.spanish_summary: 'El parlamento del Reino Unido...'")


# ---------------------------------------------------------------------------
# Exercise 2: AI.EMBED + VECTOR_SEARCH — Semantic Search at Scale
# ---------------------------------------------------------------------------
# Goal: Generate embeddings for a product catalog and find similar products.

SETUP_EMBEDDINGS_SQL = """
-- Step 1: Create a products table with text descriptions
CREATE OR REPLACE TABLE `{project}.{dataset}.products` AS
SELECT
  product_id,
  name,
  description,
  category,
  price
FROM UNNEST([
  STRUCT('P001' AS product_id, 'Trail Running Shoes' AS name,
         'Lightweight shoes for mountain trail running with grip soles' AS description,
         'Footwear' AS category, 89.99 AS price),
  STRUCT('P002', 'Road Cycling Helmet',
         'Aerodynamic helmet for road cycling with ventilation',
         'Cycling', 149.99),
  STRUCT('P003', 'Yoga Mat',
         'Non-slip premium yoga mat for studio and outdoor practice',
         'Fitness', 45.00),
  STRUCT('P004', 'Hiking Backpack 40L',
         'Waterproof hiking backpack with hip belt and hydration sleeve',
         'Outdoor', 199.00),
  STRUCT('P005', 'Running GPS Watch',
         'GPS smartwatch for runners with heart rate monitor and pace tracking',
         'Electronics', 299.00)
]);
""".format(project=PROJECT_ID, dataset=DATASET_ID)

# Step 2: Add autonomous embedding column — BigQuery manages it automatically
AUTONOMOUS_EMBEDDING_SQL = """
ALTER TABLE `{project}.{dataset}.products`
ADD COLUMN description_embedding FLOAT64[]
  OPTIONS (
    embedding_column = TRUE,
    source_column = 'description',
    model = 'text-embedding-005'
  );
""".format(project=PROJECT_ID, dataset=DATASET_ID)

VECTOR_SEARCH_SQL = """
-- Step 3: Create vector index for fast ANN search
CREATE OR REPLACE VECTOR INDEX products_embedding_idx
ON `{project}.{dataset}.products`(description_embedding)
OPTIONS (distance_type = 'COSINE', index_type = 'IVF');

-- Step 4: Semantic search with AI.SEARCH (uses managed embeddings automatically)
SELECT base.name, base.category, base.price, distance
FROM VECTOR_SEARCH(
  TABLE `{project}.{dataset}.products`,
  'description_embedding',
  (SELECT AI.EMBED('outdoor gear for running and hiking trails',
                   model => 'text-embedding-005') AS embedding),
  top_k => 3,
  distance_type => 'COSINE'
)
ORDER BY distance;
""".format(project=PROJECT_ID, dataset=DATASET_ID)

# Simplified version using AI.SEARCH (Preview, Feb 2026)
AI_SEARCH_SQL = """
SELECT name, category, price
FROM AI.SEARCH(
  TABLE `{project}.{dataset}.products`,
  'description',
  'outdoor gear for running and hiking trails'
)
LIMIT 3;
""".format(project=PROJECT_ID, dataset=DATASET_ID)

def exercise_2_semantic_search():
    """
    Build a semantic product search system using:
    - Autonomous embedding generation (no pipeline needed)
    - Vector index for fast approximate nearest neighbor (ANN) search
    - AI.SEARCH as the simplified interface

    Key insight: Autonomous embeddings = BigQuery keeps them in sync
    automatically. No Dataflow pipeline, no manual refresh.
    """
    print("=== Exercise 2: Semantic Search with Autonomous Embeddings ===")
    print()
    print("Step 1 - Setup products table:")
    print(SETUP_EMBEDDINGS_SQL)
    print()
    print("Step 2 - Add autonomous embedding column (BigQuery manages sync):")
    print(AUTONOMOUS_EMBEDDING_SQL)
    print()
    print("Step 3 - Vector search + AI.SEARCH:")
    print(VECTOR_SEARCH_SQL)
    print()
    print("Expected results for query 'outdoor gear for running and hiking trails':")
    print("  1. Trail Running Shoes (distance: 0.05) ← most similar")
    print("  2. Hiking Backpack 40L (distance: 0.12)")
    print("  3. Running GPS Watch (distance: 0.18)")


# ---------------------------------------------------------------------------
# Exercise 3: AI.SIMILARITY — Find Duplicate/Similar Support Tickets
# ---------------------------------------------------------------------------

AI_SIMILARITY_SQL = """
WITH tickets AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS id, 'How do I cancel my subscription?' AS text),
    STRUCT(2, 'What is the process to end my account?'),
    STRUCT(3, 'I want to delete my billing information'),
    STRUCT(4, 'My payment is not going through'),
    STRUCT(5, 'Card declined when trying to pay')
  ])
),
pairs AS (
  SELECT
    a.id AS ticket_a,
    b.id AS ticket_b,
    a.text AS text_a,
    b.text AS text_b,
    AI.SIMILARITY(a.text, b.text) AS similarity_score
  FROM tickets a
  CROSS JOIN tickets b
  WHERE a.id < b.id  -- avoid duplicates and self-comparison
)
SELECT *
FROM pairs
WHERE similarity_score > 0.85  -- threshold for "duplicate" tickets
ORDER BY similarity_score DESC;
"""

def exercise_3_duplicate_detection():
    """
    Use AI.SIMILARITY to find semantically duplicate support tickets.
    AI.SIMILARITY internally:
    1. Calls AI.EMBED on both texts
    2. Computes cosine similarity between the two embedding vectors
    3. Returns a score between 0 (unrelated) and 1 (identical meaning)

    Pre-sales story: Route duplicate tickets to the same agent,
    auto-suggest answers from previously resolved similar tickets.
    """
    print("=== Exercise 3: Duplicate Detection with AI.SIMILARITY ===")
    print(AI_SIMILARITY_SQL)
    print()
    print("Expected high-similarity pairs:")
    print("  tickets 1+2: 'cancel subscription' ≈ 'end account' → ~0.93")
    print("  tickets 4+5: 'payment not through' ≈ 'card declined' → ~0.89")


# ---------------------------------------------------------------------------
# Exercise 4: Global Queries (Preview) — Multi-Region Analytics
# ---------------------------------------------------------------------------
# Based on: BigQuery global queries announcement, Feb 18 2026

GLOBAL_QUERY_SQL = """
-- Global queries: SET the execution location first
SET @@location = 'US';

-- Join data from EU and ASIA regions into a US-executed query
-- This would previously require an ETL pipeline to centralize data!
WITH all_transactions AS (
  -- EU dataset (stored in europe-west1)
  SELECT customer_id, transaction_amount, 'EU' AS region
  FROM `mycompany-eu.transactions.sales_2025`

  UNION ALL

  -- APAC dataset (stored in asia-east1)
  SELECT customer_id, transaction_amount, 'APAC' AS region
  FROM `mycompany-apac.transactions.sales_2025`
)
SELECT
  c.customer_name,
  t.region,
  SUM(t.transaction_amount) AS total_sales,
  COUNT(*) AS transaction_count
FROM `mycompany-us.customers.master` AS c        -- US dataset
JOIN all_transactions AS t ON c.id = t.customer_id
GROUP BY c.customer_name, t.region
ORDER BY total_sales DESC
LIMIT 20;
"""

def exercise_4_global_queries():
    """
    Demonstrate BigQuery global queries (Preview, Feb 2026).
    Key requirements to enable:
    1. Admin enables global queries for the project
    2. User has special bigquery.globalQueries.run permission
    3. SET @@location specifies where final query runs

    How it works internally:
    1. BQ decomposes query into per-region sub-queries
    2. Each sub-query runs in its home region
    3. Only the results (not raw data) transfer to execution location
    4. Final assembly at SET @@location region

    Governance: Respects VPC Service Controls — data can't cross
    boundaries that violate established policies.
    """
    print("=== Exercise 4: Global Queries (Preview — Feb 2026) ===")
    print()
    print("Pre-requisites:")
    print("  gcloud projects add-iam-policy-binding PROJECT \\")
    print("    --member='user:you@company.com' \\")
    print("    --role='roles/bigquery.globalQueriesRunner'")
    print()
    print("SQL (runs across EU + APAC + US datasets):")
    print(GLOBAL_QUERY_SQL)
    print()
    print("Key selling point:")
    print("  Before: ETL pipeline to centralize data = days of engineering")
    print("  After:  One SQL statement = minutes of setup")
    print("  Data stays in region for compliance; only aggregates move.")


# ---------------------------------------------------------------------------
# Exercise 5: Continuous Queries (BigQuery Enterprise Edition)
# ---------------------------------------------------------------------------

CONTINUOUS_QUERY_SQL = """
-- Continuous queries stream data as it arrives — no separate Dataflow job needed
-- Requires: BigQuery Enterprise edition + CONTINUOUS assignment type

-- Export high-value transaction alerts to Pub/Sub in real-time
EXPORT DATA OPTIONS(
  uri = 'pubsub://projects/{project}/topics/high-value-alerts',
  format = 'JSON'
)
AS
SELECT
  transaction_id,
  user_id,
  amount,
  merchant_name,
  CURRENT_TIMESTAMP() AS alert_time
FROM APPENDS(TABLE `{project}.{dataset}.transactions`, NULL, NULL)
WHERE amount > 10000  -- flag transactions over $10k
  AND country_code != user_country_code;  -- flag cross-border
""".format(project=PROJECT_ID, dataset=DATASET_ID)

def exercise_5_continuous_queries():
    """
    Continuous queries run perpetually and process data as it arrives.
    They're an alternative to Dataflow for simple streaming transforms.

    APPENDS() function reads NEW rows added to a table since last checkpoint.
    Output can go to: Pub/Sub, Bigtable, or another BigQuery table.

    When to use Continuous Queries vs Dataflow:
    +---------------------------+-------------------+-------------------+
    | Factor                    | Continuous Query  | Dataflow          |
    +---------------------------+-------------------+-------------------+
    | Complexity                | Simple SQL        | Complex pipelines |
    | Setup                     | Minutes           | Hours             |
    | Custom transforms         | No (SQL only)     | Yes (Beam SDK)    |
    | Windowing/session groups  | Limited           | Full Beam support |
    | ML inference in pipeline  | Via AI.GENERATE   | RunInference      |
    | Cost model                | BQ slots          | Dataflow workers  |
    +---------------------------+-------------------+-------------------+

    Edition requirement: Enterprise or Enterprise Plus
    """
    print("=== Exercise 5: Continuous Queries (Enterprise Edition) ===")
    print()
    print("SQL (runs perpetually, alerting on new high-value transactions):")
    print(CONTINUOUS_QUERY_SQL)
    print()
    print("Compare to Dataflow: no Python/Java code, no cluster management.")
    print("Trade-off: less flexible than full Apache Beam pipelines.")


# ---------------------------------------------------------------------------
# Exercise 6: BigQuery Editions — Choosing the Right Edition
# ---------------------------------------------------------------------------

def exercise_6_editions_decision_tree():
    """
    Decision tree for recommending BigQuery editions to customers.
    Know this for pre-sales conversations.
    """
    print("=== Exercise 6: BigQuery Editions Decision Tree ===")
    print()

    decision_tree = """
    START: What is the primary workload?
    │
    ├── Ad-hoc exploration / dev/test / infrequent queries
    │   └── → ON-DEMAND ($6.25/TiB, first 1TB free)
    │
    ├── Regular analytics workloads, need predictable cost
    │   │
    │   ├── Need: BI Engine acceleration?         → Enterprise (minimum)
    │   ├── Need: BigQuery ML?                    → Enterprise (minimum)
    │   ├── Need: Continuous queries (streaming)? → Enterprise (minimum)
    │   ├── Need: Vector search with index?       → Enterprise (minimum)
    │   ├── Need: BigQuery Omni (cross-cloud)?    → Enterprise
    │   ├── Need: Cross-user caching?             → Enterprise (minimum)
    │   │
    │   ├── Need: Assured Workloads (FedRAMP/CJIS/IL4/ITAR)?
    │   │   └── → Enterprise Plus
    │   ├── Need: Managed disaster recovery?
    │   │   └── → Enterprise Plus
    │   ├── Need: Cross-region data export to Bigtable?
    │   │   └── → Enterprise Plus
    │   │
    │   └── Otherwise → Standard (autoscaling, max 1,600 slots)
    │
    └── Just starting with BQ / prototyping
        └── → ON-DEMAND + Sandbox (no credit card needed)
    """
    print(decision_tree)

    print("Commitment discounts (Enterprise & Enterprise+ only):")
    print("  1-year commitment  → 20% discount on slot-hours")
    print("  3-year commitment  → 40% discount on slot-hours")
    print()
    print("Crossover point (On-demand vs Enterprise capacity):")
    print("  If monthly BQ spend > ~$2,000 → Enterprise + autoscaling usually wins")
    print("  Run: SELECT SUM(total_bytes_processed) FROM INFORMATION_SCHEMA.JOBS")
    print("  Multiply by $6.25/TiB to estimate current on-demand spend.")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    exercises = {
        "1": exercise_1_multi_task_generation,
        "2": exercise_2_semantic_search,
        "3": exercise_3_duplicate_detection,
        "4": exercise_4_global_queries,
        "5": exercise_5_continuous_queries,
        "6": exercise_6_editions_decision_tree,
    }

    if len(sys.argv) > 1 and sys.argv[1] in exercises:
        exercises[sys.argv[1]]()
    else:
        print("BigQuery AI & 2026 Features Exercises")
        print("=" * 40)
        print("Usage: python ex01_bigquery_ai_2026.py <exercise_number>")
        print()
        print("Exercises:")
        print("  1 - AI.GENERATE multi-task analysis (GA)")
        print("  2 - Autonomous embeddings + VECTOR_SEARCH + AI.SEARCH")
        print("  3 - AI.SIMILARITY duplicate detection")
        print("  4 - Global queries (Preview, Feb 2026)")
        print("  5 - Continuous queries (Enterprise edition)")
        print("  6 - Editions decision tree (pre-sales key!)")
        print()
        print("Run all exercises:")
        for num, fn in exercises.items():
            print(f"\n{'='*50}")
            fn()
