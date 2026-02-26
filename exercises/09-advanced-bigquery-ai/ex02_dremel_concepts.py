"""
Exercise: Dremel Concepts — Understanding BigQuery's Engine
-----------------------------------------------------------
Topics: Columnar storage, repetition/definition levels, query execution model,
        slots, bytes scanned optimization, execution plan analysis

Based on: Dremel paper (2010), Dremel 2.0 (2020), BigQuery INFORMATION_SCHEMA
Purpose: Deep technical understanding for whitepaper interview questions
"""

from google.cloud import bigquery
import json

PROJECT_ID = "your-project-id"
DATASET_ID = "dremel_concepts"

client = bigquery.Client(project=PROJECT_ID)


# ---------------------------------------------------------------------------
# Exercise 1: Demonstrate Columnar Storage Impact — SELECT * vs SELECT col
# ---------------------------------------------------------------------------
# In Dremel's columnar storage, SELECT * reads ALL columns.
# SELECT specific_column reads only that column's storage.
# This is why bytes_processed differs dramatically.

def exercise_1_columnar_impact():
    """
    Demonstrate that column selection directly impacts bytes scanned —
    this is Dremel's columnar storage in action.

    Real example using BigQuery public dataset (Stack Overflow):
    - SELECT * → reads all ~50 columns
    - SELECT id → reads only 1 column
    - Cost savings: ~50x fewer bytes scanned
    """
    print("=== Exercise 1: Columnar Storage Impact (Dremel Principle) ===")
    print()

    # Dry-run queries to see bytes that would be processed
    queries = {
        "SELECT * (all columns)": """
            SELECT *
            FROM `bigquery-public-data.stackoverflow.posts_questions`
            LIMIT 1000
        """,
        "SELECT id only (1 column)": """
            SELECT id
            FROM `bigquery-public-data.stackoverflow.posts_questions`
            LIMIT 1000
        """,
        "SELECT id, title (2 columns)": """
            SELECT id, title
            FROM `bigquery-public-data.stackoverflow.posts_questions`
            LIMIT 1000
        """,
    }

    print("Dry-run comparison (bytes processed without actually running):\n")
    for description, sql in queries.items():
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        try:
            job = client.query(sql.strip(), job_config=job_config)
            bytes_gb = job.total_bytes_processed / (1024**3)
            print(f"  {description}")
            print(f"    Bytes: {job.total_bytes_processed:,} ({bytes_gb:.3f} GB)")
            print()
        except Exception as e:
            print(f"  {description}")
            print(f"    [Dry run unavailable in demo mode — would show: ~X GB vs ~0.01 GB]")
            print()

    print("Key lesson: In Dremel's columnar format,")
    print("  SELECT * = read all column files from Colossus storage")
    print("  SELECT id = read ONLY the id column file")
    print("  Estimated cost: SELECT * ~50x more expensive than SELECT id")
    print()
    print("Interview answer: 'SELECT * is expensive in BigQuery because Dremel")
    print("reads only the columns referenced — SELECT * forces reading all of them.'")


# ---------------------------------------------------------------------------
# Exercise 2: Nested Record Structure — Dremel's Repetition/Definition Levels
# ---------------------------------------------------------------------------

def exercise_2_nested_records():
    """
    Demonstrate Dremel's columnar encoding for nested + repeated fields.

    Dremel represents nested records using two metadata arrays per column:
    - Repetition level (r): which level of repeated field did this value restart at?
    - Definition level (d): how many nullable fields in the path are defined?

    This is exactly how BigQuery stores STRUCT and ARRAY columns.
    """
    print("=== Exercise 2: Nested Records — Dremel Repetition/Definition Levels ===")
    print()

    create_nested_table_sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.orders` AS
    SELECT * FROM UNNEST([
      STRUCT(
        'ORD-001' AS order_id,
        'Alice' AS customer_name,
        [
          STRUCT('SKU-A' AS sku, 2 AS quantity, 15.99 AS unit_price),
          STRUCT('SKU-B', 1, 29.99)
        ] AS line_items
      ),
      STRUCT(
        'ORD-002',
        'Bob',
        [
          STRUCT('SKU-C', 3, 9.99)
        ]
      ),
      STRUCT(
        'ORD-003',
        'Carol',
        NULL  -- no line items
      )
    ]);
    """

    print("Schema: orders(order_id, customer_name, line_items[]{sku, quantity, unit_price})")
    print()
    print("In Dremel's columnar storage, 'line_items.sku' is stored as a flat array:")
    print()
    print("  Record values:  ['SKU-A', 'SKU-B',  'SKU-C',  NULL   ]")
    print("  Repetition (r): [0,       1,         0,        0      ]")
    print("  Definition (d): [2,       2,         2,        1      ]")
    print()
    print("  r=0 → new top-level record starts here")
    print("  r=1 → repetition at line_items level (another item in same order)")
    print("  d=2 → both 'line_items' and 'line_items.sku' are defined (non-null)")
    print("  d=1 → 'line_items' level is null (Carol has no items)")
    print()

    # Query demonstrating UNNEST of nested arrays
    query_nested_sql = f"""
    SELECT
      order_id,
      customer_name,
      item.sku,
      item.quantity,
      item.unit_price,
      item.quantity * item.unit_price AS line_total
    FROM `{PROJECT_ID}.{DATASET_ID}.orders`,
    UNNEST(line_items) AS item
    ORDER BY order_id, item.sku;
    """

    print("Query to unnest and flatten nested records:")
    print(query_nested_sql)
    print()
    print("Expected output:")
    print("  ORD-001 | Alice | SKU-A | 2 | 15.99 | 31.98")
    print("  ORD-001 | Alice | SKU-B | 1 | 29.99 | 29.99")
    print("  ORD-002 | Bob   | SKU-C | 3 |  9.99 | 29.97")
    print("  ORD-003 | Carol | NULL  | - |  NULL | NULL")
    print()
    print("Key insight: Dremel reads ONLY line_items.sku from storage")
    print("when you do SELECT item.sku — skips all other columns entirely.")


# ---------------------------------------------------------------------------
# Exercise 3: INFORMATION_SCHEMA — Analyzing Slot Usage and Query Performance
# ---------------------------------------------------------------------------

def exercise_3_slot_analysis():
    """
    Use INFORMATION_SCHEMA to understand slot consumption and query efficiency.
    This is how you diagnose performance problems in production.

    Slots = Dremel leaf/mixer nodes processing in parallel
    More slots used = query is doing more parallel work
    High elapsed_ms with low slot_ms = CPU is not the bottleneck (maybe I/O)
    """
    print("=== Exercise 3: Slot Usage Analysis via INFORMATION_SCHEMA ===")
    print()

    # Query 1: Find the most slot-intensive queries in the last 7 days
    heavy_queries_sql = f"""
    SELECT
      job_id,
      user_email,
      query,
      total_bytes_processed / POW(1024, 3) AS bytes_processed_gb,
      total_slot_ms / 1000.0 AS slot_seconds,
      (total_slot_ms / TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)) AS avg_slots_used,
      TIMESTAMP_DIFF(end_time, start_time, SECOND) AS duration_seconds,
      ROUND(total_bytes_processed / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd
    FROM `{PROJECT_ID}`.INFORMATION_SCHEMA.JOBS
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      AND job_type = 'QUERY'
      AND state = 'DONE'
      AND error_result IS NULL
    ORDER BY total_slot_ms DESC
    LIMIT 20;
    """

    print("Query 1: Top slot-consuming queries (last 7 days):")
    print(heavy_queries_sql)
    print()

    # Query 2: Find queries scanning too much data (no partition filter)
    expensive_scans_sql = f"""
    SELECT
      job_id,
      user_email,
      total_bytes_processed / POW(1024, 3) AS bytes_gb,
      ROUND(total_bytes_processed / POW(1024, 4) * 6.25, 2) AS cost_usd,
      -- Extract tables touched (from referenced_tables)
      ARRAY_TO_STRING(
        ARRAY(SELECT CONCAT(t.project_id, '.', t.dataset_id, '.', t.table_id)
              FROM UNNEST(referenced_tables) AS t),
        ', '
      ) AS tables_scanned,
      SUBSTR(query, 1, 200) AS query_preview
    FROM `{PROJECT_ID}`.INFORMATION_SCHEMA.JOBS
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND job_type = 'QUERY'
      AND total_bytes_processed > 100 * POW(1024, 3)  -- > 100 GB scanned
    ORDER BY total_bytes_processed DESC
    LIMIT 10;
    """

    print("Query 2: Find expensive full-table scans (no partition pruning):")
    print(expensive_scans_sql)
    print()

    # Query 3: Slot utilization over time (for capacity planning)
    slot_utilization_sql = f"""
    SELECT
      TIMESTAMP_TRUNC(creation_time, HOUR) AS hour,
      SUM(total_slot_ms) / (3600 * 1000) AS total_slot_hours,
      COUNT(*) AS query_count,
      AVG(total_bytes_processed / POW(1024, 3)) AS avg_gb_per_query
    FROM `{PROJECT_ID}`.INFORMATION_SCHEMA.JOBS
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      AND job_type = 'QUERY'
      AND state = 'DONE'
    GROUP BY 1
    ORDER BY 1 DESC;
    """

    print("Query 3: Slot utilization trend (for edition/commitment decision):")
    print(slot_utilization_sql)
    print()
    print("Pre-sales insight: Show a customer this query on their project.")
    print("If avg_slot_hours > N consistently → capacity commitment saves money.")


# ---------------------------------------------------------------------------
# Exercise 4: Partition Pruning — Dremel I/O Optimization
# ---------------------------------------------------------------------------

def exercise_4_partition_pruning():
    """
    Demonstrate partition pruning: BigQuery reads only the relevant
    partition files from Colossus storage — not the whole table.

    This is a direct Dremel optimization: fewer files to open = less I/O.
    """
    print("=== Exercise 4: Partition Pruning — Dremel I/O Optimization ===")
    print()

    setup_sql = f"""
    -- Create a partitioned + clustered events table
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.events`
    PARTITION BY DATE(event_time)
    CLUSTER BY user_id, event_type
    AS
    SELECT
      GENERATE_UUID() AS event_id,
      'user_' || CAST(CAST(RAND() * 1000 AS INT64) AS STRING) AS user_id,
      CASE CAST(RAND() * 4 AS INT64)
        WHEN 0 THEN 'click'
        WHEN 1 THEN 'purchase'
        WHEN 2 THEN 'view'
        ELSE 'search'
      END AS event_type,
      RAND() * 1000 AS amount,
      TIMESTAMP_SUB(CURRENT_TIMESTAMP(),
                    INTERVAL CAST(RAND() * 90 AS INT64) DAY) AS event_time
    FROM UNNEST(GENERATE_ARRAY(1, 1000000));
    """

    print("Setup: 1M row events table, partitioned by day, clustered by user+type")
    print(setup_sql)
    print()

    # Bad query — no partition filter, full scan
    bad_query = f"""
    -- BAD: No partition filter → reads ALL partitions (90 days of data)
    SELECT COUNT(*), SUM(amount)
    FROM `{PROJECT_ID}.{DATASET_ID}.events`
    WHERE event_type = 'purchase';
    -- Bytes scanned: ~1TB (all 90 partitions)
    """

    # Good query — partition filter + cluster filter
    good_query = f"""
    -- GOOD: Partition + cluster pruning → reads only 7 partition files
    --       AND only the 'purchase' cluster blocks within those partitions
    SELECT COUNT(*), SUM(amount)
    FROM `{PROJECT_ID}.{DATASET_ID}.events`
    WHERE
      event_time >= TIMESTAMP('2025-02-19')  -- partition filter
      AND event_time <  TIMESTAMP('2025-02-26')
      AND event_type = 'purchase'            -- cluster filter
      AND user_id LIKE 'user_5%';            -- cluster filter
    -- Bytes scanned: ~10GB (7 partitions × cluster pruning)
    -- 100x reduction in I/O = 100x cost reduction
    """

    print("BAD query (no partition filter):")
    print(bad_query)
    print()
    print("GOOD query (partition + cluster filters):")
    print(good_query)
    print()
    print("Dremel explanation:")
    print("  Partitions = separate directories in Colossus")
    print("  Cluster blocks = sorted mini-files within each partition")
    print("  Dremel opens only the relevant files — skips rest entirely")
    print("  Result: 100x fewer bytes read = 100x lower cost + faster query")
    print()
    print("Require partition filter (prevent accidental full scans):")
    require_filter_sql = f"""
    ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.events`
    SET OPTIONS (require_partition_filter = TRUE);
    """
    print(require_filter_sql)


# ---------------------------------------------------------------------------
# Exercise 5: Understanding Dremel Execution Plan (EXPLAIN)
# ---------------------------------------------------------------------------

def exercise_5_execution_plan():
    """
    Analyze BigQuery's query execution plan to understand Dremel's
    multi-level tree execution. BigQuery Console shows this visually;
    here we simulate what it shows.
    """
    print("=== Exercise 5: Dremel Execution Plan Analysis ===")
    print()
    print("In BigQuery Console → Query results → Execution details")
    print("You see the Dremel multi-level execution tree:")
    print()

    execution_plan_explanation = """
    Dremel Execution Plan Anatomy:
    ┌─────────────────────────────────────────────────────────┐
    │  Stage S00: Input (READ from Colossus storage)          │
    │    Workers: 500                                         │
    │    Records read: 1,000,000,000                          │
    │    Bytes read: 2.4 TB → after column pruning: 15 GB     │
    │    Operations: SCAN (partition: event_time, cluster: user_id) │
    ├─────────────────────────────────────────────────────────┤
    │  Stage S01: Repartition + Sort (Shuffle)                │
    │    Workers: 200                                         │
    │    Records shuffled: 50,000,000                         │
    │    This is Dremel 2.0's disaggregated shuffle           │
    │    (in-memory across network, not disk)                 │
    ├─────────────────────────────────────────────────────────┤
    │  Stage S02: Aggregation (GROUP BY)                      │
    │    Workers: 50                                          │
    │    Records output: 1,000 (one per group)                │
    ├─────────────────────────────────────────────────────────┤
    │  Stage S03: Final Merge (Root server)                   │
    │    Workers: 1                                           │
    │    Records output: 1,000                                │
    │    Written to: results table                            │
    └─────────────────────────────────────────────────────────┘

    Key metrics to look for:
    • avg_cpu_ms vs elapsed_ms: if elapsed >> cpu, there's a straggler
    • input_units vs output_units: large reduction = good GROUP BY
    • shuffle bytes: high = consider pre-aggregation or clustering
    • REPARTITION_BY_HASH: triggers for window functions, JOINs
    """

    print(execution_plan_explanation)

    # Query to get job stats via API
    stats_query = f"""
    SELECT
      job_id,
      statement_type,
      total_bytes_processed,
      total_slot_ms,
      -- Per-stage breakdown (requires jobs.getQueryResults)
      -- Access via: bq show --format=prettyjson <project>:<job_id>
      referenced_tables,
      labels
    FROM `{PROJECT_ID}`.INFORMATION_SCHEMA.JOBS
    WHERE job_id = 'YOUR_JOB_ID'  -- replace with actual job ID
    LIMIT 1;
    """

    print("Get job execution details via INFORMATION_SCHEMA:")
    print(stats_query)
    print()
    print("Or via CLI:")
    print("  bq show --format=prettyjson myproject:US.bqjob_r123abc")
    print()
    print("Interview answer for 'What happens when you run a BigQuery query?':")
    print("""
  1. Query submitted to BigQuery API → parsed into execution plan
  2. Planner allocates slots (Dremel workers) from your reservation
  3. S00: Leaf workers open columnar files in Colossus — only queried columns
  4. S01: Shuffle — partial results move across network (Dremel 2.0: in-memory)
  5. S02+: Intermediate aggregation at mixer nodes
  6. S03: Root server assembles final result
  7. Result written to temporary table → returned to user
  Total wall-clock: seconds for TBs (thousands of parallel workers)
    """)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    exercises = {
        "1": exercise_1_columnar_impact,
        "2": exercise_2_nested_records,
        "3": exercise_3_slot_analysis,
        "4": exercise_4_partition_pruning,
        "5": exercise_5_execution_plan,
    }

    if len(sys.argv) > 1 and sys.argv[1] in exercises:
        exercises[sys.argv[1]]()
    else:
        print("Dremel Concepts Exercises — BigQuery Engine Deep Dive")
        print("=" * 55)
        print("Usage: python ex02_dremel_concepts.py <exercise_number>")
        print()
        print("Exercises:")
        print("  1 - Columnar storage impact (SELECT * vs SELECT col)")
        print("  2 - Nested records (repetition/definition levels)")
        print("  3 - Slot usage analysis via INFORMATION_SCHEMA")
        print("  4 - Partition pruning (Dremel I/O optimization)")
        print("  5 - Execution plan analysis (multi-level tree)")
        print()
        for num, fn in exercises.items():
            print(f"\n{'='*55}")
            fn()
