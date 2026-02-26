"""
Exercise 05 — BigQuery Window Functions (Python)
-------------------------------------------------
Goal:
    - Master all major BigQuery window functions via the Python client
    - Understand PARTITION BY vs GROUP BY
    - Use frame clauses (ROWS/RANGE BETWEEN) for running aggregations
    - See real query results using public BigQuery datasets

Interview relevance:
    "How would you compute a 7-day rolling average in BigQuery?"
    "What's the difference between RANK() and DENSE_RANK()?"
    "When would you use window functions instead of a subquery?"

Setup:
    pip install google-cloud-bigquery[pandas]
    export GOOGLE_CLOUD_PROJECT=your-project-id

Note: These queries use bigquery-public-data — no data upload required.
"""

import os
from google.cloud import bigquery


def get_client() -> bigquery.Client:
    return bigquery.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT"))


# ---------------------------------------------------------------------------
# EXERCISE 1: ROW_NUMBER, RANK, DENSE_RANK
#
# Use case: "Find the top-3 words per corpus in Shakespeare's works."
# ---------------------------------------------------------------------------

def demo_ranking_functions(client: bigquery.Client) -> None:
    """
    ROW_NUMBER()  — unique sequential number, no ties
    RANK()        — tied rows get same rank; next rank skips (1,1,3)
    DENSE_RANK()  — tied rows get same rank; next rank does NOT skip (1,1,2)
    NTILE(n)      — divide rows into n buckets (quartiles, deciles)
    """
    query = """
    WITH word_counts AS (
        SELECT
            corpus,
            word,
            SUM(word_count) AS total_count
        FROM `bigquery-public-data.samples.shakespeare`
        GROUP BY corpus, word
    ),
    ranked AS (
        SELECT
            corpus,
            word,
            total_count,
            -- TODO: Add ranking functions below
            ROW_NUMBER() OVER (
                PARTITION BY corpus
                ORDER BY total_count DESC
            ) AS row_num,
            RANK() OVER (
                PARTITION BY corpus
                ORDER BY total_count DESC
            ) AS rnk,
            DENSE_RANK() OVER (
                PARTITION BY corpus
                ORDER BY total_count DESC
            ) AS dense_rnk,
            NTILE(4) OVER (
                PARTITION BY corpus
                ORDER BY total_count DESC
            ) AS quartile   -- 1 = top 25%, 4 = bottom 25%
        FROM word_counts
    )
    SELECT *
    FROM ranked
    WHERE row_num <= 5        -- Top 5 words per corpus
      AND corpus IN ('hamlet', 'macbeth', 'othello')
    ORDER BY corpus, row_num
    """

    df = client.query(query).to_dataframe()
    print("\n=== Ranking Functions ===")
    print(df.to_string(index=False))
    print()
    print("Note: When two words have the same count:")
    print("  RANK skips the next rank (1,1,3)")
    print("  DENSE_RANK does NOT skip (1,1,2)")
    print("  ROW_NUMBER always gives unique values (arbitrary tiebreak)")


# ---------------------------------------------------------------------------
# EXERCISE 2: Aggregate window functions (SUM, AVG, MIN, MAX)
#
# Use case: "For each word in each corpus, show the running total of
#            word counts ordered by count descending."
# ---------------------------------------------------------------------------

def demo_aggregate_window_functions(client: bigquery.Client) -> None:
    """
    SUM() OVER    — running sum
    AVG() OVER    — running average
    COUNT() OVER  — running count

    Frame clause:
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW  → running total
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW          → 7-row moving average
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING → full partition total
    """
    query = """
    WITH monthly_wiki AS (
        SELECT
            EXTRACT(YEAR  FROM datehour) AS yr,
            EXTRACT(MONTH FROM datehour) AS mo,
            SUM(views) AS monthly_views
        FROM `bigquery-public-data.wikipedia.pageviews_2023`
        WHERE wiki = 'en'
          AND title = 'Python_(programming_language)'
          AND datehour >= '2023-01-01'
        GROUP BY yr, mo
        ORDER BY yr, mo
    )
    SELECT
        yr,
        mo,
        monthly_views,
        -- TODO: Running total from start of dataset to current month
        SUM(monthly_views) OVER (
            ORDER BY yr, mo
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_total,
        -- TODO: 3-month moving average
        AVG(monthly_views) OVER (
            ORDER BY yr, mo
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS moving_avg_3mo,
        -- TODO: Percentage of the full-year total
        ROUND(
            monthly_views / SUM(monthly_views) OVER () * 100,
            2
        ) AS pct_of_year_total
    FROM monthly_wiki
    ORDER BY yr, mo
    """

    df = client.query(query).to_dataframe()
    print("\n=== Aggregate Window Functions (Wikipedia pageviews) ===")
    print(df.to_string(index=False))


# ---------------------------------------------------------------------------
# EXERCISE 3: LAG and LEAD — access previous/next row values
#
# Use case: "Compute month-over-month change in Wikipedia pageviews."
# ---------------------------------------------------------------------------

def demo_lag_lead(client: bigquery.Client) -> None:
    """
    LAG(col, offset, default)   → value from N rows BEFORE current row
    LEAD(col, offset, default)  → value from N rows AFTER current row

    Classic use: period-over-period change (MoM, YoY, DoD)
    """
    query = """
    WITH monthly AS (
        SELECT
            EXTRACT(YEAR  FROM datehour) AS yr,
            EXTRACT(MONTH FROM datehour) AS mo,
            SUM(views) AS monthly_views
        FROM `bigquery-public-data.wikipedia.pageviews_2023`
        WHERE wiki = 'en'
          AND title = 'Google'
          AND datehour >= '2023-01-01'
        GROUP BY yr, mo
    )
    SELECT
        yr,
        mo,
        monthly_views,
        -- TODO: Previous month's views
        LAG(monthly_views, 1, 0) OVER (ORDER BY yr, mo) AS prev_month_views,
        -- TODO: Month-over-month change (absolute)
        monthly_views - LAG(monthly_views, 1, 0) OVER (ORDER BY yr, mo) AS mom_change,
        -- TODO: Month-over-month % change
        ROUND(
            SAFE_DIVIDE(
                monthly_views - LAG(monthly_views, 1) OVER (ORDER BY yr, mo),
                LAG(monthly_views, 1) OVER (ORDER BY yr, mo)
            ) * 100,
            2
        ) AS mom_pct_change,
        -- TODO: Next month's views (useful for forecasting validation)
        LEAD(monthly_views, 1) OVER (ORDER BY yr, mo) AS next_month_views
    FROM monthly
    ORDER BY yr, mo
    """

    df = client.query(query).to_dataframe()
    print("\n=== LAG / LEAD — Month-over-Month Change (Google Wikipedia) ===")
    print(df.to_string(index=False))


# ---------------------------------------------------------------------------
# EXERCISE 4: FIRST_VALUE, LAST_VALUE, NTH_VALUE
# ---------------------------------------------------------------------------

def demo_first_last_value(client: bigquery.Client) -> None:
    """
    FIRST_VALUE(col) OVER (...)   → first value in the window frame
    LAST_VALUE(col) OVER (...)    → last value (requires explicit RANGE/ROWS frame!)
    NTH_VALUE(col, n) OVER (...)  → nth value in the window

    IMPORTANT: LAST_VALUE default frame is ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    → Without explicit frame, LAST_VALUE = CURRENT ROW (gotcha!)
    Fix: use ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    """
    query = """
    WITH word_counts AS (
        SELECT
            corpus,
            word,
            SUM(word_count) AS total_count
        FROM `bigquery-public-data.samples.shakespeare`
        WHERE corpus IN ('hamlet', 'macbeth')
        GROUP BY corpus, word
        QUALIFY ROW_NUMBER() OVER (PARTITION BY corpus ORDER BY total_count DESC) <= 10
    )
    SELECT
        corpus,
        word,
        total_count,
        -- Most frequent word in this corpus
        FIRST_VALUE(word) OVER (
            PARTITION BY corpus
            ORDER BY total_count DESC
        ) AS most_frequent_word,
        -- Least frequent word in the top-10 (need full frame!)
        LAST_VALUE(word) OVER (
            PARTITION BY corpus
            ORDER BY total_count DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS least_frequent_word,
        -- 3rd most frequent word
        NTH_VALUE(word, 3) OVER (
            PARTITION BY corpus
            ORDER BY total_count DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS third_most_frequent
    FROM word_counts
    ORDER BY corpus, total_count DESC
    """

    df = client.query(query).to_dataframe()
    print("\n=== FIRST_VALUE / LAST_VALUE / NTH_VALUE ===")
    print(df.to_string(index=False))


# ---------------------------------------------------------------------------
# EXERCISE 5: QUALIFY clause (BigQuery-specific)
#
# QUALIFY filters window function results — like HAVING for aggregates.
# Avoids a subquery wrapping pattern.
# ---------------------------------------------------------------------------

def demo_qualify(client: bigquery.Client) -> None:
    """
    QUALIFY filters rows based on window function result.
    Without QUALIFY you need: SELECT * FROM (... window function ...) WHERE ...

    Use case: "Get only the top-1 word per corpus."
    """
    query = """
    -- Without QUALIFY (verbose):
    -- SELECT * FROM (
    --   SELECT corpus, word, SUM(word_count) AS cnt,
    --          ROW_NUMBER() OVER (PARTITION BY corpus ORDER BY SUM(word_count) DESC) rn
    --   FROM `bigquery-public-data.samples.shakespeare`
    --   GROUP BY corpus, word
    -- ) WHERE rn = 1

    -- With QUALIFY (BigQuery-specific, cleaner):
    SELECT
        corpus,
        word,
        SUM(word_count) AS total_count
    FROM `bigquery-public-data.samples.shakespeare`
    GROUP BY corpus, word
    QUALIFY ROW_NUMBER() OVER (PARTITION BY corpus ORDER BY SUM(word_count) DESC) = 1
    ORDER BY corpus
    """

    df = client.query(query).to_dataframe()
    print("\n=== QUALIFY Clause (deduplicate per group) ===")
    print(df.to_string(index=False))
    print("\nNote: QUALIFY is a BigQuery / Snowflake extension. Standard SQL needs a subquery.")


# ---------------------------------------------------------------------------
# EXERCISE 6: Sessionisation with window functions
#
# Use case: "Group page view events within 30-minute sessions."
# ---------------------------------------------------------------------------

def demo_sessionisation(client: bigquery.Client) -> None:
    """
    Session windows = group events where gap between consecutive events < threshold.
    BigQuery doesn't have native session windows in SQL, but you can simulate them
    with LAG + conditional SUM.

    Pattern:
      1. LAG() to find time since previous event per user
      2. CASE: if gap > threshold, mark as new session (1 else 0)
      3. Cumulative SUM of session markers = session ID
    """
    query = """
    WITH events AS (
        -- Simulate user events (using shakespeare as a stand-in)
        SELECT
            corpus        AS user_id,
            word          AS page,
            word_count    AS gap_seconds,  -- Treat word_count as seconds between events
            ROW_NUMBER() OVER (PARTITION BY corpus ORDER BY word_count DESC) AS seq
        FROM `bigquery-public-data.samples.shakespeare`
        WHERE corpus IN ('hamlet', 'macbeth')
        QUALIFY ROW_NUMBER() OVER (PARTITION BY corpus ORDER BY word_count DESC) <= 20
    ),
    with_lag AS (
        SELECT
            user_id,
            page,
            gap_seconds,
            seq,
            -- Time since previous event for this user
            LAG(gap_seconds, 1, 0) OVER (PARTITION BY user_id ORDER BY seq) AS prev_gap
        FROM events
    ),
    session_markers AS (
        SELECT
            *,
            -- New session if gap > 1800 seconds (30 min) — using 50 here for demo
            IF(prev_gap > 50 OR seq = 1, 1, 0) AS is_new_session
        FROM with_lag
    )
    SELECT
        user_id,
        page,
        seq,
        gap_seconds,
        -- Cumulative sum of session markers = unique session ID per user
        SUM(is_new_session) OVER (
            PARTITION BY user_id
            ORDER BY seq
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS session_id
    FROM session_markers
    ORDER BY user_id, seq
    """

    df = client.query(query).to_dataframe()
    print("\n=== Sessionisation with Window Functions ===")
    print(df.to_string(index=False))
    print("\nSession ID increments each time a 'gap' is detected.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    client = get_client()

    print("Running window function exercises against BigQuery public datasets...")
    print("Each query shows bytes scanned — try to observe caching effects on re-run.\n")

    demo_ranking_functions(client)
    demo_lag_lead(client)
    demo_first_last_value(client)
    demo_qualify(client)
    demo_sessionisation(client)

    # Skipping aggregate window + Wikipedia queries to keep default run fast
    # Uncomment to run:
    # demo_aggregate_window_functions(client)


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Write a query that finds the 7-day rolling average of Wikipedia pageviews
#    for a page of your choice. Use ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.
#
# 2. Use PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ...) — BigQuery's
#    approximate median. How does it differ from AVG?
#
# 3. Rewrite demo_qualify WITHOUT using QUALIFY — use a subquery or CTE instead.
#    Which is more readable? Which is more standard SQL?
#
# 4. Add APPROX_QUANTILES(total_count, 4) to get quartile boundaries without
#    using NTILE (which needs ORDER BY all rows). When would you use each?
