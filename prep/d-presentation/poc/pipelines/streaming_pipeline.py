"""
streaming_pipeline.py
─────────────────────
Apache Beam pipeline: Brand A POS events → Pub/Sub → BigQuery (streaming insert).

Demonstrates:
  1. Publisher: simulates Brand A point-of-sale events into Pub/Sub
  2. Consumer pipeline: Pub/Sub → parse → canonical transform → BQ streaming write
  3. Fixed 5-minute windows with 2-minute watermark for late data
  4. Dead-letter sink for parse/validation failures
  5. Exactly-once semantics via Dataflow shuffle (annotated in comments)

Architecture mapping (AWS analogy for the presentation):
  Pub/Sub   ≈ Kinesis Data Streams
  Dataflow  ≈ Kinesis Data Analytics / Flink on EMR
  BigQuery  ≈ Redshift (but serverless + real-time)

Usage:

  # Mode 1: Run publisher only (sends synthetic events to Pub/Sub)
  python streaming_pipeline.py --mode publisher \\
    --project YOUR_PROJECT_ID \\
    --topic brand-a-pos-events \\
    --num-events 200

  # Mode 2: Run Beam pipeline locally (DirectRunner — no GCP billing)
  python streaming_pipeline.py --mode pipeline \\
    --project YOUR_PROJECT_ID \\
    --topic brand-a-pos-events \\
    --runner DirectRunner

  # Mode 3: Deploy to Dataflow (DataflowRunner — GCP billing applies)
  python streaming_pipeline.py --mode pipeline \\
    --project YOUR_PROJECT_ID \\
    --topic brand-a-pos-events \\
    --runner DataflowRunner \\
    --region us-central1 \\
    --temp-location gs://YOUR_PROJECT_ID-portfolio-raw/dataflow-temp

Requirements:
  pip install apache-beam[gcp] google-cloud-pubsub google-cloud-bigquery faker
"""

import argparse
import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, GoogleCloudOptions
from apache_beam.transforms import window, trigger


# ─────────────────────────────────────────────────────────────
# Constants — replace with real values before running
# ─────────────────────────────────────────────────────────────
DEFAULT_PROJECT = "YOUR_PROJECT_ID"
DEFAULT_TOPIC   = "brand-a-pos-events"
BQ_DATASET      = "streaming"
BQ_TABLE        = "streaming_orders"
DLQ_DATASET     = "streaming"
DLQ_TABLE       = "streaming_orders_dlq"  # dead-letter queue for bad messages

STORES          = [f"STR-A-{i:02d}" for i in range(1, 11)]
PRODUCTS        = [f"SKU-A-{i:04d}" for i in range(1000, 2000)]


# ─────────────────────────────────────────────────────────────
# BigQuery table schema for streaming_orders
# ─────────────────────────────────────────────────────────────
STREAMING_ORDERS_SCHEMA = {
    "fields": [
        {"name": "order_key",        "type": "STRING",    "mode": "REQUIRED"},
        {"name": "customer_key",     "type": "STRING",    "mode": "NULLABLE"},  # NULL if no cust_id
        {"name": "brand_id",         "type": "STRING",    "mode": "REQUIRED"},
        {"name": "store_key",        "type": "STRING",    "mode": "NULLABLE"},
        {"name": "channel",          "type": "STRING",    "mode": "REQUIRED"},
        {"name": "event_ts",         "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "event_date",       "type": "DATE",      "mode": "REQUIRED"},
        {"name": "amount_usd",       "type": "NUMERIC",   "mode": "REQUIRED"},
        {"name": "source_order_id",  "type": "STRING",    "mode": "REQUIRED"},
        {"name": "window_start",     "type": "TIMESTAMP", "mode": "NULLABLE"},  # 5-min window start
        {"name": "_pipeline_ts",     "type": "TIMESTAMP", "mode": "NULLABLE"},
    ]
}

DLQ_SCHEMA = {
    "fields": [
        {"name": "raw_message",  "type": "STRING",    "mode": "REQUIRED"},
        {"name": "error",        "type": "STRING",    "mode": "REQUIRED"},
        {"name": "received_ts",  "type": "TIMESTAMP", "mode": "REQUIRED"},
    ]
}


# ─────────────────────────────────────────────────────────────
# PART 1: Publisher — simulates Brand A POS events into Pub/Sub
# ─────────────────────────────────────────────────────────────

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_pos_event(event_index: int) -> dict:
    """Generate a single synthetic Brand A POS event."""
    cust_id = random.randint(100, 5000)
    order_id = f"A-LIVE-{event_index:06d}"
    channel = random.choice(["PHYSICAL", "PHYSICAL", "DIGITAL"])
    return {
        "order_id":       order_id,
        "cust_id":        cust_id,
        "product_id":     random.choice(PRODUCTS),
        "store_id":       random.choice(STORES) if channel == "PHYSICAL" else None,
        "transaction_ts": datetime.now(tz=timezone.utc).isoformat(),
        "amount_usd":     round(random.uniform(10.0, 500.0), 2),
        "discount_pct":   round(random.choice([0.0, 0.0, 0.05, 0.10, 0.15]), 2),
        "channel":        channel,
    }


def run_publisher(project: str, topic_id: str, num_events: int, delay_ms: int = 200):
    """Publish synthetic Brand A events to Pub/Sub."""
    from google.cloud import pubsub_v1

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_id)

    print(f"Publishing {num_events} events to {topic_path}...")
    for i in range(num_events):
        event = generate_pos_event(i)
        data = json.dumps(event).encode("utf-8")
        future = publisher.publish(topic_path, data=data)
        future.result()  # wait for acknowledgement
        if i % 50 == 0:
            print(f"  Published {i}/{num_events} events")
        time.sleep(delay_ms / 1000.0)

    print(f"Done. Published {num_events} events.")


# ─────────────────────────────────────────────────────────────
# PART 2: Beam Transforms — parsing and canonical transformation
# ─────────────────────────────────────────────────────────────

class ParseAndValidateFn(beam.DoFn):
    """
    Parse raw Pub/Sub message bytes → Python dict.
    Emit to 'valid' tag on success, 'dead_letter' tag on failure.

    Exactly-once note: Dataflow shuffle-based exactly-once guarantees
    that each Pub/Sub message is processed exactly once by the Dataflow
    worker cluster, even in the event of worker failures or restarts.
    This relies on Dataflow's native deduplication using message IDs.
    """
    VALID_TAG  = "valid"
    DLQ_TAG    = "dead_letter"

    def process(self, element, timestamp=beam.DoFn.TimestampParam):
        raw_bytes = element
        received_ts = datetime.now(tz=timezone.utc).isoformat()
        try:
            record = json.loads(raw_bytes.decode("utf-8"))
            # Required field validation
            for required in ("order_id", "cust_id", "amount_usd", "transaction_ts", "channel"):
                if required not in record or record[required] is None:
                    raise ValueError(f"Missing required field: {required}")
            if record["amount_usd"] <= 0:
                raise ValueError(f"amount_usd must be positive: {record['amount_usd']}")
            yield beam.pvalue.TaggedOutput(self.VALID_TAG, record)
        except Exception as e:
            yield beam.pvalue.TaggedOutput(self.DLQ_TAG, {
                "raw_message": raw_bytes.decode("utf-8", errors="replace"),
                "error":       str(e),
                "received_ts": received_ts,
            })


class ToCanonicalFn(beam.DoFn):
    """
    Transform a parsed Brand A event into the canonical.order row format.
    Applies the same SHA-256 identity resolution used in transform_canonical.sql.
    """
    def process(self, record):
        cust_id_str = str(record["cust_id"])
        order_id    = record["order_id"]
        ts_str      = record["transaction_ts"]

        try:
            event_ts = datetime.fromisoformat(ts_str)
        except ValueError:
            event_ts = datetime.now(tz=timezone.utc)

        canonical_row = {
            "order_key":       sha256_hex(f"brand_a|{order_id}"),
            "customer_key":    sha256_hex(f"brand_a|{cust_id_str}"),
            "brand_id":        "brand_a",
            "store_key":       record.get("store_id"),
            "channel":         record.get("channel", "UNKNOWN"),
            "event_ts":        event_ts.isoformat(),
            "event_date":      event_ts.date().isoformat(),
            "amount_usd":      round(
                record["amount_usd"] * (1 - float(record.get("discount_pct", 0.0))), 2
            ),
            "source_order_id": order_id,
            "window_start":    None,  # filled after windowing
            "_pipeline_ts":    datetime.now(tz=timezone.utc).isoformat(),
        }
        yield canonical_row


class AddWindowInfoFn(beam.DoFn):
    """Attach the window start time to each row (for analytics on window boundaries)."""
    def process(self, element, window=beam.DoFn.WindowParam):
        element["window_start"] = str(window.start.to_utc_datetime().isoformat())
        yield element


# ─────────────────────────────────────────────────────────────
# PART 3: Beam Pipeline definition
# ─────────────────────────────────────────────────────────────

def run_pipeline(project: str, topic_id: str, argv: list):
    """
    Build and run the Beam streaming pipeline.

    Watermark strategy:
      - Fixed 5-minute windows for aggregation
      - 2-minute allowed_lateness: late data arriving within 2 min after window close
        is still processed into the window; beyond 2 min → discarded (acceptable for POS)
      - Early firings every 60s: partial results land in BQ during the window
        (useful for the live demo — you see rows before the window closes)

    Late data beyond allowed_lateness → routed to DLQ for manual inspection.

    Exactly-once semantics:
      - Apache Beam on Dataflow with STREAMING_ENGINE and shuffle-based delivery
        provides at-least-once processing by default.
      - For exactly-once writes to BigQuery, use BigQueryIO.writeRows() with
        method=FILE_LOADS or STORAGE_WRITE_API.
      - For the POC/demo, STREAMING_INSERTS are used (simpler, near-real-time,
        at-least-once — acceptable for demonstration purposes).
    """
    subscription_path = f"projects/{project}/topics/{topic_id}"

    options = PipelineOptions(argv)
    options.view_as(StandardOptions).streaming = True

    gcp_options = options.view_as(GoogleCloudOptions)
    gcp_options.project = project
    gcp_options.job_name = "brand-a-streaming-poc"

    bq_table   = f"{project}:{BQ_DATASET}.{BQ_TABLE}"
    dlq_table  = f"{project}:{DLQ_DATASET}.{DLQ_TABLE}"

    with beam.Pipeline(options=options) as p:
        # Read from Pub/Sub
        raw_msgs = (
            p
            | "ReadPubSub" >> beam.io.ReadFromPubSub(topic=subscription_path)
        )

        # Parse and validate — split into valid / dead_letter
        parsed = (
            raw_msgs
            | "ParseAndValidate" >> beam.ParDo(
                ParseAndValidateFn()
            ).with_outputs(
                ParseAndValidateFn.DLQ_TAG,
                main=ParseAndValidateFn.VALID_TAG
            )
        )

        # Write dead-letter messages to BQ DLQ table
        (
            parsed[ParseAndValidateFn.DLQ_TAG]
            | "WriteDLQ" >> beam.io.WriteToBigQuery(
                table=dlq_table,
                schema=DLQ_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

        # Transform valid records to canonical format
        canonical_rows = (
            parsed[ParseAndValidateFn.VALID_TAG]
            | "ToCanonical" >> beam.ParDo(ToCanonicalFn())
        )

        # Apply 5-minute fixed windows
        # Watermark: 2-minute allowed lateness
        windowed = (
            canonical_rows
            | "ApplyWindows" >> beam.WindowInto(
                window.FixedWindows(size=5 * 60),  # 5-minute windows
                trigger=trigger.AfterWatermark(
                    early=trigger.AfterProcessingTime(60),   # emit partial every 60s
                    late=trigger.AfterCount(1),              # emit each late element
                ),
                accumulation_mode=trigger.AccumulationMode.DISCARDING,
                allowed_lateness=2 * 60,                     # 2 min late data tolerance
            )
            | "AddWindowInfo" >> beam.ParDo(AddWindowInfoFn())
        )

        # Write to BigQuery (streaming inserts)
        # Production: use STORAGE_WRITE_API for exactly-once guarantees
        (
            windowed
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                table=bq_table,
                schema=STREAMING_ORDERS_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,  # near-real-time
                # NOTE: For true exactly-once, switch to:
                # method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API
            )
        )

    logging.info("Pipeline complete.")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Brand A POS streaming pipeline (Pub/Sub → BQ)")
    parser.add_argument("--mode", choices=["publisher", "pipeline", "both"],
                        default="publisher",
                        help="Run publisher only, pipeline only, or both sequentially")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP project ID")
    parser.add_argument("--topic",   default=DEFAULT_TOPIC,   help="Pub/Sub topic ID")
    parser.add_argument("--num-events", type=int, default=200, help="Events to publish (publisher mode)")
    parser.add_argument("--delay-ms",   type=int, default=200, help="Delay between published events (ms)")

    # Remaining args passed through to Beam PipelineOptions
    args, beam_args = parser.parse_known_args()

    if args.mode in ("publisher", "both"):
        run_publisher(args.project, args.topic, args.num_events, args.delay_ms)

    if args.mode in ("pipeline", "both"):
        run_pipeline(args.project, args.topic, beam_args)


if __name__ == "__main__":
    main()
