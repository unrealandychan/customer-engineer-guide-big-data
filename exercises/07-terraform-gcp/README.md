# Category 07 — Terraform for GCP

## What you will practice

| Module                        | GCP Resources provisioned                                |
|-------------------------------|----------------------------------------------------------|
| `01-bigquery/`                | Dataset, partitioned + clustered table, IAM binding      |
| `02-dataproc/`                | Cluster with autoscaling policy, preemptible workers     |
| `03-pubsub/`                  | Topic, subscription, dead-letter topic + subscription    |
| `04-gcs/`                     | Bucket, lifecycle rules, uniform bucket-level IAM        |
| `05-full-pipeline/`           | End-to-end: GCS + BQ dataset + Pub/Sub + Dataproc        |

---

## Prerequisites

```bash
# Install Terraform (macOS)
brew tap hashicorp/tap && brew install hashicorp/tap/terraform

# Authenticate
gcloud auth application-default login

# Verify
terraform version
```

---

## Usage Pattern (same for every module)

```bash
cd 01-bigquery/

# 1. Initialise providers and modules
terraform init

# 2. Preview what will be created/changed/destroyed
terraform plan -var="project_id=your-project-id"

# 3. Apply — creates real GCP resources
terraform apply -var="project_id=your-project-id"

# 4. Destroy when done (avoids charges)
terraform destroy -var="project_id=your-project-id"
```

---

## Key Terraform Concepts

| Concept           | Description                                                  |
|-------------------|--------------------------------------------------------------|
| `provider`        | Plugin for a cloud API (here: `hashicorp/google`)            |
| `resource`        | Infrastructure object to manage (`google_bigquery_dataset`)  |
| `variable`        | Input parameter (set via `-var` or `terraform.tfvars`)       |
| `output`          | Expose values after apply (e.g. bucket name, dataset ID)     |
| `data source`     | Read existing resources without managing them                |
| `locals`          | Computed values reused within a module                       |
| `module`          | Reusable group of resources (like a function)                |
| `state`           | `.tfstate` file tracking what Terraform manages              |
| `backend`         | Where state is stored (GCS bucket for team use)              |

---

## Interview One-Liners

- **Why Terraform over `gcloud` scripts?**
  Declarative, idempotent, drift detection, dependency graph, plan-before-apply safety.

- **How do you store Terraform state in GCP?**
  `backend "gcs" { bucket = "my-tf-state"; prefix = "env/prod" }`

- **What is `terraform plan`?**
  Dry-run: shows exactly what will be created/modified/destroyed without making any API calls.

- **How do you prevent accidental destruction of a critical resource?**
  `lifecycle { prevent_destroy = true }` in the resource block.
