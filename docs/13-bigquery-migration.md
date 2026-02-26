# Doc 13 — BigQuery Migration Playbook

> BigQuery migration is one of the most common pre-sales motions at Google Cloud. A customer almost always comes from somewhere: Redshift, Teradata, Snowflake, Hive, or on-prem Hadoop. This doc covers the full migration conversation — discovery, technical mapping, objection handling, and positioning.

---

## Why Migration Comes Up So Often

Almost every enterprise you talk to has an existing data warehouse or data lake. "Move to BigQuery" is one of the most frequent GCP deals. You need to:

1. Know the **migration paths** from the major platforms
2. Be able to **run a discovery conversation** to scope the migration
3. Handle the common **objections and fears**
4. Know Google's **tooling and programs** that accelerate migration
5. Position the **TCO and business value**

---

## The Migration Conversation Framework

### Step 1 — Discovery Questions (ask these first)

```
Platform & scale:
├── "What warehouse/lake are you running today?"
├── "How many TB of data? How many tables? Users?"
├── "What's your current infrastructure cost per month?"
└── "Are you self-managed or on a managed service?"

Workloads:
├── "What types of workloads? ETL jobs, BI dashboards, ad-hoc SQL?"
├── "Do you have streaming pipelines, or batch only?"
└── "What BI tools connect to it? Tableau, Looker, Power BI?"

Pain points:
├── "What frustrates your team about the current setup?"
├── "What would you do if the warehouse were 10x faster? 10x cheaper?"
└── "Is there anything your current platform can't do that you wish it could?"

Timeline and risk:
├── "Is this a lift-and-shift, or are you open to re-architecting?"
├── "Do you have a hard deadline (contract expiry, hardware refresh)?"
└── "How risk-tolerant is the team? Big-bang or phased migration?"
```

### Step 2 — Map Their World to BigQuery

| Their Platform | Their Term | BigQuery Equivalent |
|---------------|-----------|---------------------|
| Redshift | Schema | Dataset |
| Redshift | Distribution key | Clustering column |
| Redshift | Sort key | Partition column |
| Redshift | Vacuum | No equivalent (BQ handles it automatically) |
| Teradata | Database | Dataset |
| Teradata | BTEQ scripts | BigQuery scheduled queries or Dataflow |
| Teradata | AmPS (worker nodes) | Slots (BQ handles allocation) |
| Teradata | Permanent space | No equivalent (BQ auto-manages storage) |
| Snowflake | Virtual Warehouse | Slot reservations (or just on-demand) |
| Snowflake | Time Travel | BigQuery Time Travel (7 days default, up to 7 days) |
| Snowflake | Zero-copy clone | BigQuery table snapshots / table clones |
| Hive/Hadoop | Partitioned table (HDFS files) | External table on GCS or native BQ table |
| On-prem Oracle | Stored procedures | BQ stored procedures (JS or SQL) |

---

## Migration Paths by Source Platform

### From Amazon Redshift

**Similarity level:** Medium-High — both are columnar SQL warehouses

**Key differences:**
- Redshift: node-based, you pick cluster size, vacuum required, WLM for concurrency
- BigQuery: serverless, no cluster, auto-manages everything

**Migration approach:**
1. **Schema migration:** Use BigQuery Migration Service (BQMS) to translate Redshift DDL → BQ DDL
2. **SQL translation:** BQMS translates most Redshift SQL dialects automatically (handles `LISTAGG`, `DATEADD`, window functions)
3. **Data migration:** Unload Redshift tables to S3 → Transfer Service copies to GCS → BQ load job
4. **ETL jobs:** Assess whether to lift-and-shift (same Spark/Python) or re-build as Dataflow pipelines

**Common objection:** *"We're already invested in AWS."*
> "The question isn't AWS vs GCP — it's what you can unlock. BigQuery's serverless model means you stop paying for idle clusters. Many customers run Redshift on AWS and BigQuery on GCP for analytics workloads where BigQuery is the right tool — hybrid is completely supported."

---

### From Teradata

**Similarity level:** Low-Medium — Teradata is MPP, complex stored procedures, proprietary SQL extensions

**Key differences:**
- Teradata: on-prem or cloud, requires significant DBA expertise, very proprietary syntax (BTEQ, FastLoad, MultiLoad, TPT)
- BigQuery: serverless, standard SQL, no DBA required

**This is Google's most common "modernization" deal — Teradata is expensive and aging.**

**Migration approach:**
1. **Assessment:** Inventory databases, objects, SQL jobs, ETL dependencies
2. **Schema migration:** BQMS auto-translates Teradata DDL (handles SET tables, multiset, etc.)
3. **SQL translation:** BQMS translates BTEQ/SQL — expect 70-90% auto-translation; rest needs manual review
4. **Data extraction:** Teradata TPT (Teradata Parallel Transporter) → GCS
5. **ETL re-platforming:** BTEQ scripts → BigQuery scheduled queries or Dataflow pipelines
6. **Validation:** Row counts, checksums, sample value comparison

**Migration timeline (typical):**
```
Month 1-2: Assessment + schema/SQL translation
Month 3-4: Data migration (wave 1 — dev/test environments)
Month 5-6: ETL migration + parallel run (validate BQ vs Teradata outputs)
Month 7-8: Wave 2 (production migration) + cutover
Month 9+:  Decommission Teradata
```

**The TCO pitch:**
> "Teradata licenses are typically $500K-$5M/year. BigQuery is usage-based — a customer I've seen moved from $1.2M/year Teradata to $180K/year BigQuery for the same workload. The migration pays for itself in under 12 months."

---

### From Snowflake

**Similarity level:** High — both are cloud-native SQL warehouses with similar SQL compatibility

**Key differences:**
- Snowflake: compute/storage separation, virtual warehouses (still have to pick/size), multi-cloud
- BigQuery: fully serverless (no warehouse to manage), native GCP integration (Vertex AI, Dataplex, Looker)

**This is a competitive deal — Snowflake customers are happy, not in pain. Position on Google-native advantages.**

**Migration approach:**
1. **Schema migration:** BQMS translates Snowflake DDL (most standard SQL, minor dialect differences)
2. **Data migration:** Snowflake COPY INTO → GCS → BigQuery Load
3. **Feature mapping:**
   - Snowflake Zero-copy clone → BigQuery table clones (beta/GA)
   - Snowflake Streams (CDC) → BigQuery change data capture via Datastream
   - Snowflake Tasks → BigQuery scheduled queries or Composer

**Positioning vs Snowflake:**
| | BigQuery | Snowflake |
|--|---------|-----------|
| Pricing model | On-demand (per TB) + Slot reservations | Per-second compute (warehouse must be running) |
| AI/ML | Native (BQML, Vertex AI direct integration) | Cortex (growing but less mature) |
| Governance | Dataplex + Data Catalog native | Requires 3rd party |
| BI tool | Looker native integration | Works with many; Looker also compatible |
| Streaming | Native (Pub/Sub → BQ direct) | Kafka connector or Snowpipe |

---

### From Hive / Hadoop On-Prem

**Similarity level:** Low — Hive is file-based, schema-on-read; BigQuery is schema-on-write

**Key differences:**
- Hive/Hadoop: data lives in HDFS files, schemas defined externally, queries often run via Spark
- BigQuery: managed storage, schemas enforced at write time

**Migration approach — two paths:**

**Path A: Lift-and-shift data, modernize later**
1. Copy HDFS data to GCS (use `gsutil rsync` or Storage Transfer Service)
2. Create BigQuery external tables pointing to GCS files (query immediately, no loading needed)
3. Gradually migrate hot tables to native BigQuery storage for better performance
4. Replace Hive jobs with BigQuery scheduled queries or Dataflow

**Path B: Full re-platform**
1. Transform data during migration (use Dataflow or Dataproc to clean and reformat)
2. Load directly into BigQuery native tables
3. Rewrite Hive queries as BigQuery SQL

---

## Google's Migration Tooling

### BigQuery Migration Service (BQMS)

**The most important tool to know about.**

BQMS is a suite of tools in the Cloud Console that automates:

1. **Schema Assessment:** Scan a database, list all objects, estimate migration complexity
2. **SQL Translation (Batch):** Submit a folder of SQL files → BQMS outputs translated BigQuery SQL
3. **Interactive SQL Translation:** Paste one query → get BigQuery SQL in real time
4. **Migration Workflow:** End-to-end guided workflow: assess → translate → migrate → validate

**Supported sources:**
- Amazon Redshift
- Apache HiveQL
- Teradata (BTEQ, SQL, DDL)
- Oracle
- SQL Server (T-SQL)
- MySQL / PostgreSQL
- Snowflake (SQL dialect)

```bash
# Example: batch translate Teradata SQL files to BigQuery SQL
gcloud migration translation batch-translate-queries \
  --source-location=gs://my-bucket/teradata-sql/ \
  --target-location=gs://my-bucket/bq-sql/ \
  --source-dialect=TERADATA \
  --target-dialect=BIGQUERY
```

**What it can't do:**
- 100% translation (complex stored procedures may need manual rework)
- Migrate application code that embeds SQL (Java/.NET apps)
- Validate results (you still need to compare outputs)

### Datastream (CDC for Live Migration)

When you need to migrate a live production database with minimal downtime:

```
Source DB (Oracle/MySQL/PostgreSQL/SQL Server/AlloyDB)
      ↓
Datastream (captures change data in real time — CDC)
      ↓
BigQuery (streams inserts/updates/deletes continuously)
```

- Zero downtime migration: migrate historical data, then stream ongoing changes
- BigQuery automatically deduplicates and handles updates via merge
- **Use case:** Migrate an OLTP database to BigQuery for analytics while it's still running

### Storage Transfer Service

Move large data volumes to GCS as a prerequisite for BigQuery loading:

- AWS S3 → GCS (for Redshift unload files)
- Azure Blob → GCS
- On-prem HDFS → GCS (via agent)
- Scheduled or one-time transfers

### Database Migration Service (DMS)

For migrating databases to Cloud SQL or AlloyDB (PostgreSQL, MySQL, SQL Server) — not directly to BigQuery, but often the first step in a pipeline where Cloud SQL feeds BigQuery via Datastream.

---

## Migration Patterns

### Pattern 1: Batch "Lift and Load"

```
Source DB/Warehouse
      ↓
Export/Unload to GCS (CSV, Parquet, Avro)
      ↓
BigQuery Load Job (bq load)
      ↓
Validate (row counts, checksums)
```

**Best for:** Historical/archive data, cold migration, development/staging environments

### Pattern 2: Streaming / Live Migration (Zero Downtime)

```
Source DB (still live in production)
      ↓
Datastream (CDC — captures ongoing changes)
      ↓
BigQuery (live replica)
      ↓ (when ready to cut over)
Switch application traffic → BigQuery is now source of truth
Decommission source system
```

**Best for:** Databases that can't afford downtime, live OLTP-to-analytics pipelines

### Pattern 3: Phased Migration (Wave Approach)

```
Wave 1: Migrate dev/test (low risk, build team confidence)
Wave 2: Migrate non-critical production workloads
Wave 3: Migrate critical workloads (parallel run — validate outputs)
Wave 4: Cut over to BigQuery, decommission legacy system
```

**Best for:** Large enterprises with complex, high-risk environments

---

## Migration Validation

Never declare migration success without validation. Use these methods:

```sql
-- 1. Row count validation
SELECT COUNT(*) FROM legacy_table;       -- Teradata/Redshift
SELECT COUNT(*) FROM `proj.dataset.table`;  -- BigQuery
-- Must match exactly

-- 2. Aggregate validation (check sums, not just counts)
SELECT
  SUM(revenue) as total_revenue,
  COUNT(DISTINCT user_id) as unique_users,
  MIN(order_date) as first_order,
  MAX(order_date) as last_order
FROM legacy_table;
-- Run same query on BigQuery, compare results

-- 3. Sample row comparison
SELECT * FROM legacy_table ORDER BY id LIMIT 100;
-- Compare with BigQuery output for same IDs

-- 4. Schema validation
-- Compare column names, types, nullability between source and BigQuery
```

---

## Objection Handling — Migration Specific

**"Migration is too risky. What if something breaks?"**
> "We de-risk by running in parallel — BigQuery runs alongside the legacy system for a validation period. We only cut over when row counts and aggregate numbers match exactly. The legacy system stays live as a fallback until the team is confident."

**"Our SQL is very complex and proprietary — it won't translate."**
> "BQMS typically translates 70-90% automatically. The remaining 10-30% is flagged for manual review — it's not a black box. Google's Professional Services team specializes in this for Teradata migrations specifically. And you're migrating once — the investment is worth it to escape the license cost."

**"We just renewed our Snowflake/Redshift contract."**
> "Perfect time to start the technical evaluation so you're ready at renewal. We can set up a Proof of Concept in parallel — bring your three most complex queries, we'll run them on BigQuery and show you the performance and cost comparison. Zero commitment."

**"We don't have the team capacity to run a migration."**
> "Google has a Migration Center program, and most System Integrator partners (Accenture, SADA, Deloitte) specialize in this. We can co-deliver or bring in an SI. The migration itself is often funded through the TCO savings in the first year."

**"What about our BI tools? Everything talks to Teradata today."**
> "BigQuery has a native JDBC/ODBC driver. Tableau, Power BI, Looker, Qlik — all connect without changes to reports. For Looker specifically, it's even better — Looker is built on BigQuery and unlocks semantic modeling that Teradata can't offer."

---

## The TCO Argument (Numbers to Know)

| Platform | Typical Cost Model | Benchmark |
|---------|-------------------|-----------|
| Teradata on-prem | License + hardware + DBA staff | $500K–$5M/year all-in |
| Teradata on cloud | License + VM compute | ~$300K–$2M/year |
| Amazon Redshift | Node-based compute + storage | ~$50K–$500K/year |
| Snowflake | Per-second compute + storage | ~$50K–$500K/year |
| **BigQuery (on-demand)** | $6.25/TB scanned + $0.02/GB storage | Highly variable — often 40-60% cheaper |
| **BigQuery (reservations)** | $1,700–$2,100/slot/month | Predictable; reserve for steady workloads |

**Key TCO advantages of BigQuery:**
1. No license fee (unlike Teradata)
2. No cluster to provision or resize
3. No DBA required (no vacuuming, indexing, stats collection)
4. No idle cost — on-demand means you only pay when queries run
5. Built-in disaster recovery, replication, backups at no extra cost

---

## Quick Reference — Migration Tool Map

```
Need to...                              Use...
─────────────────────────────────────────────────────
Translate SQL from Teradata/Redshift   BigQuery Migration Service (BQMS)
Move files from S3/Azure/HDFS to GCS  Storage Transfer Service
Stream live DB changes to BigQuery     Datastream (CDC)
Load GCS files into BigQuery           bq load / BigQuery Data Transfer
Migrate MySQL/Postgres to Cloud SQL    Database Migration Service (DMS)
Assess migration complexity            BQMS Assessment
Validate migration results             SQL row count + aggregate comparison
Orchestrate multi-step migration ETL   Cloud Composer (Airflow)
```

---

## Practice Q&A

**Q1: A customer has 200 Teradata BTEQ scripts. How do you approach the SQL migration?**
<details><summary>Answer</summary>
Use BigQuery Migration Service batch translation — submit all BTEQ files to BQMS and it auto-translates to BigQuery SQL. Typically 70-90% translates automatically. BQMS flags the rest with error details for manual rework. Use the BQMS assessment first to understand complexity before committing to a timeline.
</details>

**Q2: A customer needs to migrate their production Oracle database to BigQuery with zero downtime. What's the architecture?**
<details><summary>Answer</summary>
Use Datastream for CDC (change data capture). Datastream reads the Oracle redo log, captures all inserts/updates/deletes in real time, and streams them to BigQuery. During the migration window, migrate historical data and let Datastream catch up. When BigQuery is in sync, cut over application traffic. The old Oracle system stays live as a fallback.
</details>

**Q3: What is BigQuery Migration Service and what does it do?**
<details><summary>Answer</summary>
BQMS is a suite of tools in Cloud Console for automated migration: it assesses source databases (inventory of objects, complexity), batch-translates SQL files from Teradata/Redshift/Hive/Oracle to BigQuery SQL, and provides an interactive query translator for testing. It supports most major source platforms.
</details>

**Q4: A customer asks "how long does a Teradata migration take?" How do you answer?**
<details><summary>Answer</summary>
It depends on scope, but a typical enterprise Teradata migration runs 6-9 months in waves: month 1-2 assessment and translation, month 3-4 dev/test migration, month 5-6 ETL re-platforming and parallel run, month 7-8 production cutover. Smaller shops can do it in 3-4 months.
</details>

**Q5: Why would a happy Snowflake customer consider BigQuery?**
<details><summary>Answer</summary>
Three differentiators: (1) Native AI/ML — BigQuery ML and Vertex AI integrate without data movement; (2) Governance — Dataplex Universal Catalog is deeper and more automated than Snowflake's governance story; (3) Looker — native semantic layer that works best on BigQuery. Position with a PoC using their most complex queries.
</details>
