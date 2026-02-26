"""
Exercise 04 — Create Partitioned + Clustered Tables
-----------------------------------------------------
Goal:
    - Create a date-partitioned table with clustering
    - Insert rows using load_table_from_json (batch) and streaming insert
    - Observe bytes processed difference with/without partition filter
    - Set require_partition_filter and partition expiration

This is one of the MOST important BigQuery topics for the interview.
"""

import os
import datetime
import random
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
DATASET_ID = "bq_exercises"
TABLE_ID   = "events"

client = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


# ---------------------------------------------------------------------------
# EXERCISE 4a: Create a partitioned + clustered table
# ---------------------------------------------------------------------------
def create_partitioned_table() -> None:
    """
    Create a table partitioned by event_date (DATE column)
    and clustered by country and event_type.

    Why this matters in the interview:
      - Partitioning = skip whole date ranges (IO pruning at partition level)
      - Clustering = skip blocks within a partition (block pruning)
      - Combined = queries scan only the data they actually need
    """

    schema = [
        bigquery.SchemaField("event_id",    "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("event_date",  "DATE",      mode="REQUIRED"),
        bigquery.SchemaField("event_type",  "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("country",     "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("user_id",     "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("amount",      "FLOAT64",   mode="NULLABLE"),
    ]

    table = bigquery.Table(table_ref, schema=schema)

    # TODO: Set time partitioning on the event_date column
    #   bigquery.TimePartitioning(
    #       type_  = bigquery.TimePartitioningType.DAY,
    #       field  = "event_date",
    #       expiration_ms = 365 * 24 * 60 * 60 * 1000   # 1 year retention
    #   )
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="event_date",
        expiration_ms=365 * 24 * 60 * 60 * 1000,
    )

    # TODO: Set clustering fields — most-filtered columns first
    table.clustering_fields = ["country", "event_type"]

    # TODO: Require all queries to include a partition filter (prevents full scans)
    table.require_partition_filter = True

    client.create_table(table, exists_ok=True)
    print(f"Created table: {table_ref}")
    print(f"  Partition by : event_date (daily, 365-day expiry)")
    print(f"  Clustered by : country, event_type")
    print(f"  Partition filter required: True")


# ---------------------------------------------------------------------------
# EXERCISE 4b: Insert sample rows
# ---------------------------------------------------------------------------
def insert_sample_rows() -> None:
    """
    Generate synthetic event rows and load them into the partitioned table.
    """
    countries   = ["US", "GB", "DE", "JP", "BR", "AU"]
    event_types = ["purchase", "page_view", "signup", "refund"]
    rows        = []

    # Generate 500 events across the last 30 days
    for i in range(500):
        days_ago = random.randint(0, 29)
        event_date = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
        rows.append({
            "event_id":   f"evt_{i:05d}",
            "event_date": event_date,
            "event_type": random.choice(event_types),
            "country":    random.choice(countries),
            "user_id":    f"user_{random.randint(1, 100):04d}",
            "amount":     round(random.uniform(1.0, 500.0), 2),
        })

    # TODO: Load rows using client.load_table_from_json(rows, table_ref)
    #   Use WriteDisposition.WRITE_APPEND
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    load_job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    load_job.result()
    print(f"\nInserted {len(rows)} rows into {table_ref}")


# ---------------------------------------------------------------------------
# EXERCISE 4c: Compare bytes scanned WITH and WITHOUT partition filter
# ---------------------------------------------------------------------------
def compare_scan_cost() -> None:
    """
    Run two queries and compare bytes processed:
      1. With a partition filter   → scans only relevant partitions
      2. Without a partition filter → require_partition_filter will block this

    NOTE: require_partition_filter = True means the second query will fail.
    Temporarily set it to False on the table to run it for comparison.
    """
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    # Query WITH partition filter (fast, cheap)
    q_with_filter = f"""
        SELECT
            country,
            COUNT(*) AS events,
            SUM(amount) AS revenue
        FROM `{table_ref}`
        WHERE event_date BETWEEN '{week_ago}' AND '{today}'
          AND country = 'US'
        GROUP BY country
    """

    print("\n=== Comparing scan cost ===")
    job = client.query(q_with_filter)
    job.result()
    print(f"  WITH partition filter   → bytes scanned: {job.total_bytes_processed:>12,}")
    print(f"  Estimated cost         → ${job.total_bytes_processed / 1e12 * 6.25:.6f}")


# ---------------------------------------------------------------------------
# EXERCISE 4d: Window functions on the partitioned table
# ---------------------------------------------------------------------------
def run_window_functions() -> None:
    """
    Practice window functions — a very common interview SQL topic.
    """
    query = f"""
        WITH daily_revenue AS (
            SELECT
                event_date,
                country,
                SUM(amount) AS revenue
            FROM `{table_ref}`
            WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY event_date, country
        )
        SELECT
            event_date,
            country,
            revenue,
            -- 7-day rolling average per country
            AVG(revenue) OVER (
                PARTITION BY country
                ORDER BY event_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) AS rolling_7d_avg,
            -- Rank countries by revenue per day (1 = highest revenue)
            RANK() OVER (
                PARTITION BY event_date
                ORDER BY revenue DESC
            ) AS daily_rank
        FROM daily_revenue
        ORDER BY event_date DESC, daily_rank
        LIMIT 30
    """

    print("\n=== Window functions: rolling avg + daily rank ===")
    for row in client.query(query).result():
        print(f"  {row.event_date}  {row.country:<4}  "
              f"rev=${row.revenue:>8.2f}  "
              f"7d_avg=${row.rolling_7d_avg:>8.2f}  "
              f"rank=#{row.daily_rank}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    create_partitioned_table()
    insert_sample_rows()
    compare_scan_cost()
    run_window_functions()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. After running compare_scan_cost(), temporarily set require_partition_filter=False
#    on the table and run a query WITHOUT a date filter. How many bytes are scanned?
#    Compare the cost. Then re-enable the filter.
#
# 2. Add a TIMESTAMP column instead of DATE and use TIMESTAMP partitioning.
#    What changes in the LoadJobConfig and TimePartitioning setup?
#
# 3. Create a second version of the table clustered by user_id instead of country.
#    Run a query filtering on user_id and compare bytes processed.
