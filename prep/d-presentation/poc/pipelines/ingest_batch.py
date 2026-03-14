"""
ingest_batch.py
───────────────
Generates synthetic retail order data for all 3 brands and writes
Parquet files to Google Cloud Storage (GCS).

Simulates a nightly batch ingestion process in the architecture:
  Brand A (Kinesis events) → GCS landing zone
  Brand B (SAP nightly export) → SFTP drop → GCS landing zone
  Brand C (Shopify webhooks) → GCS event stream

Usage:
  # Generate data and upload to GCS
  python ingest_batch.py --project YOUR_PROJECT_ID --rows 1000

  # Dry-run: write locally only (no GCS upload)
  python ingest_batch.py --dry-run --rows 500

Requirements:
  pip install google-cloud-storage pandas pyarrow faker

GCS Output Structure:
  gs://{PROJECT_ID}-portfolio-raw/brand-a/orders/YYYY-MM-DD/orders.parquet
  gs://{PROJECT_ID}-portfolio-raw/brand-b/orders/YYYY-MM-DD/orders.parquet
  gs://{PROJECT_ID}-portfolio-raw/brand-c/orders/YYYY-MM-DD/orders.parquet
"""

import argparse
import io
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


# ─────────────────────────────────────────────────────────────
# Synthetic data generators
# ─────────────────────────────────────────────────────────────

def random_ts(days_back: int = 90) -> datetime:
    """Return a random UTC timestamp within the last N days."""
    start = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
    return start + timedelta(seconds=random.randint(0, days_back * 86400))


def generate_brand_a(n: int) -> pd.DataFrame:
    """Brand A: integer cust_id, PHYSICAL/DIGITAL channel, discount_pct."""
    stores = [f"STR-A-{i:02d}" for i in range(1, 11)]
    rows = []
    for i in range(n):
        ts = random_ts()
        channel = random.choice(["PHYSICAL", "PHYSICAL", "DIGITAL"])  # skew physical
        rows.append({
            "order_id":       f"A-{ts.year}-{i+1:06d}",
            "cust_id":        random.randint(100, 5000),
            "product_id":     f"SKU-A-{random.randint(1000, 9999)}",
            "store_id":       random.choice(stores) if channel == "PHYSICAL" else None,
            "transaction_ts": ts.isoformat(),
            "amount_usd":     round(random.uniform(10.0, 500.0), 2),
            "discount_pct":   round(random.choice([0.0, 0.0, 0.05, 0.10, 0.15, 0.20]), 2),
            "channel":        channel,
            "_ingestion_ts":  datetime.now(tz=timezone.utc).isoformat(),
            "_source_file":   "synthetic/ingest_batch.py",
        })
    return pd.DataFrame(rows)


def generate_brand_b(n: int) -> pd.DataFrame:
    """Brand B: UUID customer_uuid, SAP-style ord_number, date-only, gross/net split."""
    plants = [f"PLANT-{i:02d}" for i in range(1, 8)]
    # Fixed pool of customers (SAP UUIDs are stable)
    customer_pool = [str(uuid.uuid4()) for _ in range(500)]
    rows = []
    for i in range(n):
        ts = random_ts()
        gross = round(random.uniform(15.0, 600.0), 2)
        net = round(gross * random.uniform(0.85, 0.93), 2)  # 7-15% tax
        currency = random.choice(["USD", "USD", "USD", "CAD"])  # mostly USD
        rows.append({
            "ord_number":     f"{i+1000000:010d}",
            "customer_uuid":  random.choice(customer_pool),
            "sku":            f"MAT-B-{random.randint(100, 999):05d}",
            "location_code":  random.choice(plants),
            "txn_date":       ts.date().isoformat(),
            "gross_amount":   gross,
            "net_amount":     net,
            "currency_code":  currency,
            "_batch_date":    datetime.now(tz=timezone.utc).date().isoformat(),
            "_source_file":   "synthetic/ingest_batch.py",
        })
    return pd.DataFrame(rows)


def generate_brand_c(n: int) -> pd.DataFrame:
    """Brand C: loyalty_number (nullable ~30% NULL for guests), Shopify variant_id."""
    shops = ["SHOP-C-US", "SHOP-C-UK", "SHOP-C-AU"]
    # Fixed loyalty pool — some customers have IDs, ~30% are guests
    loyalty_pool = [f"LYL_{i:04d}" for i in range(1, 800)]
    rows = []
    for i in range(n):
        ts = random_ts()
        is_guest = random.random() < 0.30
        currency = "USD" if "US" in random.choice(shops) else random.choice(["GBP", "AUD"])
        rows.append({
            "transaction_id":    str(random.randint(5000000000, 9999999999)),
            "loyalty_number":    None if is_guest else random.choice(loyalty_pool),
            "variant_id":        f"VARIANT-C-{random.randint(100, 999)}",
            "shop_id":           random.choice(shops),
            "created_at":        ts.isoformat(),
            "subtotal_price":    round(random.uniform(20.0, 350.0), 2),
            "currency":          currency,
            "fulfillment_status": random.choice(["fulfilled", "fulfilled", None, "partial"]),
            "_webhook_ts":        datetime.now(tz=timezone.utc).isoformat(),
            "_source_topic":     "synthetic/ingest_batch.py",
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# GCS upload
# ─────────────────────────────────────────────────────────────

def upload_to_gcs(df: pd.DataFrame, bucket_name: str, gcs_path: str) -> None:
    """Convert DataFrame to Parquet in memory and upload to GCS."""
    from google.cloud import storage  # import here so dry-run doesn't require SDK

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(buffer, content_type="application/octet-stream")
    print(f"  ✓ Uploaded {len(df)} rows → gs://{bucket_name}/{gcs_path}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic retail orders and upload to GCS.")
    parser.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID"),
                        help="GCP project ID")
    parser.add_argument("--rows", type=int, default=1000,
                        help="Number of rows to generate per brand (default: 1000)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Write Parquet files locally only, skip GCS upload")
    args = parser.parse_args()

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    bucket = f"{args.project}-portfolio-raw"

    brands = {
        "brand-a": generate_brand_a(args.rows),
        "brand-b": generate_brand_b(args.rows),
        "brand-c": generate_brand_c(args.rows),
    }

    for brand_name, df in brands.items():
        print(f"\nBrand: {brand_name} ({len(df)} rows)")
        gcs_path = f"{brand_name}/orders/{today}/orders.parquet"

        if args.dry_run:
            local_path = f"/tmp/{brand_name}_orders.parquet"
            df.to_parquet(local_path, index=False)
            print(f"  [DRY RUN] Written locally: {local_path}")
            print(f"  Sample:\n{df.head(3).to_string()}")
        else:
            upload_to_gcs(df, bucket, gcs_path)


if __name__ == "__main__":
    main()
