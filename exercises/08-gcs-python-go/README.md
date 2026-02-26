# Category 08 — Cloud Storage (Python + Go)

## What you will practice

| File                | Language | Topics                                                        |
|---------------------|----------|---------------------------------------------------------------|
| `ex01_gcs_python.py`| Python   | Upload, download, list, copy, delete, signed URLs, metadata   |
| `ex01_gcs_go.go`    | Go       | Same operations using `cloud.google.com/go/storage`           |

---

## GCS Concepts Cheat Sheet

| Concept            | Description                                                      |
|--------------------|------------------------------------------------------------------|
| **Bucket**         | Container for objects; globally unique name                      |
| **Object (Blob)**  | File stored in a bucket; immutable once written                  |
| **Prefix**         | Simulated folder path (`data/2024/`) — GCS has no real folders   |
| **Signed URL**     | Time-limited URL for unauthenticated access to a specific object |
| **CMEK**           | Customer-Managed Encryption Key via Cloud KMS                    |
| **Lifecycle Rule** | Auto-transition or delete objects by age or storage class        |
| **Versioning**     | Keep previous object versions on overwrite/delete                |
| **Uniform Access** | Disable per-object ACLs — use bucket-level IAM only              |

---

## Storage Class Cost Guide

| Class      | $/GB/month | Min storage | Retrieval cost | Use case                        |
|------------|------------|-------------|----------------|---------------------------------|
| STANDARD   | $0.020     | None        | Free           | Hot data, frequent access       |
| NEARLINE   | $0.010     | 30 days     | $0.01/GB       | Accessed < once/month           |
| COLDLINE   | $0.004     | 90 days     | $0.02/GB       | Accessed < once/quarter         |
| ARCHIVE    | $0.0012    | 365 days    | $0.05/GB       | Disaster recovery, compliance   |

---

## Setup

### Python
```bash
pip install google-cloud-storage
export GOOGLE_CLOUD_PROJECT=your-project-id
export BUCKET_NAME=your-bucket-name
python ex01_gcs_python.py
```

### Go
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export BUCKET_NAME=your-bucket-name
go mod tidy
go run ex01_gcs_go.go
```

---

## Interview One-Liners

- **GCS vs S3?** Both object stores. GCS has stronger consistency (always strongly consistent), uniform bucket-level IAM, and native BigQuery integration.

- **How do you serve a file from GCS to a browser without making the bucket public?**
  Generate a V4 signed URL with `GET` method and a short expiration.

- **How do you allow a web app to upload directly to GCS without proxying?**
  Generate a signed URL with `PUT` method and `Content-Type` restriction.

- **What is the cheapest way to store 100 TB of logs you access once a year?**
  ARCHIVE storage class (~$120/month vs $2,000 for STANDARD).
