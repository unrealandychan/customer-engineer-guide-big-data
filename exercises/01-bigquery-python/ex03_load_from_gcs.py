"""
Exercise 03 — Load Data from GCS into BigQuery
------------------------------------------------
Goal:
    - Upload a local CSV file to GCS
    - Load that GCS file into a new BigQuery table
    - Verify the data with a query
    - Understand LoadJobConfig options (schema, write disposition, skip rows)

Prerequisites:
    - A GCS bucket you own: set BUCKET_NAME below
    - A BigQuery dataset: set DATASET_ID below
    pip install google-cloud-bigquery google-cloud-storage
"""

import os
import io
from google.cloud import bigquery, storage

# ---------------------------------------------------------------------------
# CONFIG — edit these before running
# ---------------------------------------------------------------------------
PROJECT_ID  = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
BUCKET_NAME = os.environ.get("GCS_BUCKET", "your-bucket-name")
DATASET_ID  = "bq_exercises"
TABLE_ID    = "sales_data"
GCS_OBJECT  = "exercises/sales_data.csv"

# ---------------------------------------------------------------------------
# Sample CSV data (written to GCS in setup_sample_data)
# ---------------------------------------------------------------------------
SAMPLE_CSV = """order_id,customer_id,product,amount,order_date
1001,cust_a,Widget A,29.99,2025-01-15
1002,cust_b,Widget B,49.50,2025-01-16
1003,cust_a,Widget C,15.00,2025-01-17
1004,cust_c,Widget A,29.99,2025-01-18
1005,cust_b,Widget D,99.00,2025-01-19
1006,cust_d,Widget B,49.50,2025-01-20
1007,cust_a,Widget D,99.00,2025-01-21
1008,cust_c,Widget C,15.00,2025-01-22
"""

bq_client  = bigquery.Client(project=PROJECT_ID)
gcs_client = storage.Client(project=PROJECT_ID)


# ---------------------------------------------------------------------------
# STEP 0: Setup — create dataset and upload CSV to GCS
# ---------------------------------------------------------------------------
def setup() -> None:
    # Create BigQuery dataset (if it doesn't exist)
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = "US"
    bq_client.create_dataset(dataset_ref, exists_ok=True)
    print(f"Dataset `{DATASET_ID}` ready.")

    # Upload sample CSV to GCS
    bucket = gcs_client.bucket(BUCKET_NAME)
    blob   = bucket.blob(GCS_OBJECT)
    blob.upload_from_file(io.BytesIO(SAMPLE_CSV.encode()), content_type="text/csv")
    print(f"Uploaded sample CSV to gs://{BUCKET_NAME}/{GCS_OBJECT}")


# ---------------------------------------------------------------------------
# EXERCISE 3a: Load CSV from GCS with auto-detected schema
# ---------------------------------------------------------------------------
def load_csv_autodetect() -> None:
    """
    Load the CSV from GCS into BigQuery using schema auto-detection.
    BigQuery will infer column types from the file content.
    """
    uri        = f"gs://{BUCKET_NAME}/{GCS_OBJECT}"
    table_ref  = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}_autodetect"

    # TODO: Build a LoadJobConfig:
    #   - source_format = bigquery.SourceFormat.CSV
    #   - skip_leading_rows = 1  (skip header)
    #   - autodetect = True
    #   - write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    # TODO: Call bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    # TODO: Call .result() to wait for completion
    load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_ref)
    print(f"\nLoaded {table.num_rows} rows into {table_ref} (autodetect)")
    print(f"Schema: {[(f.name, f.field_type) for f in table.schema]}")


# ---------------------------------------------------------------------------
# EXERCISE 3b: Load CSV with explicit schema
# ---------------------------------------------------------------------------
def load_csv_explicit_schema() -> None:
    """
    Define the schema explicitly so BigQuery uses the exact types you want.
    This avoids type mismatches that auto-detect can introduce.
    """
    uri       = f"gs://{BUCKET_NAME}/{GCS_OBJECT}"
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}_explicit"

    # TODO: Define a schema as a list of bigquery.SchemaField objects
    #   bigquery.SchemaField("column_name", "TYPE", mode="NULLABLE" or "REQUIRED")
    #   Types: STRING, INTEGER, FLOAT64, DATE, TIMESTAMP, BOOL
    schema = [
        bigquery.SchemaField("order_id",     "INTEGER",  mode="REQUIRED"),
        bigquery.SchemaField("customer_id",  "STRING",   mode="REQUIRED"),
        bigquery.SchemaField("product",      "STRING",   mode="NULLABLE"),
        bigquery.SchemaField("amount",       "FLOAT64",  mode="NULLABLE"),
        bigquery.SchemaField("order_date",   "DATE",     mode="NULLABLE"),
    ]

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_ref)
    print(f"\nLoaded {table.num_rows} rows into {table_ref} (explicit schema)")


# ---------------------------------------------------------------------------
# EXERCISE 3c: Verify data with a query
# ---------------------------------------------------------------------------
def verify_loaded_data() -> None:
    query = f"""
        SELECT
            customer_id,
            COUNT(*)         AS order_count,
            SUM(amount)      AS total_spent,
            MIN(order_date)  AS first_order,
            MAX(order_date)  AS last_order
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}_explicit`
        GROUP BY customer_id
        ORDER BY total_spent DESC
    """
    print("\n=== Customer summary from loaded data ===")
    for row in bq_client.query(query).result():
        print(f"  {row.customer_id:<12} orders={row.order_count}  "
              f"spent=${row.total_spent:.2f}  "
              f"({row.first_order} → {row.last_order})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    setup()
    load_csv_autodetect()
    load_csv_explicit_schema()
    verify_loaded_data()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Change SAMPLE_CSV to have a bad row (e.g., amount = "N/A").
#    Run load_csv_autodetect() — what error do you get?
#    Fix it using job_config.max_bad_records = 1.
#
# 2. Upload a JSON-lines file to GCS and load it with:
#    source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
#
# 3. Try write_disposition = WRITE_APPEND and run the load twice.
#    How many rows do you get? How would you prevent duplicates?
