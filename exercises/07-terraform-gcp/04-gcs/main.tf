##############################################################################
# Exercise 04 — Cloud Storage: Bucket with Lifecycle Rules + IAM
#
# Resources created:
#   - google_storage_bucket              : bucket with versioning + lifecycle
#   - google_storage_bucket_iam_member   : uniform bucket-level access IAM
#   - google_storage_bucket_object       : upload a sample object
#
# Key interview topics:
#   - Versioning: keep previous object versions
#   - Lifecycle rules: auto-transition or delete objects by age/storage class
#   - Storage classes: STANDARD → NEARLINE → COLDLINE → ARCHIVE
#   - Uniform bucket-level access: disables legacy ACLs (recommended)
#   - CMEK: Customer-managed encryption keys via Cloud KMS
#
# Usage:
#   terraform init
#   terraform plan  -var="project_id=YOUR_PROJECT"
#   terraform apply -var="project_id=YOUR_PROJECT"
##############################################################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "bucket_name" {
  description = "Globally unique bucket name"
  type        = string
  default     = ""  # Will be computed if empty
}

variable "reader_sa_email" {
  description = "SA email to grant objectViewer"
  type        = string
  default     = ""
}

variable "writer_sa_email" {
  description = "SA email to grant objectCreator"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Locals — computed values
# ---------------------------------------------------------------------------
locals {
  # If no bucket name provided, generate one from project + random suffix
  effective_bucket_name = var.bucket_name != "" ? var.bucket_name : "${var.project_id}-tf-exercise"
}

# ---------------------------------------------------------------------------
# GCS Bucket
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "main" {
  name          = local.effective_bucket_name
  location      = var.region
  storage_class = "STANDARD"

  # Recommended: disables per-object ACLs, uses bucket-level IAM only
  uniform_bucket_level_access = true

  # Versioning: keeps previous versions of objects
  versioning {
    enabled = true
  }

  # Lifecycle rules: automatically manage storage class and deletion
  lifecycle_rule {
    # Move to NEARLINE after 30 days (accessed < once/month; 30-day min storage)
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 30  # days since object creation
    }
  }

  lifecycle_rule {
    # Move to COLDLINE after 90 days (accessed < once/quarter; 90-day min storage)
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
    condition {
      age = 90
    }
  }

  lifecycle_rule {
    # Move to ARCHIVE after 365 days (rarely accessed; 365-day min storage, cheapest)
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
    condition {
      age = 365
    }
  }

  lifecycle_rule {
    # Delete objects after 7 years (data retention compliance)
    action {
      type = "Delete"
    }
    condition {
      age = 2557  # ~7 years
    }
  }

  lifecycle_rule {
    # Clean up old non-current versions after 30 days (versioning cost control)
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 3    # Keep at most 3 versions
      with_state         = "ARCHIVED"
    }
  }

  # CORS — allow browser direct uploads (e.g., from a web app)
  cors {
    origin          = ["https://your-app-domain.com"]
    method          = ["GET", "PUT", "POST", "DELETE"]
    response_header = ["Content-Type", "Authorization"]
    max_age_seconds = 3600
  }

  # Soft delete: retain deleted objects for 7 days (recently GA)
  soft_delete_policy {
    retention_duration_seconds = 604800  # 7 days
  }

  labels = {
    managed_by = "terraform"
    env        = "dev"
  }

  # Prevent accidental deletion — uncomment for production
  # lifecycle {
  #   prevent_destroy = true
  # }
}

# ---------------------------------------------------------------------------
# IAM — uniform bucket-level access
# ---------------------------------------------------------------------------
resource "google_storage_bucket_iam_member" "reader" {
  count = var.reader_sa_email != "" ? 1 : 0

  bucket = google_storage_bucket.main.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.reader_sa_email}"
}

resource "google_storage_bucket_iam_member" "writer" {
  count = var.writer_sa_email != "" ? 1 : 0

  bucket = google_storage_bucket.main.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${var.writer_sa_email}"
}

# ---------------------------------------------------------------------------
# Upload a sample object (Terraform can manage GCS objects)
# ---------------------------------------------------------------------------
resource "google_storage_bucket_object" "sample_config" {
  name    = "config/sample.json"
  bucket  = google_storage_bucket.main.name
  content = jsonencode({
    version    = "1.0"
    created_by = "terraform"
    purpose    = "tf-exercise"
  })
  content_type = "application/json"
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "bucket_name" {
  value = google_storage_bucket.main.name
}

output "bucket_url" {
  value = google_storage_bucket.main.url  # gs://bucket-name
}

output "sample_object_self_link" {
  value = google_storage_bucket_object.sample_config.self_link
}

output "storage_class_cost_guide" {
  value = <<-EOT
    STANDARD  : $0.020/GB/month — hot data, frequent access
    NEARLINE  : $0.010/GB/month — accessed < once/month (30-day min charge)
    COLDLINE  : $0.004/GB/month — accessed < once/quarter (90-day min charge)
    ARCHIVE   : $0.0012/GB/month — rarely accessed (365-day min, slowest retrieval)
  EOT
}

##############################################################################
# CHALLENGES
#
# 1. Add a Pub/Sub notification on the bucket so every object creation publishes
#    an event to a Pub/Sub topic:
#    google_storage_notification { bucket, topic, event_types = ["OBJECT_FINALIZE"] }
#
# 2. Enable CMEK (Customer-Managed Encryption Key):
#    - Create a google_kms_key_ring and google_kms_crypto_key
#    - Set encryption { default_kms_key_name = google_kms_crypto_key.key.id }
#
# 3. Create a second "staging" bucket without versioning or lifecycle,
#    and use google_storage_transfer_job to automatically sync objects
#    from staging → main on a schedule.
#
# 4. Add a retention policy (legal hold equivalent):
#    retention_policy { retention_period = 2592000 }  # 30 days — objects cannot be deleted
##############################################################################
