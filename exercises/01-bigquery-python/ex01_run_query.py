"""
Exercise 01 — Run a BigQuery Query and Print Results
-----------------------------------------------------
Goal:
    - Connect to BigQuery using the Python client library
    - Run a SQL query against a public dataset
    - Iterate over results and print rows
    - Load results into a Pandas DataFrame

Dataset used: bigquery-public-data.samples.shakespeare
"""

from google.cloud import bigquery
import pandas as pd

# ---------------------------------------------------------------------------
# STEP 1: Create a BigQuery client
# The client automatically uses GOOGLE_CLOUD_PROJECT and
# GOOGLE_APPLICATION_CREDENTIALS environment variables.
# ---------------------------------------------------------------------------
client = bigquery.Client()


# ---------------------------------------------------------------------------
# EXERCISE 1a: Run a basic query and iterate over results
# ---------------------------------------------------------------------------
def run_basic_query() -> None:
    query = """
        SELECT
            word,
            SUM(word_count) AS total_count
        FROM
            `bigquery-public-data.samples.shakespeare`
        GROUP BY
            word
        ORDER BY
            total_count DESC
        LIMIT 10
    """

    print("=== Top 10 most frequent words in Shakespeare ===")
    # TODO: Execute the query using client.query(query)
    # TODO: Call .result() to wait for completion
    # TODO: Iterate and print each row's word and total_count
    query_job = client.query(query)
    results = query_job.result()

    for row in results:
        print(f"  {row.word:<20} {row.total_count:>8,}")


# ---------------------------------------------------------------------------
# EXERCISE 1b: Load results into a Pandas DataFrame
# ---------------------------------------------------------------------------
def run_query_to_dataframe() -> pd.DataFrame:
    query = """
        SELECT
            corpus,
            COUNT(DISTINCT word) AS unique_words,
            SUM(word_count)      AS total_words
        FROM
            `bigquery-public-data.samples.shakespeare`
        GROUP BY
            corpus
        ORDER BY
            total_words DESC
        LIMIT 20
    """

    # TODO: Use client.query(query).to_dataframe() to get a DataFrame
    df = client.query(query).to_dataframe()
    print("\n=== Words per Shakespeare work (top 20) ===")
    print(df.to_string(index=False))
    return df


# ---------------------------------------------------------------------------
# EXERCISE 1c: Inspect job metadata — bytes scanned, duration
# ---------------------------------------------------------------------------
def inspect_job_metadata() -> None:
    query = """
        SELECT word, word_count
        FROM `bigquery-public-data.samples.shakespeare`
        WHERE word = 'love'
        LIMIT 100
    """

    query_job = client.query(query)
    query_job.result()  # Wait for completion

    # TODO: Print the following job statistics:
    #   - query_job.total_bytes_processed  (bytes scanned)
    #   - query_job.total_bytes_billed     (bytes billed — min 10MB)
    #   - query_job.slot_millis            (slot-milliseconds used)
    #   - (query_job.ended - query_job.started).total_seconds()
    print("\n=== Job metadata ===")
    print(f"  Bytes scanned : {query_job.total_bytes_processed:,}")
    print(f"  Bytes billed  : {query_job.total_bytes_billed:,}")
    print(f"  Slot-ms used  : {query_job.slot_millis:,}")
    duration = (query_job.ended - query_job.started).total_seconds()
    print(f"  Duration      : {duration:.2f}s")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_basic_query()
    run_query_to_dataframe()
    inspect_job_metadata()

# ---------------------------------------------------------------------------
# CHALLENGES (try these after the basics work)
# ---------------------------------------------------------------------------
# 1. Change the query in run_basic_query() to filter only words longer than
#    5 characters. How does the result change?
#
# 2. In inspect_job_metadata(), run the same query twice in a row.
#    Does the second run show 0 bytes billed? (BigQuery result cache)
#
# 3. Add a LIMIT 5 to the basic query. Does bytes_processed change?
#    (It should NOT — LIMIT does not reduce scan cost.)
