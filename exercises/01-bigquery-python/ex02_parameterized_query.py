"""
Exercise 02 — Parameterized Queries
-------------------------------------
Goal:
    - Understand why parameterized queries matter (prevent SQL injection)
    - Use bigquery.ScalarQueryParameter and ArrayQueryParameter
    - Pass named parameters via QueryJobConfig

Reference:
    https://cloud.google.com/bigquery/docs/parameterized-queries
"""

from google.cloud import bigquery

client = bigquery.Client()


# ---------------------------------------------------------------------------
# EXERCISE 2a: Scalar parameter — single value filter
# ---------------------------------------------------------------------------
def query_by_word(word: str) -> None:
    """
    Safely query Shakespeare for a specific word using a named parameter.
    Never use f-strings or .format() for user-supplied SQL values!
    """
    query = """
        SELECT
            corpus,
            SUM(word_count) AS occurrences
        FROM
            `bigquery-public-data.samples.shakespeare`
        WHERE
            word = @target_word
        GROUP BY
            corpus
        ORDER BY
            occurrences DESC
    """

    # TODO: Create a QueryJobConfig with a ScalarQueryParameter
    #   bigquery.ScalarQueryParameter(name, type_, value)
    #   type_ = "STRING" for text values
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("target_word", "STRING", word)
        ]
    )

    print(f"\n=== Occurrences of '{word}' by work ===")
    results = client.query(query, job_config=job_config).result()
    for row in results:
        print(f"  {row.corpus:<40} {row.occurrences:>5}")


# ---------------------------------------------------------------------------
# EXERCISE 2b: Array parameter — filter by multiple values at once
# ---------------------------------------------------------------------------
def query_multiple_words(words: list[str]) -> None:
    """
    Find total occurrences of each word in a list, across all works.
    Use an ArrayQueryParameter to pass the list safely.
    """
    query = """
        SELECT
            word,
            SUM(word_count) AS total
        FROM
            `bigquery-public-data.samples.shakespeare`
        WHERE
            word IN UNNEST(@word_list)
        GROUP BY
            word
        ORDER BY
            total DESC
    """

    # TODO: Create a QueryJobConfig with an ArrayQueryParameter
    #   bigquery.ArrayQueryParameter(name, array_type, values)
    #   array_type = "STRING"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("word_list", "STRING", words)
        ]
    )

    print(f"\n=== Totals for words: {words} ===")
    results = client.query(query, job_config=job_config).result()
    for row in results:
        print(f"  {row.word:<20} {row.total:>8,}")


# ---------------------------------------------------------------------------
# EXERCISE 2c: Struct parameter — combine multiple filter values
# ---------------------------------------------------------------------------
def query_with_min_count(word: str, min_count: int) -> None:
    """
    Find all works where 'word' appears at least 'min_count' times.
    Uses two scalar parameters of different types.
    """
    query = """
        SELECT
            corpus,
            SUM(word_count) AS occurrences
        FROM
            `bigquery-public-data.samples.shakespeare`
        WHERE
            word = @word
        GROUP BY
            corpus
        HAVING
            SUM(word_count) >= @min_count
        ORDER BY
            occurrences DESC
    """

    # TODO: Add two ScalarQueryParameters — one STRING, one INT64
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("word", "STRING", word),
            bigquery.ScalarQueryParameter("min_count", "INT64", min_count),
        ]
    )

    print(f"\n=== Works where '{word}' appears >= {min_count} times ===")
    results = client.query(query, job_config=job_config).result()
    for row in results:
        print(f"  {row.corpus:<40} {row.occurrences:>5}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    query_by_word("love")
    query_multiple_words(["love", "death", "king", "sword", "night"])
    query_with_min_count("king", min_count=50)

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Try passing a raw f-string SQL (no parameters) with user input "love' OR '1'='1".
#    Notice how it could corrupt or expose data. Then show the parameterized version is safe.
#
# 2. Add a DATE parameter to filter corpus rows before a certain year
#    (use bigquery-public-data.samples.natality or similar dated dataset).
#
# 3. Wrap query_by_word() in a simple CLI using argparse so you can run:
#    python ex02_parameterized_query.py --word "sword"
