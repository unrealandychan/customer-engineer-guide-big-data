# Interview D: Presentation Round — Case Analysis & Strategy

**Interviewer:** William (Hiring Manager)  
**Format:** 45 min total — 30 min presentation + 10–15 min Q&A  
**Role Being Assessed:** Practice Customer Engineer (Specialist CE)

---

## 1. What the Case Is

You are playing a **Practice/Specialist Customer Engineer** (not a generalist). Your job in this scenario:

> A strategic customer's sales cycle is **blocked** by a highly ambiguous technical challenge. You were brought in as the specialist CE to **build the custom architecture, write/demo the code**, and present the solution that **unblocks the deal**.

### The Scenario

| Item | Detail |
|---|---|
| **Customer type** | Retail — merging 3 brands into one Portfolio Company |
| **Stakeholders you present to** | CIO's technical domain expert (Technical) + VP of Strategy (Business) |
| **CIO's mandate from Board** | 1-year plan for **AI activation + Data monetization** |
| **Current state** | 3 brands × each has separate Cloud + On-Prem data platforms for Physical Stores AND Digital eCommerce = **6+ fragmented data environments** |
| **The blocker** | No unified architecture that can handle batch + streaming, serve traditional analytics AND AI/ML training, while consolidating 3 disparate platforms |
| **Your deliverable** | A concrete, custom architecture + migration recommendation — not a generic deck |

### Why This Is Hard (The "Unblocker" Framing)

The recruiter specifically says: *"Why was an off-the-shelf solution impossible?"* — so your narrative must explain that:
- Each brand has different schemas, governance models, latency needs, and data maturity
- A cookie-cutter Lakehouse template can't handle 6 source environments with conflicting SLAs, schemas, and ownership boundaries
- AI activation across 3 brands requires a **unified feature store + data contracts** — not just ETL consolidation

---

## 2. What William Is Evaluating

| Dimension | What He Wants to See |
|---|---|
| **Domain-specific technical acumen** | You know the GCP data stack deeply: BigQuery, Dataflow, Pub/Sub, Vertex AI, Dataplex, etc. |
| **Hands-on keyboard skills** | You show actual code, a diagram you built, a working pipeline, a script — not just slides |
| **Identifying customer solutions** | You frame the answer around the customer's business problem, not product features |
| **Engaging with your audience** | You speak to the techie AND the VP — shift register mid-presentation |
| **Conveying measurable business value** | ROI, time-to-insight, reduced infra cost, AI revenue potential — in numbers |
| **Effectively handling Q&A** | Stay calm under pressure, admit tradeoffs, don't bluff |

---

## 3. Recommended Architecture (The Solution to Present)

### High-Level Design: "Unified AI-Ready Data Platform"

```
[Brand 1 Sources]     [Brand 2 Sources]     [Brand 3 Sources]
 POS, eComm DB,        POS, eComm API,        On-prem DWH,
 Legacy DWH, Files     SaaS Platforms         Streaming events

        |                    |                    |
        +--------------------+--------------------+
                             |
                    [Ingestion Layer]
              Pub/Sub (streaming)  +  Cloud Storage (batch)
              Dataflow (unified pipeline — Apache Beam)
                             |
                    [Landing Zone]
               GCS Raw Bucket (per-brand, partitioned)
                             |
                    [Transform Layer]
                  Dataflow / dbt (for batch)
                  Dataflow Streaming for real-time
                             |
             +---------------------------------+
             |         BigQuery                |
             |  (Central Analytical Layer)     |
             |  - Per-brand datasets           |
             |  - Unified portfolio dataset    |
             |  - BI Engine for dashboards     |
             +---------------------------------+
                             |
               +-------------+-------------+
               |                           |
      [AI/ML Layer]               [Governance Layer]
      Vertex AI Feature Store     Dataplex (Data Mesh)
      Vertex AI Pipelines         Data Catalog
      BigQuery ML                 IAM per brand/domain
      (batch + online serving)    Column-level security
```

### Key Architectural Decisions to Defend

1. **Why BigQuery as the central analytical store?**
   - Serverless — no cluster management during migration chaos
   - Native support for batch SQL + streaming inserts (via Pub/Sub → Dataflow → BQ)
   - BigQuery ML enables in-place model training — no data movement to a separate ML platform in phase 1
   - Physical/logical dataset separation per brand satisfies governance without separate warehouses

2. **Why Dataflow (Apache Beam) over Spark (Dataproc)?**
   - Unified batch + streaming model in one codebase — critical when 3 brands have mixed latency needs
   - Managed, autoscaling — less ops overhead during a merger (teams are distracted)
   - If Dataproc is already in use at one brand, note it as a valid migration-period bridge

3. **Why Pub/Sub for streaming?**
   - Decouples producers (brand apps) from consumers (pipelines) — especially important when brands have different release cycles
   - Global, managed — can ingest from on-prem via Cloud VPN or Pub/Sub Lite

4. **Why Dataplex (Data Mesh approach)?**
   - Each brand becomes a **data domain** — owns and serves its own data products
   - CIO gets a portfolio-wide governance view without forcing a monolithic ETL team
   - Enables brand-level autonomy while enabling cross-brand AI features

5. **Why Vertex AI Feature Store?**
   - Cross-brand AI features (e.g., customer lifetime value across merged loyalty programs) need a shared, low-latency feature store
   - Prevents training-serving skew — same features used to train models are served online

---

## 4. The Migration Strategy (1-Year Roadmap)

### Phase 0 — Discovery & Inventory (Month 1–2)
- Audit all 3 brands: schemas, data owners, volumes, SLAs, security policies
- Score each source system for: data quality, latency criticality, AI readiness
- Establish Data Governance team + Data Stewards per brand (Dataplex domains set up)
- Deliverable: **Migration priority matrix + architecture blueprint**

### Phase 1 — Foundation + Brand 1 Migration (Month 2–5)
- Stand up GCS landing zones, BigQuery projects, IAM structure
- Build shared Dataflow pipelines (templates) for batch ingestion
- Pub/Sub topics per brand for streaming events
- Migrate Brand 1 (lowest complexity or highest business priority) end-to-end
- Validate BI dashboards on BigQuery

### Phase 2 — Brand 2 & 3 Migration + AI Foundation (Month 5–9)
- Onboard Brands 2 & 3 using the same pipeline templates
- Handle on-prem → GCS transfer (Storage Transfer Service, gsutil for batch)
- Stand up Vertex AI Feature Store with first shared feature: unified customer profile
- First BigQuery ML model: cross-brand demand forecasting

### Phase 3 — AI Activation & Data Monetization (Month 9–12)
- Full Vertex AI Pipelines for automated retraining
- Looker/Looker Studio dashboards for CIO's portfolio view
- Data monetization: expose data products to external partners via Analytics Hub
- OnlinePrediction API endpoints for real-time personalization across all 3 brands

---

## 5. Presentation Flow (30 Minutes)

| Segment | Time | Content |
|---|---|---|
| **1. Title & Context** | 2 min | Who you are, what you were asked to solve, what you'll cover |
| **2. The Specialized Challenge** | 5 min | 6 fragmented environments, why "just buy a Lakehouse" doesn't work, what a generic solution misses |
| **3. Technical Deep-Dive / Live Demo** | 10 min | Walk the architecture diagram, show the Dataflow pipeline code or BQ schema, explain the data flow end-to-end |
| **4. Architectural Decisions & Trade-offs** | 5 min | Defend BigQuery vs Snowflake, Dataflow vs Spark, Data Mesh vs Monolith — speak to the technical stakeholder |
| **5. Business & Strategic Value** | 4 min | Speak to the VP: time-to-insight, cost reduction estimate, AI revenue unlock, competitive advantage |
| **6. Implementation & Next Steps** | 4 min | 4-phase roadmap, quick wins, risk mitigations |

---

## 6. Business Value Translation (For the VP of Strategy)

Prepare specific metrics — even estimates with stated assumptions are better than vague claims:

| Metric | Example Framing |
|---|---|
| **Data consolidation cost savings** | "Eliminating 5 redundant on-prem DWH licenses could save $X/year in maintenance" |
| **Time-to-insight** | "From 3 weeks per ad-hoc cross-brand report → same-day with BigQuery + BI Engine" |
| **AI revenue activation** | "Cross-brand demand forecasting alone can reduce inventory overstock by 10–15%, worth $Y at your scale" |
| **Data monetization (Analytics Hub)** | "Selling anonymized portfolio trend data as a product to suppliers is a new revenue stream enabled by the unified platform" |
| **Migration risk mitigation** | "Phased approach means Brand 1 goes live in month 5 — the Board sees progress before year-end" |

---

## 7. Q&A Prep: Likely Questions


### From the Technical Stakeholder (William playing domain expert)

| Question | How to Answer |
|---|---|
| "Why not just use Spark/Databricks? We already use it at Brand 2." | Acknowledge the existing investment. Propose Dataproc as a bridge for Brand 2 migration, with a phased move to Dataflow for unified streaming. Don't dismiss it. |
| "How do you handle schema conflicts across 3 brands?" | Dataplex schema enforcement at the landing zone + dbt for transformation-layer normalization + agreed-upon canonical data model |
| "What's your approach to PII/GDPR across 3 jurisdictions?" | BigQuery column-level security, Dataplex data policies, VPC Service Controls per brand, Cloud DLP for discovery and masking |
| "How do streaming and batch pipelines share the same code?" | Apache Beam's unified model — same pipeline logic runs in batch (bounded) or streaming (unbounded) mode |
| "What if Vertex AI is not mature enough for our use case?" | BigQuery ML as a fallback for in-warehouse models, option to use open-source (MLflow on Dataproc) for specialized workloads |
| "How do you ensure data quality during migration?" | Great Expectations or Dataplex data quality tasks, automated checks in the Dataflow pipeline before landing in BQ |

### From the Business Stakeholder (VP of Strategy)

| Question | How to Answer |
|---|---|
| "What's the risk if this goes over the 1-year timeline?" | Phase 1 delivers a working BI platform by month 5 — that's a Board-visible win. AI activation is phase 3 and can flex |
| "How much will this cost?" | GCP's serverless pricing means you pay for what you use — contrast to fixed on-prem costs. Provide a rough T-shirt size estimate |
| "Can we monetize our data externally?" | Yes — BigQuery Analytics Hub. Walk through a concrete supplier data product example |
| "What makes this AI-ready vs just a data warehouse?" | Feature Store, Vertex AI Pipelines, and the fact that all data is accessible to BigQuery ML without data movement |

---

## 8. Hands-On Demonstration Ideas

Pick **one** to actually prep and show live:

1. **Dataflow streaming pipeline** — Python/Beam code ingesting from Pub/Sub, transforming, writing to BigQuery. Show it actually running or show the code live.
2. **BigQuery schema design** — Show the multi-brand dataset structure, partitioning strategy, a cross-brand query that works.
3. **BigQuery ML model** — Simple demand forecasting model trained inline on sample retail data (`CREATE MODEL` statement).
4. **Dataplex data zones** — Walk through a working Dataplex setup (raw zone → curated zone → product zone) with screenshots or live demo.
5. **Architecture diagram** — A detailed, original Excalidraw, Lucidchart, or Google Slides diagram you built (not a screenshot from docs).

> **Recommendation:** Go with option 1 or 3 — they show coding + GCP depth simultaneously and directly address the "technology depth gaps" feedback from Interview A.

---

## 9. What to Prepare (Practical Checklist)

- [ ] Create your architecture diagram (Excalidraw / Lucidchart / Slides) — dedicate 1 hour
- [ ] Write and test a Dataflow Beam pipeline snippet (batch OR streaming to BQ) — 1 hour
- [ ] Optionally: run a `CREATE MODEL` in BigQuery on a public retail dataset (e.g., `bigquery-public-data.iowa_liquor_sales`) — 30 min
- [ ] Build your slide deck following the 6-part structure — 1 hour
- [ ] Practice the 30-minute run-through out loud at least once — 30 min
- [ ] Test screen sharing on Google Meet before the interview
- [ ] Prepare 3 specific ROI/metric talking points for the VP segment
- [ ] Print or have ready 5 architectural trade-off arguments

---

## 10. The Core Narrative Thread

Tie everything together with this story:

> *"The CIO of this new Portfolio Company has one year to prove to the Board that this merger creates value. The answer is AI-powered analytics across 3 brands — but right now, the data is fragmented across 6 platforms. I was brought in to build the architecture that makes that possible. What I'll show you today is not a wish list — it's a concrete, phased design with working components, real trade-off decisions, and a path from where you are today to AI activation by end of year."*

This framing simultaneously:
- Connects to the VP's strategic concern (Board mandate, 1-year clock)
- Sets up your technical credibility (architecture + working code)
- Positions you as a specialist, not a generalist
