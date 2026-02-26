"""
Exercise 06 — BigQuery Schema Management (Python)
--------------------------------------------------
Goal:
    - Create, inspect, and update table schemas programmatically
    - Add / rename / relax columns (BigQuery rules are strict — learn them)
    - Understand schema evolution constraints
    - Work with RECORD (STRUCT) fields and REPEATED (ARRAY) fields
    - Use table snapshots and expiration

Interview relevance:
    "How do you safely add a column to a production BigQuery table?"
    "Can you rename a column in BigQuery?" (No — learn the workaround)
    "What is the difference between NULLABLE, REQUIRED, and REPEATED?"

Setup:
    pip install google-cloud-bigquery
    export GOOGLE_CLOUD_PROJECT=your-project-id
"""

import os
import time
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from google.api_core.exceptions import NotFound


def get_client() -> bigquery.Client:
    return bigquery.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT"))


PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
DATASET = "schema_exercises"
TABLE   = "events_v1"


# ---------------------------------------------------------------------------
# EXERCISE 1: Create a dataset and a table with an explicit schema
# ---------------------------------------------------------------------------

def create_dataset(client: bigquery.Client) -> bigquery.Dataset:
    """Create a dataset. Idempotent (exists_ok=True)."""
    ds_ref = bigquery.DatasetReference(PROJECT, DATASET)
    dataset = bigquery.Dataset(ds_ref)
    dataset.location = "US"
    dataset.description = "Schema management exercise dataset"

    # TODO: Use client.create_dataset(dataset, exists_ok=True)
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset: {dataset.full_dataset_id}")
    return dataset


def create_table_v1(client: bigquery.Client) -> bigquery.Table:
    """
    Create an events table with a mix of field modes:
      REQUIRED — field must be present (no NULL allowed)
      NULLABLE  — field can be NULL
      REPEATED  — field is an array (ARRAY<type> in SQL)

    Also demonstrates a nested RECORD (STRUCT) field.
    """
    table_ref = f"{PROJECT}.{DATASET}.{TABLE}"

    schema = [
        # Primary key (not enforced, but documented)
        SchemaField("event_id",   "STRING",    mode="REQUIRED",
                    description="Unique event identifier (UUID)"),
        SchemaField("event_date", "DATE",       mode="REQUIRED"),
        SchemaField("event_type", "STRING",     mode="NULLABLE"),
        SchemaField("country",    "STRING",     mode="NULLABLE"),
        SchemaField("amount",     "FLOAT64",    mode="NULLABLE"),

        # REPEATED field — stored as an array in BigQuery
        SchemaField("tags",       "STRING",     mode="REPEATED",
                    description="List of tags attached to the event"),

        # RECORD (STRUCT) — nested fields
        SchemaField("metadata",   "RECORD",     mode="NULLABLE",
                    fields=[
                        SchemaField("source",     "STRING",  mode="NULLABLE"),
                        SchemaField("version",    "STRING",  mode="NULLABLE"),
                        SchemaField("session_id", "STRING",  mode="NULLABLE"),
                    ]),
    ]

    table = bigquery.Table(table_ref, schema=schema)

    # Partition on event_date
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="event_date",
    )
    table.clustering_fields = ["country", "event_type"]

    # Auto-expire table after 90 days from last modification (optional)
    # table.expires = datetime.now(timezone.utc) + timedelta(days=90)

    # TODO: Use client.create_table(table, exists_ok=True)
    table = client.create_table(table, exists_ok=True)
    print(f"Table created: {table.full_table_id}")
    return table


# ---------------------------------------------------------------------------
# EXERCISE 2: Inspect a table schema
# ---------------------------------------------------------------------------

def inspect_table_schema(client: bigquery.Client) -> None:
    """
    Read the current schema of a table.
    Useful for: schema validation, documentation generation, audit.
    """
    table = client.get_table(f"{PROJECT}.{DATASET}.{TABLE}")

    print(f"\n=== Schema for {table.full_table_id} ===")
    print(f"Partitioned by: {table.time_partitioning}")
    print(f"Clustered by:   {table.clustering_fields}")
    print(f"Num rows:        {table.num_rows}")
    print(f"Num bytes:       {table.num_bytes}")
    print(f"Modified:        {table.modified}")
    print()

    def print_schema(fields, indent=0):
        prefix = "  " * indent
        for field in fields:
            mode_str = f"[{field.mode}]" if field.mode != "NULLABLE" else ""
            print(f"{prefix}{field.name:25s} {field.field_type:10s} {mode_str}")
            if field.fields:  # Nested RECORD
                print_schema(field.fields, indent + 1)

    print_schema(table.schema)


# ---------------------------------------------------------------------------
# EXERCISE 3: Schema evolution — adding columns
#
# BigQuery schema evolution rules:
#   ✅ ADD a new NULLABLE or REPEATED column                  (allowed)
#   ✅ RELAX a REQUIRED column to NULLABLE                    (allowed)
#   ✅ ADD a nested field to a REPEATED RECORD               (allowed)
#   ❌ Remove a column                                        (NOT allowed directly)
#   ❌ Rename a column                                        (NOT allowed directly)
#   ❌ Change a field's type (e.g., STRING → INTEGER)         (NOT allowed)
#   ❌ Make a NULLABLE column REQUIRED                        (NOT allowed)
# ---------------------------------------------------------------------------

def add_columns(client: bigquery.Client) -> None:
    """
    Add new nullable columns to an existing table.
    This is the most common schema evolution operation.
    """
    table = client.get_table(f"{PROJECT}.{DATASET}.{TABLE}")

    new_fields = [
        SchemaField("user_id",    "STRING",  mode="NULLABLE",
                    description="User identifier (added in v2)"),
        SchemaField("created_at", "TIMESTAMP", mode="NULLABLE",
                    description="Event creation timestamp"),
    ]

    # Merge existing schema with new fields
    original_schema = table.schema
    updated_schema  = original_schema + new_fields

    # TODO: Update the table object and call client.update_table
    table.schema = updated_schema
    table = client.update_table(table, ["schema"])

    print(f"\nAdded columns: {[f.name for f in new_fields]}")
    print(f"New column count: {len(table.schema)}")


def relax_required_column(client: bigquery.Client) -> None:
    """
    Relax a REQUIRED field to NULLABLE.
    Once a field is NULLABLE it CANNOT be changed back to REQUIRED.
    """
    table = client.get_table(f"{PROJECT}.{DATASET}.{TABLE}")

    updated_schema = []
    for field in table.schema:
        if field.name == "event_type" and field.mode == "REQUIRED":
            # Recreate the field with NULLABLE mode
            updated_schema.append(
                SchemaField(field.name, field.field_type, mode="NULLABLE",
                            description=field.description, fields=field.fields)
            )
            print(f"  Relaxed '{field.name}' from REQUIRED → NULLABLE")
        else:
            updated_schema.append(field)

    table.schema = updated_schema
    client.update_table(table, ["schema"])


# ---------------------------------------------------------------------------
# EXERCISE 4: "Rename" a column (workaround — BigQuery doesn't support rename)
# ---------------------------------------------------------------------------

def rename_column_workaround(client: bigquery.Client,
                              old_name: str, new_name: str) -> None:
    """
    BigQuery does NOT support renaming columns directly.
    Workaround: CREATE TABLE AS SELECT ... with the column renamed.
    This copies the data (costs money for large tables).

    Alternative (zero-cost but more complex):
      - Add new column
      - Backfill: UPDATE t SET new_col = old_col WHERE TRUE
      - Drop old column reference from queries (you can't delete columns)
      - Use a VIEW that selects new_col and hides old_col
    """
    new_table = TABLE + "_renamed"
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT}.{DATASET}.{new_table}` AS
    SELECT
        event_id,
        event_date,
        event_type,
        country,
        {old_name} AS {new_name},   -- Rename here
        tags,
        metadata
    FROM `{PROJECT}.{DATASET}.{TABLE}`
    """
    print(f"\nRename workaround: {old_name} → {new_name}")
    print(f"Query (would run):\n{query}")
    # Uncomment to actually run:
    # client.query(query).result()


# ---------------------------------------------------------------------------
# EXERCISE 5: Insert rows and verify schema enforcement
# ---------------------------------------------------------------------------

def insert_sample_rows(client: bigquery.Client) -> None:
    """Insert test rows that exercise all field types."""
    table_ref = f"{PROJECT}.{DATASET}.{TABLE}"

    rows = [
        {
            "event_id":   "evt-001",
            "event_date": "2024-01-15",
            "event_type": "purchase",
            "country":    "US",
            "amount":     99.99,
            "tags":       ["promo", "mobile"],      # REPEATED field = list
            "metadata": {                             # RECORD field = dict
                "source":     "web",
                "version":    "3.1",
                "session_id": "sess-abc123",
            },
        },
        {
            "event_id":   "evt-002",
            "event_date": "2024-01-15",
            "event_type": "view",
            "country":    "GB",
            "amount":     None,                      # NULL for NULLABLE field
            "tags":       [],                         # Empty REPEATED = empty array
            "metadata":   None,                       # NULL for NULLABLE RECORD
        },
    ]

    # TODO: Use client.insert_rows_json(table_ref, rows)
    errors = client.insert_rows_json(table_ref, rows)

    if errors:
        print(f"Insert errors: {errors}")
    else:
        print(f"Inserted {len(rows)} rows into {table_ref}")
        print("Note: Streaming inserts may take 90s to appear in SELECT queries.")


# ---------------------------------------------------------------------------
# EXERCISE 6: Table copies, snapshots, and expiry
# ---------------------------------------------------------------------------

def copy_table(client: bigquery.Client, dest_table_id: str) -> None:
    """Copy a table (snapshot at point in time — reads all partitions)."""
    src = f"{PROJECT}.{DATASET}.{TABLE}"
    dst = f"{PROJECT}.{DATASET}.{dest_table_id}"

    job_config = bigquery.CopyJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    job = client.copy_table(src, dst, job_config=job_config)
    job.result()  # Wait for completion
    print(f"Copied {src} → {dst}")


def set_table_expiration(client: bigquery.Client, days: int = 30) -> None:
    """Set table expiration so it is auto-deleted after N days."""
    table = client.get_table(f"{PROJECT}.{DATASET}.{TABLE}")
    table.expires = datetime.now(timezone.utc) + timedelta(days=days)

    # TODO: Use client.update_table(table, ["expires"])
    client.update_table(table, ["expires"])
    print(f"Table will expire on: {table.expires.isoformat()}")


def delete_table(client: bigquery.Client) -> None:
    """Delete a table. Raises NotFound if it doesn't exist."""
    table_ref = f"{PROJECT}.{DATASET}.{TABLE}"
    try:
        client.delete_table(table_ref)
        print(f"Deleted table: {table_ref}")
    except NotFound:
        print(f"Table not found (already deleted?): {table_ref}")


# ---------------------------------------------------------------------------
# Main — run all exercises
# ---------------------------------------------------------------------------

def main():
    client = get_client()

    # Setup
    create_dataset(client)
    create_table_v1(client)

    # Inspect
    inspect_table_schema(client)

    # Evolve schema
    add_columns(client)
    inspect_table_schema(client)

    # Insert data
    insert_sample_rows(client)

    # Demonstrate rename workaround
    rename_column_workaround(client, old_name="amount", new_name="transaction_amount")

    # Cleanup (comment out to keep resources)
    # set_table_expiration(client, days=1)
    # delete_table(client)


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Add a REPEATED RECORD field (array of structs):
#    SchemaField("line_items", "RECORD", mode="REPEATED", fields=[
#        SchemaField("product_id", "STRING", mode="NULLABLE"),
#        SchemaField("quantity",   "INTEGER", mode="NULLABLE"),
#        SchemaField("price",      "FLOAT64", mode="NULLABLE"),
#    ])
#    Then insert a row with multiple line items and query with UNNEST().
#
# 2. Use the BigQuery Data Policy API to set column-level access control
#    (column masking) on the "amount" field so only certain roles see it.
#
# 3. Create a VIEW over the table that renames "amount" to "transaction_amount"
#    without copying data:
#    client.create_table(bigquery.Table(view_ref), exists_ok=True) with view_query set.
#
# 4. Write a schema migration function that:
#    - Compares two schema lists (current vs desired)
#    - Identifies safe operations (add nullable, relax required)
#    - Raises an error for unsafe operations (type change, column removal)
