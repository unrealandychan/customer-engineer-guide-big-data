##############################################################################
# Exercise 05 — Full Pipeline: GCS + BQ + Pub/Sub + IAM (End-to-End)
#
# This module wires together the individual exercises into a realistic
# analytics ingestion pipeline:
#
#   [Producer] → Pub/Sub Topic → Subscription → [Dataflow/Beam job]
#                                                        ↓
#                                               BigQuery Table (partitioned)
#                                                        ↑
#                GCS Bucket (raw files) → BQ Load Job ───┘
#
# Resources:
#   - GCS bucket (raw data landing zone)
#   - Pub/Sub topic + pull subscription + dead-letter
#   - BigQuery dataset + partitioned table
#   - Service accounts for publisher, subscriber, BQ loader
#   - IAM bindings for all service accounts
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

variable "env" {
  type    = string
  default = "dev"
}

# Derived naming convention: all resources share the same prefix
locals {
  prefix = "analytics-${var.env}"
}

# ---------------------------------------------------------------------------
# Service Accounts
# ---------------------------------------------------------------------------
resource "google_service_account" "publisher" {
  account_id   = "${local.prefix}-publisher"
  display_name = "Pub/Sub Publisher SA"
}

resource "google_service_account" "pipeline" {
  account_id   = "${local.prefix}-pipeline"
  display_name = "Dataflow / Beam Pipeline SA"
}

resource "google_service_account" "bq_loader" {
  account_id   = "${local.prefix}-bq-loader"
  display_name = "BigQuery Loader SA"
}

# ---------------------------------------------------------------------------
# GCS — Raw Data Landing Zone
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-${local.prefix}-raw"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = false  # Raw landing zone: no versioning needed
  }

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 90 }  # Auto-purge raw files after 90 days
  }

  labels = {
    purpose    = "raw-landing"
    managed_by = "terraform"
    env        = var.env
  }
}

# Allow pipeline SA to read raw files
resource "google_storage_bucket_iam_member" "pipeline_reads_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

# Allow BQ loader SA to read raw files (for BQ load jobs)
resource "google_storage_bucket_iam_member" "bq_loader_reads_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.bq_loader.email}"
}

# GCS staging bucket for Dataproc / Dataflow temp files
resource "google_storage_bucket" "staging" {
  name                        = "${var.project_id}-${local.prefix}-staging"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 7 }  # Clean temp files after 7 days
  }

  labels = {
    purpose    = "staging-temp"
    managed_by = "terraform"
    env        = var.env
  }
}

resource "google_storage_bucket_iam_member" "pipeline_rw_staging" {
  bucket = google_storage_bucket.staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

# ---------------------------------------------------------------------------
# Pub/Sub — Event Ingestion
# ---------------------------------------------------------------------------
resource "google_pubsub_topic" "events" {
  name                       = "${local.prefix}-events"
  message_retention_duration = "86400s"

  labels = {
    managed_by = "terraform"
    env        = var.env
  }
}

resource "google_pubsub_topic" "dead_letter" {
  name = "${local.prefix}-events-dlq"
}

resource "google_pubsub_subscription" "pipeline_sub" {
  name  = "${local.prefix}-pipeline-sub"
  topic = google_pubsub_topic.events.name

  ack_deadline_seconds       = 60
  message_retention_duration = "86400s"

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

# Allow publisher SA to publish
resource "google_pubsub_topic_iam_member" "publisher_can_publish" {
  topic  = google_pubsub_topic.events.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.publisher.email}"
}

# Allow pipeline SA to subscribe
resource "google_pubsub_subscription_iam_member" "pipeline_can_subscribe" {
  subscription = google_pubsub_subscription.pipeline_sub.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.pipeline.email}"
}

# Pub/Sub service account needs to forward to DLQ
resource "google_pubsub_topic_iam_member" "pubsub_sa_dlq" {
  topic  = google_pubsub_topic.dead_letter.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

data "google_project" "project" {}

# ---------------------------------------------------------------------------
# BigQuery — Analytics Warehouse
# ---------------------------------------------------------------------------
resource "google_bigquery_dataset" "analytics" {
  dataset_id                 = replace("${local.prefix}_events", "-", "_")
  location                   = "US"
  delete_contents_on_destroy = var.env == "dev" ? true : false

  labels = {
    managed_by = "terraform"
    env        = var.env
  }
}

resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "events"
  deletion_protection = false

  time_partitioning {
    type                     = "DAY"
    field                    = "event_date"
    require_partition_filter = true
  }

  clustering = ["country", "event_type"]

  schema = jsonencode([
    { name = "event_id",   type = "STRING",  mode = "REQUIRED" },
    { name = "event_date", type = "DATE",     mode = "REQUIRED" },
    { name = "event_type", type = "STRING",   mode = "NULLABLE" },
    { name = "country",    type = "STRING",   mode = "NULLABLE" },
    { name = "user_id",    type = "STRING",   mode = "NULLABLE" },
    { name = "amount",     type = "FLOAT64",  mode = "NULLABLE" },
    { name = "ingested_at",type = "TIMESTAMP",mode = "NULLABLE" },
  ])
}

# Allow pipeline SA to write to BigQuery
resource "google_bigquery_dataset_iam_member" "pipeline_bq_editor" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

# Allow BQ loader SA to write (for GCS → BQ load jobs)
resource "google_bigquery_dataset_iam_member" "bq_loader_editor" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.bq_loader.email}"
}

# Allow pipeline SA to run BigQuery jobs (not just write data)
resource "google_project_iam_member" "pipeline_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "pipeline_architecture" {
  value = <<-EOT
    ┌─────────────────────────────────────────────────────────────┐
    │                  GCP Analytics Pipeline                     │
    │                                                             │
    │  Producer ──► Pub/Sub Topic: ${google_pubsub_topic.events.name}       │
    │                     │                                       │
    │              Subscription: ${google_pubsub_subscription.pipeline_sub.name}  │
    │                     │                                       │
    │              [Dataflow/Beam Pipeline SA]                    │
    │                     │                                       │
    │              BigQuery: ${google_bigquery_dataset.analytics.dataset_id}.events │
    │                                                             │
    │  GCS Raw: gs://${google_storage_bucket.raw.name}/          │
    │  GCS Staging: gs://${google_storage_bucket.staging.name}/  │
    └─────────────────────────────────────────────────────────────┘
  EOT
}

output "service_account_emails" {
  value = {
    publisher  = google_service_account.publisher.email
    pipeline   = google_service_account.pipeline.email
    bq_loader  = google_service_account.bq_loader.email
  }
}

output "bq_table_full_id" {
  value = "${var.project_id}.${google_bigquery_dataset.analytics.dataset_id}.events"
}

output "raw_bucket_url" {
  value = "gs://${google_storage_bucket.raw.name}"
}

##############################################################################
# CHALLENGES
#
# 1. Modularise this file: extract GCS, Pub/Sub, and BigQuery blocks into
#    separate modules/ directories and call them with `module "bq" { source = ... }`.
#
# 2. Add a `terraform.tfvars` file with project_id and env values so you
#    don't need to pass -var flags every time.
#
# 3. Add a Cloud Scheduler job (google_cloud_scheduler_job) that triggers a
#    Cloud Run job to load files from GCS to BigQuery every hour.
#
# 4. Add a Monitoring dashboard (google_monitoring_dashboard) showing:
#    - Pub/Sub undelivered message count
#    - BigQuery bytes processed per day
#    - GCS bucket storage used
##############################################################################
