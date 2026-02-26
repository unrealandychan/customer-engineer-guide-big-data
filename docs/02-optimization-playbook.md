# 💰 BigQuery & Dataproc — Cost & Performance Optimization Playbook

> Use this as your reference for deep-dive optimization questions in the interview.  
> Always frame optimizations in **business terms** before going technical.

---

## Part 1: BigQuery Optimization

### 🧠 Mental Model

> BigQuery costs are dominated by **bytes scanned** (on-demand) or **slot utilization** (flat-rate).  
> Almost all optimizations = scan less data + manage compute capacity intelligently.

---

### 1.1 Table Design — Partitioning

**What it does:** Divides a table into segments by a key (date, timestamp, integer). Queries that filter on the partition key skip entire segments.

**Business pitch:** *"Partitioning lets BigQuery only read the slices of data a query actually needs. Customers routinely see 10x less data scanned vs unpartitioned tables."*

| Partition Type | When to Use |
|----------------|------------|
| Date/Timestamp column | Most analytical event/log tables |
| Ingestion time | When no business date column exists |
| Integer range | Custom bucketing (e.g., customer ID ranges) |

**Key tactics:**
- Partition on the column most frequently used in range filters (e.g., `event_date`, `order_date`)
- Daily granularity is the most common — avoid hourly unless extremely high volume
- Avoid wrapping partition column in functions (`DATE(ts)`) — breaks pruning
- Use `require_partition_filter = TRUE` on large tables to prevent accidental full scans
- Set partition expiration for data lifecycle: `partition_expiration_days = 365`
- Avoid over-partitioning (>4,000 partitions adds metadata overhead)

---

### 1.2 Table Design — Clustering

**What it does:** Sorts data within each partition by up to 4 columns. Enables **block pruning** — BigQuery skips blocks outside your filter range.

**Business pitch:** *"Clustering and partitioning together keep dashboards fast and costs predictable as data grows."*

**Key tactics:**
- Cluster on columns frequently used in `WHERE`, `JOIN`, `GROUP BY` (e.g., `user_id`, `country`, `campaign_id`)
- Combine with partitioning: `PARTITION BY event_date CLUSTER BY user_id, campaign_id`
- BigQuery auto-recluters in the background as new data arrives
- Avoid clustering on low-cardinality columns with no selectivity benefit

**Partitioning vs Clustering:**

| | Partitioning | Clustering |
|--|--------------|------------|
| Granularity | Whole segments | Blocks within segments |
| Best for | Time-range queries | Multi-dimension filters |
| Combine? | ✅ Yes, stack both | ✅ Yes, stack both |

---

### 1.3 Table Design — Avoid Sharding (Legacy Anti-Pattern)

- ❌ **Legacy:** `events_20250101`, `events_20250102` (date-sharded tables)
- ✅ **Better:** Single table `events` partitioned by `event_date`

Benefits of migration:
- Simpler queries (no `_TABLE_SUFFIX` hacks)
- Better query optimization statistics
- Native partition pruning
- **Positioning opportunity:** Offer this as a quick win in a cost-optimization engagement

---

### 1.4 Query Optimization

| Anti-Pattern | Fix |
|-------------|-----|
| `SELECT *` | Select only needed columns — up to 8x bytes reduction |
| No partition filter | Always filter on partition column in `WHERE` |
| `LIMIT` for cost control | ⚠️ LIMIT does NOT reduce bytes scanned — only use for dev |
| Repeated heavy aggregations | Create materialized views or summary tables |
| Full reloads in ETL | Use incremental models (only process new/changed data) |
| Functions on partition key | `WHERE DATE(ts) = ...` → breaks pruning; use `WHERE ts_date = ...` |

**Additional tactics:**
- Use query result caching: identical queries within 24 hours are free
- For exploration/dev: use `TABLESAMPLE` to scan a fraction of data
- Pre-aggregate heavy metrics into summary tables that dashboards query

---

### 1.5 Pricing Strategy: On-Demand vs Flat-Rate

| Mode | Best For | Risk |
|------|----------|------|
| On-demand (per TB scanned) | Ad-hoc, variable workloads | Cost spikes from unoptimized queries |
| Flat-rate / Reservations (slots) | Steady, predictable heavy workloads | Wasted spend if slots are underutilized |

**Recommended approach:**
1. Start all customers on on-demand
2. Monitor for 30–90 days to understand usage patterns
3. Move predictable, heavy workloads to slot reservations
4. Use separate reservations for ETL (batch) vs BI (interactive)

---

### 1.6 Governance & Monitoring

- Export billing to BigQuery itself → build cost dashboards
- Use `INFORMATION_SCHEMA.JOBS_BY_PROJECT` to identify the top-cost queries
- Set **budget alerts** per project and per team
- Use **BigQuery Recommender** — analyses 30 days of workload history → suggests partition/cluster changes with estimated savings
- Enforce `require_partition_filter` on large tables via organization policy

---

### 1.7 BigQuery Optimization — 3-Layer Interview Answer

**Layer 1 (Business):**
> "BigQuery costs come from data scanned. We optimize by designing tables and queries to scan as little data as possible."

**Layer 2 (Technical):**
> "The three main levers are: partitioning (skip whole time ranges), clustering (skip blocks within partitions), and query hygiene — avoiding SELECT *, filtering on partition keys, using incremental models. For pricing, we move predictable workloads to slot reservations."

**Layer 3 (Example):**
> "For a 10TB daily event log: partition by `event_date`, cluster by `user_id`. A query for last 7 days for US users goes from scanning 10TB to maybe 200GB — a 50x improvement that directly reduces cost and latency."

---

## Part 2: Dataproc Optimization

### 🧠 Mental Model

> Dataproc costs = VM time × VM cost. Optimization = use the right amount of compute at the right time + make Spark jobs efficient.

---

### 2.1 Cluster Strategy: Ephemeral vs Long-Lived

| Strategy | When to Use | Key Benefit |
|----------|------------|-------------|
| **Ephemeral** (spin up → job → tear down) | Batch ETL, periodic ML, ad-hoc | No idle costs — pay per-second |
| **Long-lived** | Continuous analytics, interactive notebooks | Avoid startup latency |

**Business pitch:**
> "Dataproc clusters start in minutes and bill per second. Many customers treat them as just-in-time compute — clusters appear for a batch job and disappear right after."

**Recommendation:** Default to ephemeral for batch workloads. Use autoscaling for long-lived clusters.

---

### 2.2 Autoscaling + Preemptible Workers

**Autoscaling:**
- Scales cluster up when YARN has pending memory (jobs queued)
- Scales down during idle periods (with cooldown to avoid thrashing)
- Configure: scale-up/down bounds, cooldown period, separate policy per cluster type

**Preemptible Workers:**
- Secondary workers that can be reclaimed by GCP at any time (with notice)
- Significant cost reduction — suitable for fault-tolerant jobs (ETL, batch transforms with retry)
- Typical savings: **18–60% TCO vs other cloud Spark platforms**

**Recommended patterns:**

| Workload | Configuration |
|----------|--------------|
| Batch ETL (fault-tolerant) | Small regular + many preemptibles + autoscaling |
| Critical production job | Mostly regular workers, fewer preemptibles, autoscaling |
| Interactive/notebook | Long-lived, regular workers, autoscaling with moderate bounds |

---

### 2.3 Right-Sizing Clusters

- Start **smaller** than you think — watch YARN CPU/memory utilization, then scale
- Small, reliable masters (e.g., `n2-standard-2`) — don't over-provision master
- Workers: CPU vs memory ratio depends on workload (Spark shuffles → more memory; simple transforms → balanced)
- Consider **Dataproc Serverless Spark** for workloads where cluster management is a burden

---

### 2.4 Storage: GCS over HDFS

- Store all data in **Cloud Storage** — decouples compute and storage
- Enables ephemeral clusters without data loss
- Co-locate data and compute in the **same region** — avoids network egress costs
- Use BigQuery connector to write aggregated results to BigQuery for serving

**Business pitch:**
> "Instead of maintaining large HDFS clusters, we land data in Cloud Storage and treat Dataproc as on-demand compute. This combination cuts infra and ops costs while making curated data available to BigQuery for analytics."

---

### 2.5 Spark Job-Level Optimization

| Optimization | Detail |
|-------------|--------|
| Enable Dataproc performance enhancements | Google-managed Spark engine improvements — free, no code changes |
| `spark.sql.shuffle.partitions` | Reduce from default 1000 for small-medium jobs |
| Dynamic allocation | Scales executors with workload within the cluster |
| Avoid data skew | Repartition, salt keys, use `AQE` (Adaptive Query Execution) |
| Cache intermediate DataFrames | For iterative algorithms or re-used intermediate results |
| Filter and project early | Reduce data volume flowing through the pipeline ASAP |
| Cluster caching | Reduce GCS re-reads for repeated scans |

---

### 2.6 Cost Attribution & Monitoring

- **Label** every cluster and job: `team=analytics`, `env=prod`, `pipeline=daily-etl`
- Export billing → build per-team, per-pipeline cost dashboards
- Alert on job runtime anomalies (e.g., a job that usually takes 20 min now takes 3 hrs)
- Identify long-lived clusters with low CPU utilization as consolidation candidates

---

### 2.7 Dataproc Optimization — 3-Layer Interview Answer

**Layer 1 (Business):**
> "Dataproc optimization is about using compute only when needed, at the right size, and making Spark jobs do less work."

**Layer 2 (Technical):**
> "The main levers are: ephemeral clusters to avoid idle costs, preemptible workers for fault-tolerant batch jobs (18–60% savings), autoscaling to match demand, and Spark tuning including Dataproc's built-in performance enhancements."

**Layer 3 (Example):**
> "For a customer's nightly Hadoop ETL, we'd migrate to Dataproc, store data in GCS instead of HDFS, run ephemeral clusters with 20% regular workers + 80% preemptibles, and submit the Spark job via Cloud Composer. The cluster exists for ~2 hours, then tears down — paying for 2 hours vs having on-prem or always-on cloud clusters 24/7."

---

## Part 3: Optimization in Pre-Sales Conversations

### Common Client Question: "How do we control BigQuery costs?"

**Response structure:**
1. Acknowledge: *"Great question — unoptimized cloud warehouses can get expensive."*
2. Diagnosis: *"First, we export billing data to understand which queries/datasets drive most spend."*
3. Table fixes: *"Then we redesign hot tables with partitioning and clustering — typically cuts scan volume 10–50x."*
4. Query fixes: *"We also help teams adopt query hygiene practices and incremental models."*
5. Pricing: *"Once patterns stabilize, we can evaluate slot reservations for predictable workloads."*
6. Offer: *"If you share volume and query patterns, we can sketch an optimized architecture and estimate savings."*

### Common Client Question: "Is Dataproc cheaper than our on-prem Hadoop?"

**Response structure:**
1. Acknowledge: *"It depends on your utilization — let's look at total cost of ownership, not just compute."*
2. TCO frame: *"On-prem includes hardware lifecycle, power, cooling, ops headcount, and patching. Those are often invisible costs."*
3. Evidence: *"ESG's economic analysis found Dataproc can be 50%+ cheaper TCO vs on-prem Hadoop and 30–50% vs some cloud Spark alternatives."*
4. Levers: *"Ephemeral clusters + preemptibles + per-second billing are the main drivers."*
5. Offer: *"We can do a rough TCO comparison if you share your cluster specs and utilization patterns."*
