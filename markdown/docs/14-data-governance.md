# Doc 14 — Data Governance on GCP

> Governance comes up in almost every enterprise deal. Security teams, legal, and CDOs ask about it. This doc gives you the full technical depth and pre-sales pitch — from column-level security to Dataplex Universal Catalog to regulatory compliance.

---

## Why Governance Matters in Pre-Sales

Enterprise customers (especially in finance, healthcare, retail, and government) will always ask:

- *"Who can see what data?"*
- *"How do we know where our data came from?"*
- *"How do we prove to regulators that PII is protected?"*
- *"How do we stop analysts from accessing production customer data?"*

If you can't answer these confidently, you lose the deal — not because the technology is wrong, but because the security team blocks it. Governance is a deal-blocker topic.

---

## The GCP Governance Stack (Four Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: METADATA & DISCOVERY                                  │
│  Dataplex Universal Catalog — find, document, understand data   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: DATA QUALITY                                          │
│  Dataplex Data Quality — SQL-based quality rules, alerting      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: ACCESS CONTROL                                        │
│  IAM + Column-Level Security (Policy Tags) + Row-Level Security │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: IDENTITY & PERIMETER                                  │
│  VPC Service Controls + Audit Logs + CMEK                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Identity and Perimeter

### IAM (Identity and Access Management)

Every GCP resource is controlled by IAM policies. For data workloads:

| Role | Who gets it | What they can do |
|------|------------|-----------------|
| `roles/bigquery.admin` | Data platform admins | Everything |
| `roles/bigquery.dataEditor` | ETL service accounts | Read + write data |
| `roles/bigquery.dataViewer` | Analysts, BI tools | Read data only |
| `roles/bigquery.jobUser` | Anyone who runs queries | Submit jobs (no data access) |
| `roles/bigquery.user` | Standard analyst | Run queries + view job results |

**Best practice:** Grant at the **dataset** level, not the project level. Use service accounts for automated pipelines, not user accounts.

### VPC Service Controls

Creates a **security perimeter** around GCP resources — data cannot leave the defined perimeter even if credentials are stolen.

```
Without VPC SC:
Stolen credential → attacker downloads all BigQuery data from home network ✗

With VPC SC:
Stolen credential → request blocked because it's outside the perimeter ✓
```

**What it protects:** BigQuery, GCS, Pub/Sub, and other APIs within the perimeter.

**Pre-sales pitch:**
> "VPC Service Controls is the answer to 'what happens if credentials are compromised?' It's a network-level data exfiltration prevention mechanism. Even with valid credentials, data cannot be accessed from outside the defined perimeter — your corporate network or approved IP ranges."

### Cloud Audit Logs

Every action against BigQuery (and all GCP services) is logged:

- **Admin Activity logs:** Who created/deleted tables, datasets, changed IAM policies
- **Data Access logs:** Every `SELECT`, `INSERT`, `DELETE` — who ran it, when, what was scanned
- **System Event logs:** Automated system actions

```sql
-- Query audit logs in BigQuery (if exported there)
SELECT
  protopayload_auditlog.authenticationInfo.principalEmail as user,
  protopayload_auditlog.resourceName as resource,
  timestamp,
  protopayload_auditlog.serviceName,
  protopayload_auditlog.methodName as action
FROM `project.dataset.cloudaudit_googleapis_com_data_access`
WHERE DATE(timestamp) = CURRENT_DATE()
  AND protopayload_auditlog.serviceName = 'bigquery.googleapis.com'
ORDER BY timestamp DESC
LIMIT 100;
```

**Pre-sales pitch:**
> "Every BigQuery query is logged — who ran it, what table they touched, how many bytes they scanned. Export to BigQuery and you have a full compliance audit trail. We've seen customers use this to identify rogue analysts scanning terabytes unnecessarily, and for GDPR right-to-erasure verification."

### Customer-Managed Encryption Keys (CMEK)

By default, GCP encrypts all data at rest with Google-managed keys. For customers requiring key control (FIPS compliance, regulated industries):

```bash
# Create a key in Cloud KMS
gcloud kms keyrings create my-keyring --location=us-central1
gcloud kms keys create my-bq-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --purpose=encryption

# Create a BigQuery dataset with CMEK
bq mk \
  --dataset \
  --default_kms_key=projects/my-project/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-bq-key \
  my-project:sensitive_dataset
```

**Pre-sales pitch:**
> "With CMEK, you hold the master key. If a regulator requires you to immediately revoke access to all data, you disable the key in Cloud KMS — BigQuery can no longer decrypt any data. This is the 'break glass' control that many financial and government customers require."

---

## Layer 2 — Access Control

### Column-Level Security with Policy Tags

**The most important BigQuery security feature for enterprise customers.**

Policy tags let you classify columns (e.g., PII, sensitive, restricted) and automatically enforce access control — without changing any application code.

**How it works:**
1. Create a **Taxonomy** (e.g., "Data Sensitivity")
2. Create **Policy Tags** within it (e.g., "PII", "Confidential", "Internal")
3. Apply policy tags to **BigQuery columns**
4. Grant the **Fine-Grained Reader** role only to users who should see that column
5. Everyone else sees `NULL` for those columns automatically — no application code needed

```sql
-- Create the taxonomy and tags via Console or API
-- Then apply to a column:
ALTER TABLE `proj.dataset.customers`
ALTER COLUMN ssn
SET OPTIONS (policy_tags = ['projects/proj/locations/us/taxonomies/123/policyTags/456']);

-- Without Fine-Grained Reader role:
SELECT ssn FROM `proj.dataset.customers`;
-- Returns: NULL (masking enforced automatically)

-- With Fine-Grained Reader role:
SELECT ssn FROM `proj.dataset.customers`;
-- Returns: actual SSN values
```

**Pre-sales pitch:**
> "Policy tags let you tag a column as 'PII' and BigQuery automatically masks it for anyone who doesn't have explicit access. No middleware, no application changes, no stored procedures. The protection is enforced at the storage layer — impossible to bypass even with direct API access."

### Row-Level Security

Restrict which **rows** a user can see — not just columns.

```sql
-- Create a row access policy: analysts only see their own region's data
CREATE OR REPLACE ROW ACCESS POLICY region_filter
ON `proj.dataset.sales`
GRANT TO ('group:us-analysts@company.com')
FILTER USING (region = 'US');

CREATE OR REPLACE ROW ACCESS POLICY region_filter_eu
ON `proj.dataset.sales`
GRANT TO ('group:eu-analysts@company.com')
FILTER USING (region = 'EU');

-- US analysts run: SELECT * FROM sales → only see US rows automatically
-- EU analysts run: SELECT * FROM sales → only see EU rows automatically
-- Admins see all rows
```

**Use case:** Multi-tenant analytics, regional data isolation, GDPR data residency requirements.

### Authorized Views and Authorized Datasets

Share data **without granting direct table access**. The view is the only access point.

```sql
-- Create a view that strips PII columns
CREATE VIEW `proj.shared_dataset.safe_customers` AS
SELECT
  customer_id,
  country,
  account_tier,
  -- PII columns omitted: no name, email, address, phone
  created_date
FROM `proj.raw_dataset.customers`;

-- Grant analysts access to the VIEW, not the underlying table
-- They can query the view but cannot access raw_dataset directly
```

**Authorized dataset:** Share an entire dataset's worth of views with another dataset — useful for data product publishing across teams.

---

## Layer 3 — Data Quality

### Dataplex Data Quality

Dataplex lets you define **SQL-based quality rules** that run on a schedule and alert if data violates them.

```yaml
# dataplex-data-quality.yaml
rules:
  - column: order_id
    rule_type: NOT_NULL
    threshold: 1.0  # 100% must be non-null

  - column: amount
    rule_type: RANGE
    min_value: 0
    max_value: 1000000
    threshold: 0.99  # 99% must be in range

  - rule_type: SQL
    sql_expression: |
      SELECT COUNTIF(order_date > CURRENT_DATE()) / COUNT(*) >= 0
      FROM ${data_asset}
    # No future-dated orders allowed
```

**Pre-sales pitch:**
> "Dataplex Data Quality gives data stewards a no-code way to define what 'good data' means. Rules run on a schedule, and if quality drops below a threshold — say, more than 1% of records are missing a required field — it triggers an alert and can block downstream pipelines from consuming bad data."

---

## Layer 4 — Metadata and Discovery

### Dataplex Universal Catalog

In 2024-2025, Google merged **Data Catalog** and **Dataplex** into **Dataplex Universal Catalog** — one platform for:

| Capability | What it does |
|------------|-------------|
| **Auto-discovery** | Scans GCS, BigQuery, Cloud SQL, Spanner — automatically registers all data assets |
| **Schema inference** | Detects column names and types from files in GCS |
| **Business glossary** | Define business terms ("MRR", "Active User") and link them to technical columns |
| **Policy tags** | Apply sensitivity classification at scale via the catalog (syncs to BigQuery) |
| **Data lineage** | Track: "this BigQuery table was produced by this Dataflow job from this Pub/Sub topic" |
| **Search** | Google-style search across all data assets: `SELECT * FROM catalog WHERE ...` |
| **Data products** | Curate and publish datasets as products with owners, SLAs, and documentation |

**Pre-sales pitch:**
> "Dataplex Universal Catalog is like Google Search for your enterprise data. An analyst can type 'customer orders Q1' and find the right BigQuery table, see its schema, understand who owns it, and know it's been quality-checked — all without asking anyone. Data stewards can see lineage diagrams showing where every column came from."

### Data Lineage

Dataplex automatically tracks lineage for:
- BigQuery queries (which table produced which)
- Dataflow jobs (which PCollection → which table)
- Composer/Airflow DAGs

```
GCS raw files
     ↓ (Dataflow pipeline)
BigQuery: raw.orders
     ↓ (dbt/scheduled query transformation)
BigQuery: curated.order_summary
     ↓ (scheduled query aggregation)
BigQuery: reporting.revenue_by_region
     ↓ (Looker reads)
Dashboard: Revenue by Region
```

**Lineage means:** Click on `reporting.revenue_by_region` in Dataplex → see every upstream table and job that produced it → trace data all the way back to the raw GCS file.

---

## Regulatory Compliance Scenarios

### GDPR — Right to Erasure (Right to Be Forgotten)

Challenge: A user requests deletion of all their data from BigQuery. BigQuery is append-only for streaming inserts.

**Solution:**
```sql
-- Delete a specific user's data from a BigQuery table
DELETE FROM `proj.dataset.user_events`
WHERE user_id = 'user_123456';

-- For partitioned tables — more efficient:
DELETE FROM `proj.dataset.user_events`
WHERE user_id = 'user_123456'
  AND event_date BETWEEN '2020-01-01' AND '2025-12-31';

-- Verify deletion with audit log entry
-- Then document in compliance system
```

**For streaming data at scale:** Use a "tombstone" or "deleted_users" table — join at query time to exclude deleted users without expensive full-table scans.

### HIPAA — Healthcare Data

BigQuery is HIPAA-compliant with the right configuration:
1. Sign a **Business Associate Agreement (BAA)** with Google
2. Use **CMEK** for key control
3. Enable **VPC Service Controls** perimeter
4. Apply **Policy Tags** to all PHI (Protected Health Information) columns
5. Enable **Data Access audit logs** for all BigQuery operations
6. Restrict to **specific geographic regions** (no multi-region storage for PHI in some jurisdictions)

### PCI-DSS — Payment Card Data

- **Never store raw card numbers in BigQuery** — store tokens only
- Use **column-level security** for cardholder names and expiry dates
- Enable **VPC Service Controls** perimeter around BQ + GCS
- **Audit logs** to Cloud Logging → BigQuery for 12-month retention
- Enable **Cloud Armor** at API layer if applicable

---

## The Governance Conversation Cheat Sheet

```
Customer asks about...        Your answer covers...
────────────────────────────────────────────────────────────────
"Who can see what?"           IAM roles + Policy Tags (column) + Row-level security
"What if credentials leak?"   VPC Service Controls (perimeter blocks exfiltration)
"Can we audit all access?"    Cloud Audit Logs → BigQuery → dashboards
"Can we encrypt with our key" CMEK via Cloud KMS
"How do we find our data?"    Dataplex Universal Catalog (search + metadata)
"Is our data good quality?"   Dataplex Data Quality rules + alerting
"Where did this table come from?" Dataplex Data Lineage
"How do we meet GDPR?"        DELETE statements + Policy Tags PII + audit logs
"How do we meet HIPAA?"       BAA + CMEK + VPC SC + Policy Tags + audit logs
```

---

## 30-Second Governance Pitch

**When a customer's security team asks "how do you handle data governance?":**

> "GCP has a four-layer governance story. At the foundation, VPC Service Controls creates a network perimeter — even stolen credentials can't exfiltrate data from outside it. On top of that, IAM controls dataset and table access, while BigQuery's native column-level security with Policy Tags automatically masks PII for unauthorized users — no application code changes needed. For metadata, Dataplex Universal Catalog auto-discovers all your data assets, tracks lineage from raw source to dashboard, and lets analysts find the right dataset through a Google-style search. And every single BigQuery query is captured in Cloud Audit Logs — you have a complete compliance trail for GDPR, HIPAA, or any regulator."

---

## Practice Q&A

**Q1: A customer's CISO asks "what prevents an employee with BigQuery access from downloading all customer PII and sending it outside the company?" How do you answer?**
<details><summary>Answer</summary>
Two controls: (1) Policy Tags on PII columns — the employee would only see NULLs for those columns unless granted Fine-Grained Reader role, even with full dataset access. (2) VPC Service Controls — even if they could query the data, the network perimeter blocks any access from outside approved networks/IPs. Plus every query is in Cloud Audit Logs, so the attempt is visible.
</details>

**Q2: What is the difference between column-level security and row-level security in BigQuery?**
<details><summary>Answer</summary>
Column-level security (Policy Tags) restricts access to specific columns — users without Fine-Grained Reader see NULL for tagged columns. Row-level security (Row Access Policies) restricts which rows users can see — a filter is automatically applied per user/group. They can be combined: some users see only certain rows AND certain columns.
</details>

**Q3: A customer wants to know how their analysts can find the right BigQuery table out of 5,000 tables. What GCP tool helps?**
<details><summary>Answer</summary>
Dataplex Universal Catalog. It auto-discovers all BigQuery tables, GCS files, and other data assets. Analysts can search with natural language or keywords, see schemas, sample data, column descriptions, owner, quality status, and lineage — all without asking anyone.
</details>

**Q4: What is data lineage and why do enterprise customers care?**
<details><summary>Answer</summary>
Data lineage tracks which upstream sources and transformations produced a given table or column. Enterprise customers care for two reasons: (1) Trust — analysts can verify a table's data came from authoritative sources; (2) Compliance — regulators (GDPR, SOX) require the ability to trace where data came from and who touched it. Dataplex tracks lineage automatically for BigQuery, Dataflow, and Composer.
</details>

**Q5: A healthcare customer asks if BigQuery is HIPAA compliant. What do you say?**
<details><summary>Answer</summary>
Yes, with the right configuration. BigQuery is on Google's HIPAA-eligible services list, but compliance is a shared responsibility. The customer needs to: sign a BAA with Google, use CMEK for encryption key control, enable VPC Service Controls, apply Policy Tags to all PHI columns, enable audit logging, and restrict data to appropriate regions. Google provides the compliant infrastructure; the customer configures it correctly.
</details>
