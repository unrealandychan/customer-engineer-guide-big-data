"""
Exercise 07 — Streaming Inserts into BigQuery
----------------------------------------------
Goal:
    - Use the BigQuery Storage Write API (recommended) for streaming
    - Understand streaming insert vs batch load trade-offs
    - Handle insert errors (partial failures)
    - Simulate a real-time event producer

Interview relevance:
    "How do you ingest real-time events into BigQuery?"
    Streaming inserts = seconds latency, higher cost per GB.
    Storage Write API = better throughput, exactly-once semantics.
"""

import os
import uuid
import time
import random
import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
DATASET_ID = "bq_exercises"
TABLE_ID   = "streaming_events"

client    = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


# ---------------------------------------------------------------------------
# STEP 0: Create target table (no require_partition_filter so streaming works easily)
# ---------------------------------------------------------------------------
def create_streaming_table() -> None:
    schema = [
        bigquery.SchemaField("event_id",    "STRING",  mode="REQUIRED"),
        bigquery.SchemaField("event_time",  "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("user_id",     "STRING",  mode="NULLABLE"),
        bigquery.SchemaField("action",      "STRING",  mode="NULLABLE"),
        bigquery.SchemaField("page",        "STRING",  mode="NULLABLE"),
        bigquery.SchemaField("session_id",  "STRING",  mode="NULLABLE"),
    ]
    table = bigquery.Table(table_ref, schema=schema)
    # Partition by ingestion time (auto — no field required)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
    )
    client.create_table(table, exists_ok=True)
    print(f"Target table ready: {table_ref}")


# ---------------------------------------------------------------------------
# EXERCISE 7a: Stream a single batch of rows using insert_rows_json
# ---------------------------------------------------------------------------
def stream_events(num_events: int = 10) -> None:
    """
    Stream rows into BigQuery using the legacy streaming API (insert_rows_json).
    Data is available for querying within seconds.

    Pricing: $0.01 per 200MB of streamed data (more expensive than batch load).
    """
    actions = ["click", "scroll", "purchase", "add_to_cart", "view_product"]
    pages   = ["/home", "/product/123", "/cart", "/checkout", "/confirm"]

    rows = []
    for _ in range(num_events):
        rows.append({
            "event_id":   str(uuid.uuid4()),
            "event_time": datetime.datetime.utcnow().isoformat(),
            "user_id":    f"user_{random.randint(1, 50):04d}",
            "action":     random.choice(actions),
            "page":       random.choice(pages),
            "session_id": str(uuid.uuid4())[:8],
        })

    # TODO: Call client.insert_rows_json(table_ref, rows)
    # It returns a list of errors (empty list = success)
    errors = client.insert_rows_json(table_ref, rows)

    if errors:
        print(f"Streaming insert errors: {errors}")
    else:
        print(f"Successfully streamed {len(rows)} events into {table_ref}")


# ---------------------------------------------------------------------------
# EXERCISE 7b: Simulate a real-time producer loop
# ---------------------------------------------------------------------------
def simulate_realtime_producer(duration_seconds: int = 30, rate_per_second: int = 5) -> None:
    """
    Continuously stream events for `duration_seconds`.
    This simulates a real-time event source (e.g., a web server sending clickstream).

    In production, you'd typically use:
      Pub/Sub → Dataflow → BigQuery   (recommended for high volume)
      or direct streaming for low volume (<1MB/s)
    """
    print(f"\nStreaming {rate_per_second} events/sec for {duration_seconds}s...")
    total = 0
    start = time.time()

    while time.time() - start < duration_seconds:
        stream_events(rate_per_second)
        total += rate_per_second
        time.sleep(1)

    print(f"Done. Streamed {total} events total.")


# ---------------------------------------------------------------------------
# EXERCISE 7c: Query recently streamed data
# ---------------------------------------------------------------------------
def query_recent_events() -> None:
    """
    Note: streamed rows may not appear in query results for a few seconds.
    Use CURRENT_TIMESTAMP() to query the streaming buffer.
    """
    query = f"""
        SELECT
            action,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_id) AS unique_users
        FROM `{table_ref}`
        WHERE event_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 MINUTE)
        GROUP BY action
        ORDER BY event_count DESC
    """
    print("\n=== Events in the last 10 minutes ===")
    for row in client.query(query).result():
        print(f"  {row.action:<20} events={row.event_count:>5}  users={row.unique_users:>4}")


# ---------------------------------------------------------------------------
# EXERCISE 7d: Handle partial insert failures
# ---------------------------------------------------------------------------
def stream_with_bad_row() -> None:
    """
    Insert a mix of good and bad rows.
    insert_rows_json returns per-row errors — handle them gracefully.
    """
    rows = [
        {   # Good row
            "event_id":   str(uuid.uuid4()),
            "event_time": datetime.datetime.utcnow().isoformat(),
            "user_id":    "user_0001",
            "action":     "click",
            "page":       "/home",
            "session_id": "abc123",
        },
        {   # Bad row: event_time is not a valid timestamp
            "event_id":   str(uuid.uuid4()),
            "event_time": "NOT_A_TIMESTAMP",
            "user_id":    "user_0002",
            "action":     "scroll",
            "page":       "/home",
            "session_id": "def456",
        },
    ]

    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        print(f"\nPartial insert errors (expected):")
        for error in errors:
            print(f"  Row index {error['index']}: {error['errors']}")
    else:
        print("\nAll rows inserted (no errors)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    create_streaming_table()
    stream_events(num_events=20)
    # Uncomment to run a 30-second producer loop:
    # simulate_realtime_producer(duration_seconds=30, rate_per_second=5)
    time.sleep(3)   # Brief wait for streaming buffer
    query_recent_events()
    stream_with_bad_row()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Measure the latency: record time before streaming and keep querying
#    until the rows appear. What's the typical lag?
#
# 2. Research the BigQuery Storage Write API (google-cloud-bigquery-storage).
#    How does it differ from insert_rows_json? When would you use it?
#    Key differences: exactly-once, higher throughput, lower cost.
#
# 3. Compare costs:
#    - Streaming 1GB/day via insert_rows_json: $0.01 * (1000MB/200MB) = $0.05/day
#    - Loading 1GB/day from GCS: FREE
#    When is streaming worth the extra cost?
