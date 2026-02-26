# 16. Data Ingestion & Orchestration

> **Pre-Sales Context:** Customers rarely have data sitting neatly in Cloud Storage. They have legacy Oracle databases, messy SaaS APIs, and complex dependencies. You must be able to architect how data *gets into* BigQuery and how those pipelines are *scheduled*.

---

## 1. Change Data Capture (CDC) with Datastream

**The Problem:** Customers want real-time analytics on their transactional databases (MySQL, PostgreSQL, Oracle, SQL Server) without impacting the performance of those source systems.

**The Solution: Datastream**
*   **What it is:** A serverless, easy-to-use CDC and replication service.
*   **How it works:** It reads the transaction logs (e.g., MySQL binlog, Postgres WAL) and streams those changes (inserts, updates, deletes) into Google Cloud.
*   **The "Golden Path":** Datastream → Cloud Storage → Dataflow (optional for complex transforms) → BigQuery.
*   **Datastream to BigQuery (Direct):** Google now offers a direct, seamless replication from Datastream straight into BigQuery, handling schema drift automatically.

**Pre-Sales Soundbite:**
> "Instead of running heavy batch extracts that slow down your production databases, Datastream reads the transaction logs in real-time. We can replicate your Oracle data directly into BigQuery with sub-second latency, completely serverless."

---

## 2. Orchestration: Cloud Composer vs. Workflows

Once you have multiple steps (Extract → Load → Transform → Train ML Model), you need an orchestrator.

### Cloud Composer (Managed Apache Airflow)
*   **What it is:** A fully managed workflow orchestration service built on Apache Airflow.
*   **When to use it:** 
    *   The customer already uses Airflow on-prem or in AWS (MWAA).
    *   They have complex, multi-cloud, or hybrid dependencies (e.g., "Wait for an AWS S3 bucket to update, then trigger a Dataproc job, then run a BigQuery SQL script").
    *   They want to write DAGs (Directed Acyclic Graphs) in Python.
*   **Pre-Sales Note:** Composer is powerful but has a baseline cost (it runs a GKE cluster under the hood). It's for enterprise-grade orchestration.

### Cloud Workflows
*   **What it is:** A fully managed, serverless state engine for executing APIs.
*   **When to use it:**
    *   Lightweight, event-driven orchestration.
    *   Connecting microservices or GCP APIs (e.g., "When a file lands in GCS, trigger a Cloud Run function, then update Firestore").
    *   Zero baseline cost (pay per execution step).

**The Trade-off:** Use **Composer** for heavy data engineering pipelines (ETL/ELT). Use **Workflows** for lightweight, event-driven microservice orchestration.

---

## 3. Visual ETL: Cloud Data Fusion

**The Problem:** The customer has a team of analysts or legacy ETL developers (Informatica, Talend) who don't know Python or Apache Beam.

**The Solution: Cloud Data Fusion**
*   **What it is:** A fully managed, cloud-native data integration service based on the open-source CDAP project.
*   **Key Features:**
    *   Drag-and-drop UI for building pipelines.
    *   150+ pre-built connectors (Salesforce, SAP, ServiceNow, etc.).
    *   **Wrangler:** A visual tool to clean and prepare data before loading.
*   **Under the hood:** When you click "Run" on a Data Fusion pipeline, it translates the visual graph into an Apache Spark job and executes it on an ephemeral **Dataproc** cluster.

**Pre-Sales Soundbite:**
> "Data Fusion allows your data analysts to build complex ETL pipelines using a drag-and-drop interface, without writing a single line of code. And because it compiles down to Dataproc under the hood, it scales infinitely."

---

## 4. Data Transfer Service (DTS)

**What it is:** A managed service to automate data movement into BigQuery on a scheduled basis.
**Best for:**
*   SaaS applications (Google Ads, YouTube, Salesforce).
*   Cross-cloud transfers (Amazon S3 to BigQuery, Azure Blob to BigQuery).
*   Data Warehouse migrations (Teradata, Redshift to BigQuery).

---

## 5. Whiteboard Scenario: The Modern ELT Architecture

**Customer Prompt:** "We have a Postgres database for transactions, logs in AWS S3, and we need to build a daily reporting dashboard. We want to use dbt for transformations."

**The Architecture:**
1.  **Ingest (Postgres):** Use **Datastream** to replicate Postgres directly to BigQuery (Real-time).
2.  **Ingest (S3):** Use **BigQuery Omni** to query S3 directly, or **Data Transfer Service (DTS)** to pull S3 logs into GCS, then BigQuery (Batch).
3.  **Transform:** Use **dbt** (running on Cloud Run or orchestrated by Composer) to execute SQL transformations *inside* BigQuery (ELT pattern).
4.  **Orchestrate:** Use **Cloud Composer** to schedule the DTS job, wait for completion, and then trigger the dbt models.

**Why this wins:** It embraces the ELT (Extract, Load, Transform) paradigm. We use managed services to get the raw data into BigQuery as fast as possible, and use BigQuery's massive compute power to do the transformations via SQL (dbt).
