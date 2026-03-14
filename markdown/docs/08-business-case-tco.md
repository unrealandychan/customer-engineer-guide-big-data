# 💰 Business Case & TCO Framework — GCP Pre-Sales

> Use this when a customer asks: "Show me the numbers" or "How do we justify this to our CFO?"
> A structured business case wins budget. This doc gives you the mental model and the template.

---

## The 3-Layer Cost Narrative

Always structure cost conversations in this order:

**Layer 1 — Why TCO, not unit price**
> "The right comparison isn't $/query or $/GB in isolation. It's total cost of ownership:
> infrastructure, operations, engineering time, and business outcomes combined."

**Layer 2 — The hidden costs of the status quo**
> On-prem Hadoop: hardware refresh cycles, data center costs, patching, dedicated ops team, slow scaling.
> DIY cloud: cluster over-provisioning, idle compute, engineering time managing infra vs building value.

**Layer 3 — GCP's cost levers (specific and quantifiable)**
> Partition/cluster → scan less → pay less. Preemptibles → 60-80% cheaper spot workers.
> Autoscaling → zero idle compute. Serverless BQ → no cluster to size.

---

## Business Case Template (Whiteboard Version)

Use this structure when asked to build a business case in a meeting or on a whiteboard.

### Step 1: Current State Costs

| Cost Category | Current (Annual) | Notes |
|---|---|---|
| Hardware / cloud compute (existing) | $_______ | Include idle capacity |
| Software licenses (data warehouse, ETL) | $_______ | |
| Data center / network | $_______ | |
| Operations FTE (DBA, infra, patching) | $_______ | Salary + benefits |
| Opportunity cost (slow time-to-insight) | $_______ | Hard to quantify — use dev hours wasted |
| **Total current state** | **$_______** | |

### Step 2: GCP Future State Costs

| Cost Category | GCP (Annual) | Notes |
|---|---|---|
| BigQuery storage | $0.02/GB/month × GB | Long-term: $0.01/GB after 90 days |
| BigQuery compute | On-demand: $6.25/TB OR flat-rate slots | Choose model based on usage pattern |
| Dataproc (if needed) | Per-second billing, preemptibles | Ephemeral clusters cut idle cost |
| Pub/Sub | $0.04/GB | Only for streaming use cases |
| Network egress | Variable | Intra-region = free; cross-region = $0.01/GB |
| Engineering / ops saved | -$_______ | Serverless = fewer infra FTE |
| **Total GCP** | **$_______** | |

### Step 3: Migration / One-Time Costs

| Item | Cost | Notes |
|---|---|---|
| Migration engineering | $_______ | Usually 3–6 months for phased migration |
| Training | $_______ | Google provides free training credits |
| PoC / pilot | Usually $0 | GCP free tier + $300 credit for new accounts |
| **One-time total** | **$_______** | Amortize over 3 years for comparison |

### Step 4: ROI Calculation

```
3-Year TCO (Current) = Current Annual × 3 + (expected growth % × hardware refresh)
3-Year TCO (GCP)     = GCP Annual × 3 + Migration one-time
Savings              = TCO Current - TCO GCP
ROI                  = Savings / Migration Cost × 100%
Payback period       = Migration Cost / Annual Savings (months)
```

---

## Real Numbers to Use (Cite These)

| Claim | Source / Number |
|---|---|
| BigQuery query cost reduction with partitioning | Up to 10x less data scanned |
| Dataproc vs on-prem Hadoop TCO | ESG: >50% cheaper |
| Dataproc vs AWS EMR | ESG: 30–50% cheaper |
| Preemptible VM discount | 60–80% vs standard VM price |
| BigQuery vs Redshift (Fivetran / GigaOm studies) | 20–40% lower cost for equivalent queries |
| Storage Write API vs streaming inserts | ~50% lower cost at high volume |
| Serverless Dataflow vs self-managed Spark | Typically 30% ops FTE savings |
| Time to value (cloud vs on-prem) | Months vs years for new capability |

> **Caveat:** Always say "based on customer benchmarks / independent analysis" — don't claim Google guarantees these numbers. Offer to run a cost model on their specific data.

---

## On-Demand vs Flat-Rate Decision Framework

This is a very common interview question: *"When would you recommend flat-rate slots vs on-demand?"*

### On-demand ($6.25/TB scanned)
**Best for:**
- Development and exploration (unpredictable, bursty)
- Small teams, early stage
- Workloads where scan volume is low and predictable
- When you're optimizing well (partitioning + clustering reduce scans significantly)

**Risk:** One unoptimized query can cost hundreds of dollars

### Flat-rate slots
**Best for:**
- Steady, predictable query workloads (dashboards, scheduled reports)
- Large orgs where multiple teams share capacity
- When you want cost ceilings and governance over who gets how much compute

**Pricing (2025):**
- Standard edition: ~$0.04/slot/hour (autoscaling)
- Enterprise edition: reserved slots, committed use discounts (up to 25% off 1-year, 44% off 3-year)

**Key insight to share:**
> "With Standard edition autoscaling, you get the best of both worlds — pay for slots only when queries are running, with automatic scale-up for peak loads and scale-down to zero when idle."

### The crossover point (rule of thumb)
If monthly on-demand spend exceeds ~$2,000/month → evaluate flat-rate.
$2,000/month ≈ 100 committed slots (the minimum) at ~$2,000/month list price.

---

## Competitive Pricing Comparisons

### BigQuery vs Snowflake

| Dimension | BigQuery | Snowflake |
|---|---|---|
| Storage | $0.02/GB/month | $0.023/GB/month (compressed) |
| Compute model | Serverless / slot-based | Virtual warehouse (credits) |
| Idle compute | $0 (serverless) | Charged while warehouse is on |
| Multi-cloud | BigQuery Omni (AWS/Azure) | Native multi-cloud (all regions) |
| AI/ML built-in | BigQuery ML + Vertex AI | Cortex AI + Snowpark ML |
| Best for | GCP-native, AI-heavy, open ecosystem | Snowflake-first, strong data sharing |

**How to position:**
> "Snowflake is a great product. The key difference is: BigQuery is serverless and integrates natively with the full Google AI stack — Vertex AI, Gemini, and Looker. If AI/ML is central to their roadmap, BQ's integrated data + AI story is stronger."

### BigQuery vs Databricks (on GCP)

| Dimension | BigQuery | Databricks |
|---|---|---|
| Primary use | SQL analytics + AI | Spark-based data engineering + ML |
| SQL experience | Native, standard SQL | SparkSQL / Delta Lake |
| ML integration | BigQuery ML + Vertex AI | MLflow + Databricks ML |
| Streaming | Pub/Sub → Dataflow → BQ | Spark Structured Streaming |
| Best for | Analytics-first, BI-heavy | Engineering-heavy, lakehouse |

**How to position:**
> "They're complementary more than competitive — customers often use Databricks for heavy data engineering workloads and BigQuery as the serving layer for SQL analytics and dashboards. Dataproc is GCP's alternative if they want Spark without the Databricks license."

### BigQuery vs AWS Redshift

| Dimension | BigQuery | Redshift |
|---|---|---|
| Architecture | Truly serverless (separation of storage/compute) | Cluster-based (node types, resizing needed) |
| Scaling | Automatic, per-query | Manual cluster resize or Serverless (newer) |
| Pricing | Per TB scanned or slots | Per node-hour or Serverless RPU |
| Operational burden | Near zero | Higher (cluster management, vacuuming) |
| Multi-cloud | BigQuery Omni | Redshift Spectrum (S3 only) |

**How to position:**
> "Redshift Serverless is catching up, but BigQuery has been truly serverless since 2010. No vacuuming, no cluster sizing, no maintenance windows. Your data team focuses on analysis, not infrastructure."

---

## How to Build a Business Case in a 30-Minute Discovery Call

1. **Minutes 0–10: Discovery** — ask these questions:
   - "What's your current data warehouse / analytics platform?"
   - "What does it cost per year (all in — infra, licenses, ops team)?"
   - "What's your biggest pain today — cost, performance, or time to deliver new analytics?"
   - "How many TB of data? How many queries per day? Peak vs average load?"
   - "What's your data team size? How much time on infra vs analytics work?"

2. **Minutes 10–20: Back-of-envelope on whiteboard**
   - Write their current state numbers
   - Apply GCP pricing to their workload (storage + compute)
   - Highlight the 2–3 biggest cost levers for their situation
   - Show the one-time migration cost is typically recouped in < 12 months

3. **Minutes 20–30: Commitment to next step**
   - "If these numbers hold up in a deeper analysis, would you want to run a PoC?"
   - Offer a **GCP cost estimation** workshop or **proof of value** engagement
   - Never close on a number you haven't verified — offer to "sharpen the pencil" together

---

## CFO-Ready One-Page Summary Template

When you need to leave something behind for a CFO or VP of Finance:

```
EXECUTIVE SUMMARY — GCP Data Platform Business Case

Current State Annual Cost:          $[X]M
  - Infrastructure:                 $[A]
  - Licenses:                       $[B]
  - Operations (FTE):               $[C]

Proposed GCP Annual Cost:           $[Y]M
  - Storage + Compute:              $[D]
  - Estimated ops savings:          -$[E] (serverless = fewer infra FTE)

One-Time Migration Investment:      $[Z]
  - Engineering:                    $[F]
  - Training:                       $[G]

3-Year NPV Savings:                 $[X×3 - Y×3 - Z]
Payback Period:                     [Z / (X-Y)] months
ROI (3-year):                       [Savings / Z × 100]%

Key Assumptions:
  - [TB of data] at $0.02/GB/month storage
  - [Query volume] at [on-demand / flat-rate model]
  - [FTE savings] based on serverless eliminating [N] ops roles
  - Migration: phased over [6/12] months, no big-bang cutover

Next Step: 2-week PoC on [customer's highest-value use case]
           to validate performance and cost assumptions.
```
