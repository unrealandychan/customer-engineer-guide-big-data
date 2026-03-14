# 📋 Interview Preparation Guideline — Google Pre-Sales (GCP Data & Analytics)

> Role: **Pre-Sales Engineer / Solutions Consultant**  
> Focus: BigQuery · Dataproc · GCP Data Stack · Streaming · Optimization · Client Objections

---

## 🎯 Role Context

This is a **pre-sales role**, not a pure engineering position. That means you are evaluated on:

1. **Technical credibility** — Can you discuss BigQuery/Dataproc with depth when engineers push back?
2. **Business storytelling** — Can you translate features into cost, speed, and revenue outcomes?
3. **Objection handling** — Can you stay composed and pivot when a client challenges GCP?
4. **Discovery skills** — Can you ask smart questions before pitching?
5. **System design communication** — Can you whiteboard an architecture and justify trade-offs?

---

## 🗂️ Topic Coverage Map

| Priority | Topic | Why It Matters |
|----------|-------|---------------|
| ⭐⭐⭐ | BigQuery architecture, SQL, partitioning, clustering | Core product, most interview questions |
| ⭐⭐⭐ | Dataproc (Spark/Hadoop on GCP) | Second core product |
| ⭐⭐⭐ | Client objection handling (cost, lock-in, AWS/Azure) | Pre-sales differentiator |
| ⭐⭐⭐ | End-to-end pipeline design (streaming + batch) | System design whiteboard |
| ⭐⭐ | Dataflow / Apache Beam | Needed for streaming story |
| ⭐⭐ | GCP data ecosystem (Pub/Sub, Composer, Dataplex) | Breadth expected |
| ⭐⭐ | Cost & performance optimization (BQ + Dataproc) | Very common pushback topic |
| ⭐ | Big data frameworks (Spark, Kafka, Flink, Airflow) | Conceptual breadth for client conversations |
| ⭐ | IAM, security, governance | Supporting detail in designs |

---

## 🧠 How to Answer Any Question (3-Layer Framework)

Use this structure in every answer:

```
Layer 1 (Business)  → One sentence: "This helps reduce analytics cost and speeds up decisions."
Layer 2 (Technical) → 2–4 sentences: explain the mechanism clearly.
Layer 3 (Deep dive) → Only if probed: concrete example, numbers, trade-offs.
```

Then **pivot back to business value**.

---

## 🔑 Core Concepts You Must Know Cold

### BigQuery
- Fully managed, serverless, columnar data warehouse separating storage and compute
- Partitioning (date/timestamp/integer) vs Clustering (sort key within partition)
- Pricing: on-demand (per TB scanned) vs flat-rate slots
- Security: IAM, row-level security, column-level security, authorized views
- Ingestion: GCS load, streaming inserts, Pub/Sub → Dataflow → BQ

### Dataproc
- Managed Hadoop/Spark/Flink on Google Compute Engine (≈ AWS EMR)
- Ephemeral clusters (spin up → job → tear down) for cost savings
- Autoscaling policies + preemptible workers = 18–60% cost reduction
- When to use Dataproc vs Dataflow vs BigQuery (critical trade-off question)

### Dataflow / Apache Beam
- Beam = unified batch + streaming programming model
- Dataflow = Google's fully managed serverless runner for Beam
- Key for streaming pipelines: Pub/Sub → Dataflow → BigQuery

### GCP Data Ecosystem (One-liner each)
| Service | One-liner |
|---------|-----------|
| Cloud Storage | Data lake, HDFS replacement, durable object store |
| Pub/Sub | Managed event ingestion (≈ Kafka) |
| Dataflow | Serverless Beam pipelines, batch + streaming |
| Dataproc | Managed Spark/Hadoop clusters |
| Cloud Composer | Managed Apache Airflow for orchestration |
| Datastream | CDC replication from on-prem/cloud databases |
| Data Fusion | Managed ETL/ELT with a visual UI |
| Dataplex | Data governance and metadata management |
| Bigtable | Low-latency key-value store for operational data |
| Looker/Looker Studio | BI and dashboards on top of BigQuery |

---

## 💬 Pre-Sales Communication Rules

1. **Lead with business outcomes**, not features
2. **Acknowledge client concerns** before rebutting them
3. **Use AWS → GCP analogies** to build bridges (you know AWS!)
4. **Ask discovery questions** before proposing a solution
5. **Justify every architecture choice** with a trade-off explanation
6. Practice the **3-layer answer** for every technical concept

---

## 🚩 Red Flags to Avoid

- ❌ Using only GCP jargon without explaining what it means in business terms
- ❌ Dismissing client's existing stack (AWS, Azure, on-prem) instead of bridging to GCP
- ❌ Not knowing when NOT to use a product (e.g., don't pitch Dataproc for simple SQL analytics)
- ❌ Saying "I don't know" without following up with "but here's how I'd approach it"
- ❌ Forgetting to mention cost implications in architecture discussions

---

## 📐 AWS → GCP Mental Map (Your Superpower)

| AWS | GCP Equivalent |
|-----|---------------|
| S3 | Cloud Storage |
| Redshift / Athena | BigQuery |
| EMR | Dataproc |
| Kinesis | Pub/Sub |
| Glue / Glue ETL | Dataflow / Data Fusion |
| Step Functions + MWAA | Cloud Composer |
| Lambda (streaming) | Dataflow |
| Managed Kafka (MSK) | Pub/Sub or Managed Kafka on GCP |
| CloudWatch / CloudTrail | Cloud Monitoring / Cloud Logging |
| AWS Glue Data Catalog | Data Catalog / Dataplex |
| SageMaker | Vertex AI |

---

## 🏆 Success Metrics for This Interview

By the end of your prep, you should be able to:

- [ ] Explain BigQuery in 30 seconds (elevator pitch), 2 minutes (whiteboard), and 5+ minutes (deep dive)
- [ ] Explain Dataproc and clearly articulate when to use it vs Dataflow vs BigQuery
- [ ] Handle the top 5 client objections with confidence
- [ ] Design two end-to-end pipelines from scratch (streaming + batch)
- [ ] Describe cost optimization strategies for both BigQuery and Dataproc
- [ ] Ask 5+ smart discovery questions before proposing a solution
- [ ] Tell 3 STAR-format stories about past technical or design wins
