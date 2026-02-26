##############################################################################
# Exercise 01 — BigQuery: Dataset, Table, IAM
#
# Resources created:
#   - google_bigquery_dataset       : the "database" container
#   - google_bigquery_table         : partitioned + clustered table
#   - google_bigquery_dataset_iam_member : grant a service account data viewer
#
# Key interview topics:
#   - Partitioning vs clustering in Terraform schema
#   - IAM binding vs IAM member (additive vs authoritative)
#   - Expiration / lifecycle via Terraform
#
# Usage:
#   terraform init
#   terraform plan  -var="project_id=YOUR_PROJECT"
#   terraform apply -var="project_id=YOUR_PROJECT"
##############################################################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
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
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Default region for resources"
  type        = string
  default     = "US"   # BigQuery uses multi-region strings like "US", "EU"
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "tf_exercise_dataset"
}

variable "table_id" {
  description = "BigQuery table ID"
  type        = string
  default     = "events"
}

variable "viewer_email" {
  description = "Service account or user email to grant BigQuery Data Viewer"
  type        = string
  default     = ""  # Leave empty to skip IAM binding
}

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
resource "google_bigquery_dataset" "main" {
  dataset_id                  = var.dataset_id
  location                    = var.region
  description                 = "Terraform exercise dataset"
  delete_contents_on_destroy  = true   # Safe for dev; remove in prod!

  # Default table expiration: 30 days (ms)
  default_table_expiration_ms = 2592000000

  labels = {
    env        = "dev"
    managed_by = "terraform"
  }
}

# ---------------------------------------------------------------------------
# Partitioned + Clustered Table
# ---------------------------------------------------------------------------
resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.main.dataset_id
  table_id            = var.table_id
  deletion_protection = false  # Allow `terraform destroy` to drop the table

  # Time-based partitioning on the event_date column
  time_partitioning {
    type                     = "DAY"
    field                    = "event_date"
    expiration_ms            = 7776000000  # 90 days per partition
    require_partition_filter = true        # Prevent full-table scans
  }

  # Clustering: up to 4 columns, order matters
  clustering = ["country", "event_type", "user_id"]

  schema = jsonencode([
    { name = "event_id",   type = "STRING",    mode = "REQUIRED" },
    { name = "event_date", type = "DATE",       mode = "REQUIRED" },
    { name = "event_type", type = "STRING",     mode = "NULLABLE" },
    { name = "country",    type = "STRING",     mode = "NULLABLE" },
    { name = "user_id",    type = "STRING",     mode = "NULLABLE" },
    { name = "amount",     type = "FLOAT64",    mode = "NULLABLE" },
    {
      name = "metadata"
      type = "RECORD"
      mode = "NULLABLE"
      fields = jsonencode([
        { name = "source",     type = "STRING", mode = "NULLABLE" },
        { name = "version",    type = "STRING", mode = "NULLABLE" },
      ])
    },
  ])

  labels = {
    managed_by = "terraform"
  }

  depends_on = [google_bigquery_dataset.main]
}

# ---------------------------------------------------------------------------
# IAM — grant BigQuery Data Viewer to a principal
# (Uses google_bigquery_dataset_iam_member = ADDITIVE, not authoritative)
# ---------------------------------------------------------------------------
resource "google_bigquery_dataset_iam_member" "viewer" {
  count = var.viewer_email != "" ? 1 : 0   # Conditional resource

  dataset_id = google_bigquery_dataset.main.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${var.viewer_email}"
}

# ---------------------------------------------------------------------------
# Outputs — values visible after `terraform apply`
# ---------------------------------------------------------------------------
output "dataset_id" {
  description = "The BigQuery dataset ID"
  value       = google_bigquery_dataset.main.dataset_id
}

output "table_full_id" {
  description = "The fully-qualified BigQuery table ID"
  value       = "${var.project_id}.${google_bigquery_dataset.main.dataset_id}.${google_bigquery_table.events.table_id}"
}

output "dataset_self_link" {
  value = google_bigquery_dataset.main.self_link
}

##############################################################################
# CHALLENGES
#
# 1. Add a second table for "users" with a different schema (no partitioning).
#    Reference the same dataset with google_bigquery_dataset.main.dataset_id.
#
# 2. Add `google_bigquery_dataset_iam_binding` (authoritative) and compare:
#    - iam_member   = additive (preserves existing bindings)
#    - iam_binding  = authoritative (replaces ALL members for the role)
#    When would you use each? (iam_binding in isolated dev, iam_member in shared env)
#
# 3. Enable remote functions / connection:
#    Add google_bigquery_connection for a Cloud SQL or BigLake connection.
#
# 4. Store Terraform state in GCS:
#    terraform {
#      backend "gcs" {
#        bucket = "your-tf-state-bucket"
#        prefix = "terraform/bigquery"
#      }
#    }
##############################################################################
