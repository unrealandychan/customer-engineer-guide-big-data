"""
Exercise 01 — Apache Beam Pipeline: Batch + Streaming on Dataflow
------------------------------------------------------------------
Goal:
    - Understand the Beam programming model (PCollection, PTransform, Pipeline)
    - Build a batch pipeline: read CSV → transform → write to BigQuery
    - Build a streaming pipeline: read from Pub/Sub → window → write to BigQuery
    - Run locally with DirectRunner, deploy to Dataflow with DataflowRunner

Interview relevance:
    "What is Apache Beam and how does Dataflow relate to it?"
    Beam = the programming model (write once).
    Dataflow = Google's managed, serverless runner for Beam.

Setup:
    pip install apache-beam[gcp]
    export GOOGLE_CLOUD_PROJECT=your-project-id

Run locally (DirectRunner):
    python ex01_beam_pipeline.py --runner DirectRunner

Run on Dataflow:
    python ex01_beam_pipeline.py \
        --runner DataflowRunner \
        --project your-project-id \
        --region us-central1 \
        --temp_location gs://your-bucket/temp/ \
        --staging_location gs://your-bucket/staging/
"""

import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
from apache_beam.transforms.window import FixedWindows, SlidingWindows
from apache_beam.transforms.trigger import AfterWatermark, AfterCount, AccumulationMode


# ---------------------------------------------------------------------------
# BigQuery table schema — used for the output table
# ---------------------------------------------------------------------------
BQ_SCHEMA = {
    "fields": [
        {"name": "event_type",   "type": "STRING",  "mode": "NULLABLE"},
        {"name": "country",      "type": "STRING",  "mode": "NULLABLE"},
        {"name": "event_count",  "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "total_amount", "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "window_start", "type": "STRING",  "mode": "NULLABLE"},
    ]
}


# ---------------------------------------------------------------------------
# Custom PTransforms (reusable pipeline components)
# ---------------------------------------------------------------------------

class ParseEventCSV(beam.DoFn):
    """
    Parse a CSV line into a structured event dict.
    DoFn = "Do Function" — the core unit of user code in Beam.
    Extend beam.DoFn and implement process(self, element).
    """
    def process(self, element: str):
        """
        Called once per element in the PCollection.
        Yield output elements (can yield 0, 1, or many per input).
        """
        try:
            parts = element.strip().split(",")
            if len(parts) < 6 or parts[0] == "event_id":  # Skip header
                return
            yield {
                "event_id":   parts[0],
                "event_date": parts[1],
                "event_type": parts[2],
                "country":    parts[3],
                "user_id":    parts[4],
                "amount":     float(parts[5]) if parts[5] else 0.0,
            }
        except Exception as e:
            # TODO: Use beam.metrics to count parse errors
            logging.warning(f"Parse error: {e} for line: {element}")


class FilterNullAmounts(beam.DoFn):
    """
    Filter out events with zero or negative amounts.
    Demonstrates conditional yield in a DoFn.
    """
    def process(self, element: Dict[str, Any]):
        if element.get("amount", 0) > 0:
            yield element
        # Implicitly drop rows with amount <= 0


class AddProcessingTimestamp(beam.DoFn):
    """
    Enrich each event with the processing timestamp.
    Shows how to add derived fields in a DoFn.
    """
    def process(self, element: Dict[str, Any]):
        element["processed_at"] = datetime.utcnow().isoformat()
        yield element


# ---------------------------------------------------------------------------
# EXERCISE 1a: Batch pipeline — CSV → BigQuery
# ---------------------------------------------------------------------------
def run_batch_pipeline(argv=None) -> None:
    """
    A simple batch Beam pipeline:
      Read CSV from GCS → Parse → Filter → Aggregate → Write to BigQuery

    Key Beam concepts:
      pipeline | "label" >> Transform  (pipe operator chains transforms)
      PCollection = distributed, immutable, unordered dataset
      PTransform = operation applied to a PCollection
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",   required=True, help="GCS path to input CSV")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--dataset", default="beam_exercises")
    parser.add_argument("--table",   default="event_aggregates")
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=options) as p:
        # Step 1: Read raw lines from GCS
        # TODO: Use beam.io.ReadFromText(known_args.input)
        raw_lines = (
            p
            | "ReadCSV" >> beam.io.ReadFromText(known_args.input)
        )

        # Step 2: Parse CSV lines into dicts
        # TODO: Apply ParseEventCSV DoFn using beam.ParDo
        events = (
            raw_lines
            | "ParseCSV"    >> beam.ParDo(ParseEventCSV())
            | "FilterNulls" >> beam.ParDo(FilterNullAmounts())
        )

        # Step 3: Aggregate — count events and sum amounts per (event_type, country)
        # TODO: Use beam.Map to create a key-value pair, then beam.GroupByKey or CombinePerKey
        aggregated = (
            events
            | "KeyByTypeCountry" >> beam.Map(
                lambda e: ((e["event_type"], e["country"]), e["amount"])
            )
            | "SumAmounts" >> beam.CombinePerKey(sum)
            | "FormatOutput" >> beam.Map(lambda kv: {
                "event_type":   kv[0][0],
                "country":      kv[0][1],
                "total_amount": kv[1],
                "event_count":  1,        # NOTE: CombinePerKey with sum loses count
                "window_start": "batch",  # Not windowed in batch mode
            })
        )

        # Step 4: Write to BigQuery
        # TODO: Use WriteToBigQuery with WRITE_TRUNCATE and CREATE_IF_NEEDED
        _ = (
            aggregated
            | "WriteToBQ" >> WriteToBigQuery(
                table=f"{known_args.project}:{known_args.dataset}.{known_args.table}",
                schema=BQ_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

    print("Batch pipeline complete.")


# ---------------------------------------------------------------------------
# EXERCISE 1b: Streaming pipeline — Pub/Sub → window → BigQuery
# ---------------------------------------------------------------------------
def run_streaming_pipeline(argv=None) -> None:
    """
    A streaming Beam pipeline:
      Pub/Sub → Parse JSON → Assign event time → Window → Aggregate → BigQuery

    Key Beam streaming concepts:
      - Watermark: how far behind event time processing is allowed to lag
      - Window: group elements by time range for aggregation
      - Trigger: when to emit windowed results (before watermark, after count, etc.)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription", required=True,
                        help="Pub/Sub subscription path: projects/P/subscriptions/S")
    parser.add_argument("--project",  required=True)
    parser.add_argument("--dataset",  default="beam_exercises")
    parser.add_argument("--table",    default="streaming_aggregates")
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    options.view_as(StandardOptions).streaming = True  # REQUIRED for streaming

    with beam.Pipeline(options=options) as p:
        # Step 1: Read from Pub/Sub
        # TODO: Use beam.io.ReadFromPubSub(subscription=...) with timestamp_attribute
        messages = (
            p
            | "ReadPubSub" >> beam.io.ReadFromPubSub(
                subscription=known_args.subscription,
                timestamp_attribute=None,   # Use processing time (no event-time attribute)
            )
        )

        # Step 2: Parse JSON messages
        def parse_pubsub_message(message_bytes: bytes) -> Dict[str, Any]:
            try:
                return json.loads(message_bytes.decode("utf-8"))
            except Exception:
                return {}

        events = (
            messages
            | "ParseJSON"   >> beam.Map(parse_pubsub_message)
            | "FilterEmpty" >> beam.Filter(lambda e: e.get("event_type"))
        )

        # Step 3: Apply a fixed 1-minute window
        # TODO: Use beam.WindowInto(FixedWindows(60))
        windowed_events = (
            events
            | "ApplyWindow" >> beam.WindowInto(
                FixedWindows(60),  # 60-second tumbling windows
                trigger=AfterWatermark(
                    early=AfterCount(10)   # Emit early result after 10 events
                ),
                accumulation_mode=AccumulationMode.DISCARDING,
            )
        )

        # Step 4: Aggregate within each window
        aggregated = (
            windowed_events
            | "KeyByType"  >> beam.Map(lambda e: (e.get("event_type", "unknown"), e.get("amount", 0)))
            | "SumPerType" >> beam.CombinePerKey(sum)
            | "Format"     >> beam.Map(lambda kv: {
                "event_type":   kv[0],
                "country":      "ALL",
                "total_amount": kv[1],
                "event_count":  1,
                "window_start": datetime.utcnow().isoformat(),
            })
        )

        # Step 5: Write to BigQuery (streaming insert)
        _ = (
            aggregated
            | "WriteToBQ" >> WriteToBigQuery(
                table=f"{known_args.project}:{known_args.dataset}.{known_args.table}",
                schema=BQ_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

    # In streaming mode, the pipeline runs until manually stopped
    print("Streaming pipeline submitted. Running until cancelled...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    if "--subscription" in sys.argv:
        run_streaming_pipeline()
    else:
        run_batch_pipeline()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Add Beam metrics to count parse errors:
#    self.parse_errors = Metrics.counter(self.__class__, 'parse_errors')
#    self.parse_errors.inc() in the except block of ParseEventCSV.
#    View metrics in the Dataflow UI or locally in pipeline result.
#
# 2. Change FixedWindows(60) to SlidingWindows(120, 60):
#    - Window size: 2 minutes, slide every 1 minute
#    - How many windows does a single event appear in?
#
# 3. Add a side input: load a country → region mapping from GCS as a dict,
#    and use it in AddProcessingTimestamp to add a "region" field.
#    beam.pvalue.AsSingleton() is the pattern for side inputs.
#
# 4. Replace CombinePerKey(sum) with a custom CombineFn that tracks
#    both count and sum simultaneously, so you can compute average.
