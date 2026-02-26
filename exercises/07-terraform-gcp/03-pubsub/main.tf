##############################################################################
# Exercise 03 — Pub/Sub: Topic, Subscription, Dead-Letter
#
# Resources created:
#   - google_pubsub_topic                : main topic
#   - google_pubsub_topic                : dead-letter topic (undeliverable msgs)
#   - google_pubsub_subscription         : push subscription with dead-letter
#   - google_pubsub_subscription         : pull subscription (simpler)
#   - google_pubsub_topic_iam_member     : allow a SA to publish
#   - google_pubsub_subscription_iam_member : allow a SA to subscribe
#
# Key interview topics:
#   - Dead-letter topics: what happens when a message is nacked repeatedly?
#   - Push vs Pull subscriptions: when to use each
#   - Message retention: how long unacked messages are kept
#   - Exactly-once delivery: available in Pub/Sub Lite
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

variable "topic_name" {
  type    = string
  default = "tf-events"
}

variable "push_endpoint" {
  description = "HTTPS endpoint for push subscription (Cloud Run URL or App Engine)"
  type        = string
  default     = ""   # Leave empty to skip push subscription
}

variable "publisher_sa_email" {
  description = "Service account email allowed to publish"
  type        = string
  default     = ""
}

variable "subscriber_sa_email" {
  description = "Service account email allowed to subscribe"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Main Topic
# ---------------------------------------------------------------------------
resource "google_pubsub_topic" "main" {
  name = var.topic_name

  # Message retention: keep messages even after delivery for replay (default: 7 days)
  message_retention_duration = "86600s"  # ~24 hours

  message_storage_policy {
    allowed_persistence_regions = [var.region]  # Data stays in this region
  }

  labels = {
    managed_by = "terraform"
    env        = "dev"
  }
}

# ---------------------------------------------------------------------------
# Dead-Letter Topic — receives messages that failed delivery N times
# ---------------------------------------------------------------------------
resource "google_pubsub_topic" "dead_letter" {
  name = "${var.topic_name}-dead-letter"

  labels = {
    managed_by = "terraform"
    purpose    = "dead-letter"
  }
}

# Dead-letter subscription — so undeliverable messages can be inspected
resource "google_pubsub_subscription" "dead_letter_sub" {
  name  = "${var.topic_name}-dead-letter-sub"
  topic = google_pubsub_topic.dead_letter.name

  ack_deadline_seconds    = 60
  message_retention_duration = "604800s"  # 7 days for investigation
}

# ---------------------------------------------------------------------------
# Pull Subscription (simplest — subscribers call receive() or pull())
# ---------------------------------------------------------------------------
resource "google_pubsub_subscription" "pull" {
  name  = "${var.topic_name}-pull-sub"
  topic = google_pubsub_topic.main.name

  ack_deadline_seconds = 60   # Time for subscriber to ack before redelivery

  # Retain undelivered messages for 24 hours
  message_retention_duration = "86400s"

  # Retry policy: exponential backoff between redeliveries
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 min max between retries
  }

  # Dead-letter: after 5 failed deliveries, forward to dead-letter topic
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  # Prevent accidental deletion of subscriptions with backlog
  # (Remove for dev environments)
  # lifecycle {
  #   prevent_destroy = true
  # }

  depends_on = [google_pubsub_topic.main, google_pubsub_topic.dead_letter]
}

# ---------------------------------------------------------------------------
# Push Subscription (Pub/Sub pushes to your HTTPS endpoint)
# ---------------------------------------------------------------------------
resource "google_pubsub_subscription" "push" {
  count = var.push_endpoint != "" ? 1 : 0

  name  = "${var.topic_name}-push-sub"
  topic = google_pubsub_topic.main.name

  ack_deadline_seconds = 30

  push_config {
    push_endpoint = var.push_endpoint

    # OIDC token: Pub/Sub will attach a JWT so your endpoint can verify the caller
    oidc_token {
      service_account_email = var.subscriber_sa_email != "" ? var.subscriber_sa_email : ""
    }

    attributes = {
      x-goog-version = "v1"
    }
  }
}

# ---------------------------------------------------------------------------
# IAM — allow service accounts to publish and subscribe
# ---------------------------------------------------------------------------
resource "google_pubsub_topic_iam_member" "publisher" {
  count = var.publisher_sa_email != "" ? 1 : 0

  topic  = google_pubsub_topic.main.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${var.publisher_sa_email}"
}

resource "google_pubsub_subscription_iam_member" "subscriber" {
  count = var.subscriber_sa_email != "" ? 1 : 0

  subscription = google_pubsub_subscription.pull.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.subscriber_sa_email}"
}

# Pub/Sub service account needs permission to publish to the dead-letter topic
resource "google_pubsub_topic_iam_member" "pubsub_sa_dead_letter_publisher" {
  topic  = google_pubsub_topic.dead_letter.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

data "google_project" "project" {}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "topic_id" {
  value = google_pubsub_topic.main.id
}

output "pull_subscription_id" {
  value = google_pubsub_subscription.pull.id
}

output "dead_letter_topic_id" {
  value = google_pubsub_topic.dead_letter.id
}

output "test_publish_command" {
  value = "gcloud pubsub topics publish ${google_pubsub_topic.main.name} --message='hello'"
}

output "test_pull_command" {
  value = "gcloud pubsub subscriptions pull ${google_pubsub_subscription.pull.name} --auto-ack"
}

##############################################################################
# CHALLENGES
#
# 1. Add a BigQuery subscription (google_pubsub_subscription with bigquery_config).
#    Pub/Sub writes directly to a BQ table — no Dataflow needed!
#    bigquery_config { table = "project:dataset.table" }
#
# 2. Add message filtering on the pull subscription:
#    filter = "attributes.event_type = \"purchase\""
#    Only purchase events will be delivered to this subscription.
#
# 3. Enable exactly-once delivery:
#    enable_exactly_once_delivery = true
#    What's the trade-off? (Higher latency, requires subscriber to use StreamingPull)
#
# 4. Create a Cloud Monitoring alert when dead-letter message count > 0:
#    google_monitoring_alert_policy resource with a pubsub/subscription/num_undelivered_messages metric.
##############################################################################
