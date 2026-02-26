##############################################################################
# Exercise 02 — Dataproc: Cluster with Autoscaling + Preemptible Workers
#
# Resources created:
#   - google_dataproc_cluster           : master + worker nodes
#   - google_dataproc_autoscaling_policy: scale workers 2–20 based on YARN
#
# Key interview topics:
#   - Preemptible (spot) workers: cost reduction but can be reclaimed
#   - Autoscaling: Dataproc scales YARN workers automatically
#   - Ephemeral clusters: create → submit job → destroy (cheapest pattern)
#   - Component gateway: web UIs (Spark, HDFS) via Cloud IAP
#
# Usage:
#   terraform init
#   terraform plan  -var="project_id=YOUR_PROJECT" -var="zone=us-central1-a"
#   terraform apply -var="project_id=YOUR_PROJECT" -var="zone=us-central1-a"
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

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "cluster_name" {
  type    = string
  default = "tf-exercise-cluster"
}

variable "staging_bucket" {
  description = "GCS bucket for Dataproc staging (must already exist)"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Autoscaling Policy
# ---------------------------------------------------------------------------
resource "google_dataproc_autoscaling_policy" "policy" {
  policy_id = "tf-exercise-autoscaling"
  location  = var.region

  worker_config {
    min_instances = 2
    max_instances = 20
    weight        = 1   # Relative weight vs secondary workers
  }

  secondary_worker_config {
    min_instances = 0
    max_instances = 50
    weight        = 1
  }

  basic_algorithm {
    yarn_config {
      # Scale up when YARN memory pending > threshold for this long
      scale_up_factor   = 1.0   # Add this fraction of current workers
      scale_down_factor = 1.0   # Remove this fraction when idle
      scale_up_min_worker_fraction   = 0.0
      scale_down_min_worker_fraction = 0.0

      graceful_decommission_timeout = "3600s"  # Give tasks 1h to finish before node removed
    }
    cooldown_period = "120s"  # Wait 2 min between scaling events
  }
}

# ---------------------------------------------------------------------------
# Dataproc Cluster
# ---------------------------------------------------------------------------
resource "google_dataproc_cluster" "cluster" {
  name   = var.cluster_name
  region = var.region

  cluster_config {
    staging_bucket = var.staging_bucket != "" ? var.staging_bucket : null

    # Master node (single master = standard cluster; 3 masters = HA)
    master_config {
      num_instances = 1
      machine_type  = "n1-standard-4"
      disk_config {
        boot_disk_type    = "pd-ssd"
        boot_disk_size_gb = 100
      }
    }

    # Primary worker nodes (persistent)
    worker_config {
      num_instances = 2
      machine_type  = "n1-standard-4"
      disk_config {
        boot_disk_type    = "pd-standard"
        boot_disk_size_gb = 100
        num_local_ssds    = 0
      }
    }

    # Secondary (preemptible / spot) workers — can be reclaimed by GCP at any time
    # Best for: fault-tolerant batch jobs; AVOID for streaming or stateful jobs
    preemptible_worker_config {
      num_instances = 5
      # preemptibility = "PREEMPTIBLE"   # default; or "SPOT" for deepest discount
    }

    # Attach autoscaling policy
    autoscaling_config {
      policy_uri = google_dataproc_autoscaling_policy.policy.name
    }

    # Installed optional components
    software_config {
      image_version = "2.1-debian11"  # Spark 3.3, Hadoop 3.3
      optional_components = [
        "JUPYTER",  # Jupyter notebook UI
        "ZEPPELIN", # Zeppelin notebook
      ]
      override_properties = {
        "dataproc:dataproc.allow.zero.workers" = "false"
        "spark:spark.executor.memory"           = "4g"
        "spark:spark.driver.memory"             = "2g"
      }
    }

    # Enable web interfaces via Cloud IAP (no VPN needed)
    endpoint_config {
      enable_http_port_access = true
    }

    # Initialisation actions — run a script on all nodes at startup
    # initialization_action {
    #   script      = "gs://your-bucket/init.sh"
    #   timeout_sec = 300
    # }

    gce_cluster_config {
      zone = var.zone

      # Optionally: restrict to internal IP only (recommended for security)
      # internal_ip_only = true

      metadata = {
        "enable-oslogin" = "TRUE"
      }

      tags = ["dataproc-cluster", "allow-internal"]
    }
  }

  # Graceful cluster termination
  graceful_decommission_timeout = "3600s"

  labels = {
    env        = "dev"
    managed_by = "terraform"
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "cluster_name" {
  value = google_dataproc_cluster.cluster.name
}

output "master_instance" {
  value = "${var.cluster_name}-m"  # Dataproc master hostname pattern
}

output "cluster_http_ports" {
  description = "Web UI endpoints (Spark, HDFS, etc.)"
  value       = google_dataproc_cluster.cluster.cluster_config[0].endpoint_config[0].http_ports
}

output "submit_job_command" {
  description = "Example gcloud command to submit a PySpark job"
  value = <<-EOT
    gcloud dataproc jobs submit pyspark gs://your-bucket/job.py \
      --cluster=${google_dataproc_cluster.cluster.name} \
      --region=${var.region} \
      --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar
  EOT
}

##############################################################################
# CHALLENGES
#
# 1. Add a scheduled deletion using google_compute_instance lifecycle or
#    a Cloud Scheduler job that calls Dataproc API to delete after 8 hours.
#    (Terraform manages the cluster; scheduled deletion needs Cloud Scheduler)
#
# 2. Change master_config to num_instances = 3 for High Availability.
#    What changes in the cluster? (Uses Zookeeper, 3-way HDFS NameNode HA)
#
# 3. Add a google_dataproc_job resource to submit a PySpark job right after
#    cluster creation and observe the depends_on behaviour.
#
# 4. Add a VPC network and subnet, then set:
#    gce_cluster_config { network = google_compute_network.vpc.self_link }
#    This isolates the cluster in a dedicated VPC.
##############################################################################
