# 🚀 Google Pre-Sales Interview Prep — GCP Data & Analytics

> A structured preparation repository for a **Google Cloud Pre-Sales Engineer** interview  
> focused on **BigQuery**, **Dataproc**, and the broader GCP data ecosystem.

---

## 📌 About This Repo

This repo consolidates study notes, interview guidelines, optimization playbooks, objection-handling scripts, and whiteboard practice questions — all tuned for a **pre-sales role** where you must demonstrate both technical depth and business storytelling.

**Interview context:**
- Role: Pre-Sales Engineer / Solutions Consultant at Google Cloud
- Topics: BigQuery · Dataproc · Dataflow/Beam · GCP Data Stack · Streaming · Cost Optimization
- Background assumed: Senior engineer with AWS experience transitioning to GCP

---

## 📁 Repository Structure

```
project-g/
├── README.md                           ← You are here
├── docs/
│   ├── 00-guideline.md                 ← Role framing, answer framework, AWS→GCP map
│   ├── 01-study-plan.md                ← 7-day structured study plan + verbal prompts
│   ├── 02-optimization-playbook.md     ← BigQuery & Dataproc cost/performance deep dive
│   ├── 03-objection-handling.md        ← Client objection scripts + discovery questions
│   ├── 04-whiteboard-questions.md      ← 6 whiteboard scenarios with full solutions
│   ├── 05-streaming-analytics.md       ← Streaming: Pub/Sub, Dataflow, Beam, Flink
│   ├── 06-gaps-quick-reference.md      ← Storage Write API, MVs, BI Engine, Dataplex, Composer
│   ├── 07-star-stories-template.md     ← STAR-G behavioral framework + 6 story templates
│   ├── 08-business-case-tco.md         ← TCO framework, competitive positioning, CFO template
│   ├── 09-big-data-topics-2026.md      ← NEW: BQ Editions, Global Queries, AI Functions, Dremel
│   ├── 10-google-whitepaper-study-guide.md ← NEW: MapReduce, Dremel, Bigtable, Spanner papers
│   ├── 11-bigquery-from-scratch.md     ← FROM SCRATCH: BigQuery fundamentals
│   ├── 12-dataproc-from-scratch.md     ← FROM SCRATCH: Dataproc fundamentals
│   ├── 13-bigquery-migration.md        ← NEW: Migration strategies, schema translation, data transfer
│   ├── 14-data-governance.md           ← NEW: Dataplex, Data Catalog, IAM, row/column-level security
│   ├── 15-competitive-intelligence.md  ← NEW: BigQuery vs Snowflake/Databricks/Redshift, Dataproc vs EMR
│   ├── 16-ingestion-and-orchestration.md ← NEW: Datastream (CDC), Cloud Composer (Airflow), Data Fusion, Data Transfer Service, ELT architecture
│   ├── 17-looker-and-bi.md             ← NEW: LookML Semantic Layer, In-Database Architecture, Looker vs Looker Studio, BI Engine
│   ├── 18-alloydb-and-spanner.md       ← NEW: AlloyDB (HTAP, Aurora killer), Spanner (Global consistency), BigQuery Federated Queries
│   └── 19-vertex-ai-bqml-mlops.md      ← NEW: BQML (SQL-based ML), Vertex AI Model Registry, Endpoints, GenAI/RAG on BigQuery
├── bq-course/                          ← 6-part deep dive into BigQuery
├── dataproc-course/                    ← 6-part deep dive into Dataproc
├── dataflow-beam-course/               ← 6-part deep dive into Dataflow/Beam
├── exercises/
│   ├── 01-bigquery-python/             ← BQ Python client (7 exercises)
│   ├── 02-bigquery-go/                 ← BQ Go client (2 exercises)
│   ├── 03-dataproc-pyspark/            ← PySpark ETL + streaming (2 exercises)
│   ├── 04-pubsub-python/               ← Pub/Sub publish/subscribe
│   ├── 05-pubsub-go/                   ← Pub/Sub in Go
│   ├── 06-dataflow-beam-python/        ← Apache Beam batch + streaming pipelines
│   ├── 07-terraform-gcp/               ← IaC for BQ, Dataproc, Pub/Sub, GCS, full pipeline
│   ├── 08-gcs-python-go/               ← Cloud Storage operations in Python + Go
│   └── 09-advanced-bigquery-ai/        ← NEW: AI.GENERATE, Dremel, Global Queries, Editions
├── soft-skills/
│   ├── README.md                       ← Orientation, mental model, 7-day practice routine
│   ├── 01-pushback-handling.md         ← 15 real pushback scenarios with VERA responses
│   ├── 02-discovery-conversation.md    ← SPIN, question laddering, needs mapping, active listening
│   ├── 03-whiteboard-facilitation.md   ← Running whiteboard sessions under pressure
│   ├── 04-difficult-personas.md        ← 8 customer archetypes + adaptation strategies
│   ├── 05-communication-frameworks.md  ← Pyramid Principle, SCQA, ELI5, Rule of Three
│   └── 06-roleplay-scripts.md          ← 4 full mock conversation scripts
└── markdown/
    └── I am having a big interview with Google , topic ab.md   ← Original source material
```

---

## 🗂️ Document Index

| File | What's Inside | Priority |
|------|--------------|----------|
| [`00-guideline.md`](docs/00-guideline.md) | Role framing, topic coverage map, answer framework (3-layer), AWS→GCP map, success checklist | ⭐⭐⭐ Read first |
| [`01-study-plan.md`](docs/01-study-plan.md) | Day-by-day tasks, hands-on goals, verbal practice prompts for each day | ⭐⭐⭐ Core plan |
| [`02-optimization-playbook.md`](docs/02-optimization-playbook.md) | Deep-dive: partitioning, clustering, query hygiene, slot strategy, Dataproc cost tactics | ⭐⭐⭐ High ROI |
| [`03-objection-handling.md`](docs/03-objection-handling.md) | 6 client objections with structured responses, discovery questions, in-whiteboard pushbacks | ⭐⭐⭐ Pre-sales key |
| [`04-whiteboard-questions.md`](docs/04-whiteboard-questions.md) | 6 full whiteboard scenarios with step-by-step solutions and pushback handling | ⭐⭐⭐ Practice daily |
| [`05-streaming-analytics.md`](docs/05-streaming-analytics.md) | Streaming concepts, BigQuery/Spark/Flink/Beam comparison, GCP patterns | ⭐⭐ Breadth |
| [`06-gaps-quick-reference.md`](docs/06-gaps-quick-reference.md) | Storage Write API, Materialized Views, BI Engine, Dataplex, Composer, BigQuery Omni, Vertex AI/BQML, key pricing numbers | ⭐⭐⭐ Gap-fill |
| [`07-star-stories-template.md`](docs/07-star-stories-template.md) | STAR-G framework, 6 behavioral question templates, analogy table, 30-second rule | ⭐⭐⭐ Must-do |
| [`08-business-case-tco.md`](docs/08-business-case-tco.md) | TCO narrative, whiteboard business case template, on-demand vs flat-rate guide, BQ vs Snowflake/Databricks/Redshift | ⭐⭐⭐ Closes deals |
| [`09-big-data-topics-2026.md`](docs/09-big-data-topics-2026.md) | **NEW** BQ Editions, Global Queries (Feb 2026), AI.GENERATE/EMBED/SIMILARITY/SEARCH, Autonomous Embeddings, Iceberg, Dremel numbers | ⭐⭐⭐ Hot topics |
| [`10-google-whitepaper-study-guide.md`](docs/10-google-whitepaper-study-guide.md) | **NEW** MapReduce, Bigtable, Dremel, GFS/Colossus, Spanner, Mesa — paper summaries + interview soundbites + paper links | ⭐⭐⭐ HR required |
| [`11-bigquery-from-scratch.md`](docs/11-bigquery-from-scratch.md) | **FROM SCRATCH** Columnar storage, Dremel execution tree, Capacitor format, ingestion paths, SQL examples, partitioning + clustering, pricing, IAM, interview answers | ⭐⭐⭐ Fundamentals |
| [`12-dataproc-from-scratch.md`](docs/12-dataproc-from-scratch.md) | **FROM SCRATCH** MapReduce model, Spark RDDs/DAG/stages/shuffle, YARN, ephemeral clusters, preemptible workers, autoscaling, PySpark code guide, Dataproc vs BigQuery vs Dataflow | ⭐⭐⭐ Fundamentals |
| [`13-bigquery-migration.md`](docs/13-bigquery-migration.md) | **NEW** Migration strategies, schema translation, data transfer, validation, and cutover planning | ⭐⭐⭐ Migration |
| [`14-data-governance.md`](docs/14-data-governance.md) | **NEW** Dataplex, Data Catalog, IAM, row/column-level security, data lineage, and quality | ⭐⭐⭐ Governance |
| [`15-competitive-intelligence.md`](docs/15-competitive-intelligence.md) | **NEW** BigQuery vs Snowflake/Databricks/Redshift, Dataproc vs EMR, Dataflow vs MSK/Kinesis | ⭐⭐⭐ Competitive |
| [`16-ingestion-and-orchestration.md`](docs/16-ingestion-and-orchestration.md) | **NEW** Datastream (CDC), Cloud Composer (Airflow), Data Fusion, Data Transfer Service, ELT architecture | ⭐⭐⭐ Architecture |
| [`17-looker-and-bi.md`](docs/17-looker-and-bi.md) | **NEW** LookML Semantic Layer, In-Database Architecture, Looker vs Looker Studio, BI Engine | ⭐⭐⭐ BI & Value |
| [`18-alloydb-and-spanner.md`](docs/18-alloydb-and-spanner.md) | **NEW** AlloyDB (HTAP, Aurora killer), Spanner (Global consistency), BigQuery Federated Queries | ⭐⭐ Databases |
| [`19-vertex-ai-bqml-mlops.md`](docs/19-vertex-ai-bqml-mlops.md) | **NEW** BQML (SQL-based ML), Vertex AI Model Registry, Endpoints, GenAI/RAG on BigQuery | ⭐⭐⭐ AI/MLOps |

### 🎓 Deep Dive Courses

| Course | What's Inside | Priority |
|--------|--------------|----------|
| [`bq-course/`](bq-course/README.md) | 6-part deep dive into BigQuery: Storage, Schema, Querying, Partitioning/Clustering, Pricing/Ops | ⭐⭐⭐ Core Tech |
| [`dataproc-course/`](dataproc-course/README.md) | 6-part deep dive into Dataproc: Spark, Architecture, Cluster Management, PySpark, Optimization | ⭐⭐⭐ Core Tech |
| [`dataflow-beam-course/`](dataflow-beam-course/README.md) | 6-part deep dive into Dataflow/Beam: Concepts, Transforms, Streaming/Windowing, Python Pipelines, Ops | ⭐⭐⭐ Core Tech |

### 🤝 Soft Skills Practice Lab (`soft-skills/`)

| File | What's Inside | Priority |
|------|--------------|----------|
| [`soft-skills/README.md`](soft-skills/README.md) | Orientation, "Doctor not Salesperson" mental model, 5 core skills, 7-day routine | ⭐⭐⭐ Read first |
| [`soft-skills/01-pushback-handling.md`](soft-skills/01-pushback-handling.md) | 15 real GCP pushback scenarios (pricing, lock-in, AWS loyalty, bad experience…) with full VERA-framework responses | ⭐⭐⭐ Highest priority |
| [`soft-skills/02-discovery-conversation.md`](soft-skills/02-discovery-conversation.md) | SPIN questioning, question laddering, the 5 Whys, 30-min call structure, needs mapping template, active listening signals | ⭐⭐⭐ Core skill |
| [`soft-skills/03-whiteboard-facilitation.md`](soft-skills/03-whiteboard-facilitation.md) | Taking control of the pen, 5-zone layout, handling interruptions, Anchor & Bridge, time management, practice drills | ⭐⭐ Must practice |
| [`soft-skills/04-difficult-personas.md`](soft-skills/04-difficult-personas.md) | 8 archetypes: Skeptic, Deep Technical, CFO, Silent Evaluator, Competitor Fan, Overtalker, Decision-Maker in a Hurry, Champion | ⭐⭐⭐ Read before any meeting |
| [`soft-skills/05-communication-frameworks.md`](soft-skills/05-communication-frameworks.md) | Pyramid Principle, SCQA, ELI5 bridging, SBI feedback model, Pause-Breathe-Frame, Rule of Three, 30-second rule | ⭐⭐⭐ Apply every day |
| [`soft-skills/06-roleplay-scripts.md`](soft-skills/06-roleplay-scripts.md) | 4 full mock conversations: discovery call, skeptical deep-dive, pushback-heavy exec presentation, whiteboard gone off-track | ⭐⭐⭐ Practice out loud |

---

## ⚡ Quick Start

### If you have 7 days
Follow [`01-study-plan.md`](docs/01-study-plan.md) day by day.

### If you have 3–4 days
| Day | Focus |
|-----|-------|
| 1 | Read `00-guideline.md` + GCP landscape + BigQuery SQL hands-on |
| 2 | `02-optimization-playbook.md` (BigQuery) + 2 pipeline designs from `04-whiteboard-questions.md` |
| 3 | `02-optimization-playbook.md` (Dataproc) + Dataflow/Beam from `05-streaming-analytics.md` |
| 4 | All of `03-objection-handling.md` + full mock interview from `04-whiteboard-questions.md` |

### If you have 1 day
1. Read `00-guideline.md` (role framing + key concepts)
2. Read `03-objection-handling.md` (objections + discovery questions)
3. Skim `04-whiteboard-questions.md` Q1, Q3, Q6 (most likely to come up)
4. Memorize the 3-layer answer framework

---

## 🧠 Key Concepts Cheat Sheet

### BigQuery in 3 Sentences
> BigQuery is Google Cloud's fully managed, serverless, columnar data warehouse that separates storage and compute. It lets teams query terabytes to petabytes with standard SQL in seconds — without provisioning any infrastructure. Cost is driven by bytes scanned, so partitioning and clustering are the primary tools for both performance and cost control.

### Dataproc in 3 Sentences
> Dataproc is Google Cloud's managed Hadoop, Spark, and Flink service — the GCP equivalent of AWS EMR. It enables lift-and-shift migrations from on-prem Hadoop/Spark with minimal code changes, while decoupling compute from storage using Cloud Storage instead of HDFS. Per-second billing, ephemeral clusters, and preemptible workers typically deliver 18–60% TCO reduction versus on-prem or alternative cloud Spark platforms.

### Dataflow/Beam in 2 Sentences
> Apache Beam is a unified programming model for batch and streaming pipelines; Cloud Dataflow is Google's fully managed, serverless runner for Beam. Dataflow is the GCP-native choice for cloud-native streaming or batch pipelines where you don't want to manage clusters.

### The Core Trade-Off (Memorize This)
| Choose... | When... |
|-----------|---------|
| **BigQuery** | SQL-friendly transforms, BI analytics, analysts as primary users |
| **Dataflow** | New cloud-native streaming or batch pipelines, no cluster ops wanted |
| **Dataproc** | Existing Spark/Hadoop workloads, custom Spark libraries, lift-and-shift |

---

## 💬 Pre-Sales Answer Framework

Apply this to every technical question:

```
1. Business impact (1 sentence)
   "This helps reduce analytics cost and speeds up decisions."

2. Technical explanation (2–4 sentences)
   "BigQuery's partitioning divides a table by date — so queries
   only scan the relevant time range instead of the full table."

3. Concrete example (if probed)
   "A 10TB events table partitioned by event_date and clustered
   by user_id scans ~200GB for a 7-day user query — 50x less data."

→ Pivot back to business value:
   "That's why dashboard load times stay fast and costs stay
   predictable even as data grows."
```

---

## 🔑 AWS → GCP Quick Reference

| AWS | GCP Equivalent |
|-----|---------------|
| S3 | Cloud Storage |
| Redshift / Athena | BigQuery |
| EMR | Dataproc |
| Kinesis | Pub/Sub |
| Glue ETL | Dataflow / Data Fusion |
| MWAA / Step Functions | Cloud Composer |
| MSK (Managed Kafka) | Pub/Sub or Managed Kafka on GCP |
| CloudWatch | Cloud Monitoring + Cloud Logging |
| Glue Data Catalog | Data Catalog / Dataplex |
| SageMaker | Vertex AI |

---

## 📊 Top 5 Client Objections (Summary)

| Objection | Key Response |
|-----------|-------------|
| "We're on AWS/Azure already" | Multi-cloud is normal; GCP wins on data + AI — start with a focused analytics use case |
| "BigQuery is expensive" | TCO framing: no infra ops; partitioning/clustering cuts query cost 50–80% |
| "We run Spark/Hadoop on-prem" | Phase 1 lift-and-shift to Dataproc (minimal code changes); Phase 2 modernize to BQ |
| "We're worried about lock-in" | Open formats (Parquet/Iceberg) on GCS, standard SQL, open-source engines |
| "We don't have enough engineers" | BigQuery is serverless; BigQuery ML and Gemini reduce specialist dependency |

Full responses with scripts → [`03-objection-handling.md`](docs/03-objection-handling.md)

---

## 🏋️ Practice Checklist

Work through these before the interview:

- [ ] Explain BigQuery in 30 seconds (elevator pitch) and 3 minutes (whiteboard)
- [ ] Explain Dataproc and the "Dataproc vs Dataflow vs BigQuery" trade-off
- [ ] Design a streaming pipeline end-to-end out loud (Q1 in `04-whiteboard-questions.md`)
- [ ] Design a batch ETL pipeline end-to-end out loud (Q2 in `04-whiteboard-questions.md`)
- [ ] Handle all 5 objections in `03-objection-handling.md` out loud
- [ ] Articulate BigQuery optimization strategy (top 4 levers)
- [ ] Articulate Dataproc cost optimization strategy (top 3 levers)
- [ ] Run a 45-min mock interview using Q1 or Q5 from `04-whiteboard-questions.md`
- [ ] Have 3 STAR format stories ready (system design win, cost reduction, debugging)
- [ ] Prepare 5 smart discovery questions you'd ask a new client
- [ ] **NEW** Explain BigQuery Editions (Standard vs Enterprise vs Enterprise Plus vs On-Demand)
- [ ] **NEW** Explain Global Queries — when and why a customer needs it
- [ ] **NEW** Explain `AI.GENERATE`, `AI.EMBED`, `AI.SIMILARITY` in plain English
- [ ] **NEW** Describe Dremel's two innovations (columnar nested storage + multi-level execution tree)
- [ ] **NEW** Explain all 6 foundational Google papers with 1 soundbite each (see `10-google-whitepaper-study-guide.md`)
- [ ] **NEW** Answer: "Why does BigQuery charge by bytes scanned, not compute time?"
- [ ] **NEW** Run exercises in `09-advanced-bigquery-ai/` (AI functions + Dremel concepts)
- [ ] **NEW** Review BigQuery migration strategies and schema translation (`13-bigquery-migration.md`)
- [ ] **NEW** Understand Data Governance with Dataplex and Data Catalog (`14-data-governance.md`)
- [ ] **NEW** Prepare competitive positioning against Snowflake, Databricks, and Redshift (`15-competitive-intelligence.md`)
- [ ] **NEW** Architect an ELT pipeline using Datastream, Composer, and BigQuery (`16-ingestion-and-orchestration.md`)
- [ ] **NEW** Explain the value of Looker's Semantic Layer and In-Database Architecture (`17-looker-and-bi.md`)
- [ ] **NEW** Position AlloyDB vs Aurora and explain Spanner's global consistency (`18-alloydb-and-spanner.md`)
- [ ] **NEW** Walk through the end-to-end MLOps lifecycle from BQML to Vertex AI (`19-vertex-ai-bqml-mlops.md`)
- [ ] **NEW** Complete the 6-part BigQuery deep dive course (`bq-course/`)
- [ ] **NEW** Complete the 6-part Dataproc deep dive course (`dataproc-course/`)
- [ ] **NEW** Complete the 6-part Dataflow/Beam deep dive course (`dataflow-beam-course/`)

### Soft Skills
- [ ] Handle all 15 pushback scenarios in `soft-skills/01-pushback-handling.md` out loud using VERA
- [ ] Run a full 30-minute mock discovery call using Script 1 in `soft-skills/06-roleplay-scripts.md`
- [ ] Practice the "Pause, Breathe, Frame" technique on 3 questions you find hard
- [ ] Apply Pyramid Principle to every answer in a mock session (bottom-line up first)
- [ ] Identify which persona archetype is in the room and adapt — drill with `soft-skills/04-difficult-personas.md`
- [ ] Prepare a 30-second ELI5 answer for: BigQuery, Dataproc, Pub/Sub, Dataflow

---

## 📚 Key Reference Links

| Resource | URL |
|---------|-----|
| BigQuery documentation | https://cloud.google.com/bigquery/docs |
| BigQuery Editions guide | https://cloud.google.com/bigquery/docs/editions-intro |
| BigQuery Global Queries (Preview) | https://cloud.google.com/bigquery/docs/global-queries |
| AI.GENERATE / AI.EMBED functions | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate |
| Autonomous embedding generation | https://cloud.google.com/bigquery/docs/autonomous-embedding-generation |
| Conversational Analytics API | https://cloud.google.com/gemini/docs/conversational-analytics-api/overview |
| Dremel paper (original, 2010) | https://research.google/pubs/pub36632/ |
| Dremel 2.0 paper (2020) | https://research.google/pubs/pub49489/ |
| MapReduce paper (2004) | https://research.google/pubs/pub62/ |
| Bigtable paper (2006) | https://research.google/pubs/pub27898/ |
| Spanner paper (2012) | https://research.google/pubs/pub39966/ |
| Mesa paper (2014) | https://research.google/pubs/pub41557/ |
| Dataproc documentation | https://cloud.google.com/dataproc/docs |
| Dataflow / Apache Beam | https://cloud.google.com/dataflow |
| BigQuery pricing | https://cloud.google.com/bigquery/pricing |
| Dataplex Universal Catalog | https://cloud.google.com/dataplex/docs |
| GCP data product list | https://cloud.google.com/products/databases |
| BigQuery partitioning guide | https://cloud.google.com/bigquery/docs/partitioned-tables |
| Dataproc autoscaling | https://cloud.google.com/dataproc/docs/concepts/autoscaling |
| What's new in Google Data Cloud | https://cloud.google.com/blog/products/data-analytics/whats-new-with-google-data-cloud |
| ESG Dataproc TCO study | https://services.google.com/fh/files/emails/esg-economic-validation-google-cloud-dataproc-apr-2022.pdf |

---

## 🗓️ Interview Prep Timeline

```
Today (Day 0)   → Read this README + 00-guideline.md
Day 1           → GCP landscape + BQ setup + hands-on SQL
Day 2           → BQ deep dive (partitioning, clustering, cost)
Day 3           → Dataproc + Dataflow/Beam
Day 4           → End-to-end pipeline designs (whiteboard)
Day 5           → Dataflow, Streaming & Orchestration
Day 6           → End-to-End Pipeline Design (Whiteboarding)
Day 7           → Advanced BigQuery, AI & Governance
Day 8           → Databases, BI & Competitive Intelligence
Day 9           → Soft Skills & Objection Handling
Day 10 (eve)    → Full mock interview + STAR stories
Interview Day   → Review cheat sheet + rest
```

---

*Prepared: February 2026 | Role: Google Cloud Pre-Sales Engineer | 19 docs · 9 exercise categories · 3 deep dive courses · 59+ files · 7 soft-skills guides*
