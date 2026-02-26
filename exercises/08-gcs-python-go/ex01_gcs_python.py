"""
Exercise 01 — Cloud Storage: Upload, Download, List, Signed URLs (Python)
--------------------------------------------------------------------------
Goal:
    - Upload files and in-memory data to GCS
    - Download blobs (streaming and fully buffered)
    - List blobs with prefix filtering (like S3 ListObjects)
    - Generate time-limited signed URLs for unauthenticated access
    - Copy and delete blobs

Interview relevance:
    "How do you move data from on-prem to BigQuery?"
    → Usually: local → GCS (this exercise) → BQ Load Job (ex03 in BQ category)
    "How do you expose GCS objects to an external partner without giving them IAM?"
    → Signed URLs

Setup:
    pip install google-cloud-storage
    export GOOGLE_CLOUD_PROJECT=your-project-id
    export BUCKET_NAME=your-bucket-name
"""

import os
import io
import json
import datetime
from pathlib import Path
from typing import Optional, Iterator

from google.cloud import storage
from google.cloud.storage import Blob, Bucket


# ---------------------------------------------------------------------------
# Helper: get client and bucket
# ---------------------------------------------------------------------------
def get_client() -> storage.Client:
    """Create and return a GCS client using Application Default Credentials."""
    return storage.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT"))


def get_bucket(client: storage.Client, bucket_name: Optional[str] = None) -> Bucket:
    """Return a Bucket object. Does not create the bucket."""
    bucket_name = bucket_name or os.environ["BUCKET_NAME"]
    return client.bucket(bucket_name)


# ---------------------------------------------------------------------------
# EXERCISE 1: Upload files and in-memory data
# ---------------------------------------------------------------------------

def upload_from_file(bucket: Bucket, local_path: str, destination_blob: str) -> Blob:
    """
    Upload a local file to GCS.
    Equivalent to: gsutil cp local_file gs://bucket/destination
    """
    blob = bucket.blob(destination_blob)

    # TODO: Use blob.upload_from_filename(local_path)
    blob.upload_from_filename(local_path)

    print(f"Uploaded {local_path} → gs://{bucket.name}/{destination_blob}")
    return blob


def upload_from_memory(bucket: Bucket, data: bytes | str, destination_blob: str,
                        content_type: str = "application/octet-stream") -> Blob:
    """
    Upload in-memory data to GCS without creating a local file.
    Useful for: generated reports, API responses, config files.
    """
    blob = bucket.blob(destination_blob)

    if isinstance(data, str):
        data = data.encode("utf-8")

    # TODO: Use blob.upload_from_string(data, content_type=content_type)
    blob.upload_from_string(data, content_type=content_type)

    print(f"Uploaded {len(data)} bytes → gs://{bucket.name}/{destination_blob}")
    return blob


def upload_json_object(bucket: Bucket, obj: dict, destination_blob: str) -> Blob:
    """Upload a Python dict as a JSON blob."""
    json_bytes = json.dumps(obj, indent=2).encode("utf-8")
    return upload_from_memory(bucket, json_bytes, destination_blob,
                               content_type="application/json")


# ---------------------------------------------------------------------------
# EXERCISE 2: Download blobs
# ---------------------------------------------------------------------------

def download_to_file(bucket: Bucket, blob_name: str, local_path: str) -> None:
    """Download a GCS blob to a local file."""
    blob = bucket.blob(blob_name)

    # TODO: Use blob.download_to_filename(local_path)
    blob.download_to_filename(local_path)

    print(f"Downloaded gs://{bucket.name}/{blob_name} → {local_path}")


def download_to_memory(bucket: Bucket, blob_name: str) -> bytes:
    """
    Download a GCS blob into memory as bytes.
    Use for: small files, configs, metadata you need to process inline.
    """
    blob = bucket.blob(blob_name)

    # TODO: Use blob.download_as_bytes()
    data = blob.download_as_bytes()

    print(f"Downloaded {len(data)} bytes from gs://{bucket.name}/{blob_name}")
    return data


def download_as_text(bucket: Bucket, blob_name: str, encoding: str = "utf-8") -> str:
    """Download a GCS blob as a decoded string."""
    return download_to_memory(bucket, blob_name).decode(encoding)


def stream_download(bucket: Bucket, blob_name: str, chunk_size: int = 8 * 1024 * 1024) -> Iterator[bytes]:
    """
    Stream a large blob in chunks to avoid loading it all into memory.
    chunk_size default: 8 MiB.
    Use for: large CSV/Parquet files that are too big to hold in RAM.
    """
    blob = bucket.blob(blob_name)
    blob.chunk_size = chunk_size  # Set resumable download chunk size

    buffer = io.BytesIO()
    blob.download_to_file(buffer)
    buffer.seek(0)

    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk
        print(f"  → yielded {len(chunk)} bytes chunk")


# ---------------------------------------------------------------------------
# EXERCISE 3: List blobs
# ---------------------------------------------------------------------------

def list_blobs(bucket: Bucket, prefix: Optional[str] = None,
               delimiter: Optional[str] = None) -> list[str]:
    """
    List blob names in a bucket, optionally filtered by prefix.

    prefix:    like a folder path — "data/2024/"
    delimiter: "/" simulates a directory listing (only shows items at this level)
    """
    client = bucket.client

    # TODO: Use client.list_blobs(bucket.name, prefix=prefix, delimiter=delimiter)
    blobs = client.list_blobs(bucket.name, prefix=prefix, delimiter=delimiter)

    names = [blob.name for blob in blobs]

    if delimiter:
        # blobs.prefixes contains "sub-directories" (virtual folders)
        # Note: must iterate blobs first to populate blobs.prefixes
        blobs = client.list_blobs(bucket.name, prefix=prefix, delimiter=delimiter)
        list(blobs)  # Exhaust iterator to populate prefixes
        print(f"Sub-prefixes (virtual folders): {list(blobs.prefixes)}")

    print(f"Found {len(names)} blobs" + (f" with prefix '{prefix}'" if prefix else ""))
    return names


def list_blob_metadata(bucket: Bucket, prefix: Optional[str] = None) -> list[dict]:
    """Return blob metadata: name, size, content_type, updated timestamp."""
    client = bucket.client
    return [
        {
            "name":         blob.name,
            "size_bytes":   blob.size,
            "content_type": blob.content_type,
            "updated":      blob.updated.isoformat() if blob.updated else None,
            "storage_class":blob.storage_class,
        }
        for blob in client.list_blobs(bucket.name, prefix=prefix)
    ]


# ---------------------------------------------------------------------------
# EXERCISE 4: Copy and delete blobs
# ---------------------------------------------------------------------------

def copy_blob(source_bucket: Bucket, source_blob_name: str,
              dest_bucket: Bucket, dest_blob_name: str) -> Blob:
    """
    Server-side copy: data moves within GCS without downloading to client.
    Equivalent to: gsutil cp gs://src/file gs://dst/file
    """
    source_blob = source_bucket.blob(source_blob_name)

    # TODO: Use bucket.copy_blob(blob, dest_bucket, dest_blob_name)
    dest_blob = source_bucket.copy_blob(source_blob, dest_bucket, dest_blob_name)

    print(f"Copied gs://{source_bucket.name}/{source_blob_name} "
          f"→ gs://{dest_bucket.name}/{dest_blob_name}")
    return dest_blob


def delete_blob(bucket: Bucket, blob_name: str) -> None:
    """Delete a single blob. Raises google.api_core.exceptions.NotFound if missing."""
    blob = bucket.blob(blob_name)

    # TODO: Use blob.delete()
    blob.delete()

    print(f"Deleted gs://{bucket.name}/{blob_name}")


def delete_blobs_by_prefix(bucket: Bucket, prefix: str) -> int:
    """Delete all blobs matching a prefix. Returns count deleted."""
    client = bucket.client
    blobs = list(client.list_blobs(bucket.name, prefix=prefix))

    if not blobs:
        print(f"No blobs found with prefix '{prefix}'")
        return 0

    # Batch delete is more efficient than individual deletes
    # TODO: Use client.batch() context manager for bulk deletes
    with client.batch():
        for blob in blobs:
            blob.delete()

    print(f"Deleted {len(blobs)} blobs with prefix '{prefix}'")
    return len(blobs)


# ---------------------------------------------------------------------------
# EXERCISE 5: Signed URLs (unauthenticated time-limited access)
# ---------------------------------------------------------------------------

def generate_signed_url_v4(bucket: Bucket, blob_name: str,
                             expiration_minutes: int = 60,
                             method: str = "GET") -> str:
    """
    Generate a V4 signed URL for temporary unauthenticated access.

    Use cases:
      - Share a file with a partner without giving them IAM
      - Allow a browser to upload directly to GCS (PUT method)
      - Pre-signed download links in a web app

    Requires a service account key file OR Workload Identity Federation.
    Set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON key.
    """
    blob = bucket.blob(blob_name)

    # TODO: Use blob.generate_signed_url(expiration, method, version)
    url = blob.generate_signed_url(
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method=method,
        version="v4",
    )

    print(f"Signed URL ({method}, expires {expiration_minutes}m): {url[:80]}...")
    return url


def generate_upload_signed_url(bucket: Bucket, blob_name: str,
                                expiration_minutes: int = 15) -> str:
    """
    Generate a PUT signed URL so a client can upload directly to GCS.
    The client's browser never needs GCP credentials.
    """
    return generate_signed_url_v4(bucket, blob_name, expiration_minutes, method="PUT")


# ---------------------------------------------------------------------------
# EXERCISE 6: Blob metadata and custom attributes
# ---------------------------------------------------------------------------

def set_blob_metadata(bucket: Bucket, blob_name: str, metadata: dict) -> None:
    """
    Set custom metadata on a blob (key-value pairs stored alongside the object).
    Metadata is returned in every list/get call — keep it small.
    """
    blob = bucket.blob(blob_name)
    blob.metadata = metadata

    # TODO: Use blob.patch() to update metadata without re-uploading the object
    blob.patch()

    print(f"Set metadata on gs://{bucket.name}/{blob_name}: {metadata}")


def get_blob_metadata(bucket: Bucket, blob_name: str) -> dict:
    """Fetch all metadata for a blob (size, content_type, custom metadata, etc.)."""
    blob = bucket.blob(blob_name)

    # TODO: Use blob.reload() to fetch current server state
    blob.reload()

    return {
        "name":           blob.name,
        "bucket":         blob.bucket.name,
        "size":           blob.size,
        "content_type":   blob.content_type,
        "storage_class":  blob.storage_class,
        "generation":     blob.generation,
        "md5_hash":       blob.md5_hash,
        "created":        blob.time_created.isoformat() if blob.time_created else None,
        "updated":        blob.updated.isoformat() if blob.updated else None,
        "custom_metadata": blob.metadata,
    }


# ---------------------------------------------------------------------------
# Main — run all exercises in sequence
# ---------------------------------------------------------------------------

def main():
    client = get_client()
    bucket = get_bucket(client)

    # 1. Upload
    upload_from_memory(bucket, b"Hello, GCS!", "exercises/hello.txt",
                        content_type="text/plain")
    upload_json_object(bucket, {"key": "value", "num": 42}, "exercises/sample.json")

    # 2. Download
    text = download_as_text(bucket, "exercises/hello.txt")
    print(f"Downloaded text: {text!r}")

    data = download_to_memory(bucket, "exercises/sample.json")
    obj = json.loads(data)
    print(f"Downloaded JSON: {obj}")

    # 3. List
    names = list_blobs(bucket, prefix="exercises/")
    print(f"Blobs: {names}")

    # 4. Metadata
    set_blob_metadata(bucket, "exercises/hello.txt", {"owner": "dev-team", "env": "test"})
    meta = get_blob_metadata(bucket, "exercises/hello.txt")
    print(f"Metadata: {json.dumps(meta, indent=2)}")

    # 5. Copy
    copy_blob(bucket, "exercises/hello.txt", bucket, "exercises/hello-copy.txt")

    # 6. Delete
    delete_blob(bucket, "exercises/hello-copy.txt")
    count = delete_blobs_by_prefix(bucket, "exercises/")
    print(f"Final cleanup: deleted {count} blobs")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Implement a resumable upload using blob.open("wb") — required for files > 5 GiB:
#    with bucket.blob("large.csv").open("wb") as f:
#        for chunk in read_large_file_in_chunks("local_large.csv"):
#            f.write(chunk)
#
# 2. Enable object versioning on the bucket via the Python SDK:
#    bucket.versioning_enabled = True
#    bucket.patch()
#    Then upload the same blob twice and list all versions.
#
# 3. Set an object lifecycle rule programmatically:
#    bucket.add_lifecycle_delete_rule(age=30)
#    bucket.patch()
#
# 4. Implement a "GCS directory sync":
#    sync_to_gcs(local_dir, bucket, gcs_prefix) — upload only files that are
#    newer than the GCS version (compare modification time vs blob.updated).
