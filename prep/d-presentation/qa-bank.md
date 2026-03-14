# Interview D — Presentation: Q&A Bank

25 questions William may ask, split by audience role. Written answer outlines included.
William plays BOTH roles in the same session — be ready to switch registers mid-Q&A.

---

## PART 1: Technical Questions (Gene / Domain Expert Lens — 12 Questions)

### Architecture & Design

**Q1: Why BigQuery over Snowflake for this architecture?**

Key points:
- Serverless — no cluster sizing during a migration where data volumes are unknown. Critical for a 3-brand merge.
- Native streaming: Dataflow → BigQuery is a managed, first-class integration. Snowflake streams are add-on; BigQuery streaming inserts are native.
- BigQuery ML: train the demand forecast model where the data already lives — no data movement, no separate ML cluster.
- Dataset-level IAM maps cleanly to brand isolation: brand engineers get access to their dataset, not others.
- AWS analogue: Redshift. Key difference: Redshift clusters require sizing; BigQuery scales serverlessly.

If they're a Snowflake customer already: "If the customer has a significant Snowflake investment, the architecture adapts — Snowflake can serve as the canonical warehouse with Dataflow feeding it. The ingestion and governance layers are platform-agnostic."

---

**Q2: How does exactly-once semantics work in your streaming pipeline?**

Key points:
- Pub/Sub guarantees at-least-once delivery (a message may be delivered more than once)
- "Exactly-once" processing is achieved at the Dataflow level via Apache Beam's **shuffle-based guarantee**: the Dataflow runner tracks processed record IDs and deduplicates within a window before writing to BigQuery
- BigQuery streaming insert is idempotent within the same `insertId` — so even if Dataflow retries, BigQuery deduplicates on the `insertId`
- Important distinction: "exactly-once processing" ≠ "exactly-once delivery from Pub/Sub." We achieve exactly-once *results* in BigQuery, which is what matters.

---

**Q3: How do you handle identity resolution across 3 brand schemas with different customer IDs?**

Key points:
- **Deterministic matching** (primary): SHA-256 hash of `(brand_id + source_customer_id)` → canonical `customer_key`. Every source record has a unique, deterministic key.
- **Probabilistic matching** (secondary, for overlap detection): normalized email hash + normalized phone hash. If Brand A customer email = Brand C customer email → these are the same person in the cross-brand customer_360.
- The identity resolution step lives in the dbt `int_canonical_customer.sql` model — it's transparent, testable, and auditable.
- **What we give up:** customers who exist in only 1 brand and provided no shared identifier are not cross-brand-linked. This is acceptable in Phase 1 — probabilistic matching improves coverage over time as more touchpoints are captured.

---

**Q4: How do you handle late-arriving data in your streaming pipeline?**

Key points:
- The Dataflow pipeline uses a **2-minute watermark** — events that arrive within 2 minutes of their event timestamp are included in the correct window
- Events arriving after the watermark (e.g. a POS system that buffered during a network outage) → written to a `late_arrivals` dead-letter table in BigQuery for async reprocessing
- The window type is **fixed 5-minute windows** — each window emits once when the watermark passes. No sliding window needed for this use case (sales aggregations, not real-time fraud detection).
- **Trade-off I made:** a longer watermark reduces late-data loss but increases dashboard latency. 2 minutes is chosen because the business use case (near-real-time store sales) tolerates 2–3 min delay but not 10+.

---

**Q5: Why Dataflow over Spark Structured Streaming?**

Key points:
- Dataflow is **serverless** — no cluster to manage, autoscales to zero. In a migration context where workload is unpredictable, this matters.
- **Unified batch + stream** in one Apache Beam framework — same codebase handles nightly batch ingestion AND real-time POS streaming. Reduces operational complexity.
- **Native GCP integration**: Pub/Sub → Dataflow → BigQuery is a fully managed, monitored pipeline. Spark requires more glue.
- **When Spark wins:** if the customer has existing Spark jobs (Brand A has PySpark?), we'd evaluate migrating to Dataproc-managed Spark instead to reduce rewrite cost.

---

**Q6: How would you handle Brand B's on-premise Oracle database with no streaming capability?**

Key points:
- **Phase 1 approach:** scheduled batch export (nightly CSV/Parquet dumps from Oracle) → SFTP or Storage Transfer Agent → GCS landing zone → Dataflow batch job → BigQuery canonical
- **Phase 2 upgrade:** **Google Datastream** (CDC product) connects directly to Oracle and streams change events in real-time. Oracle Logminer-compatible. This moves Brand B from 24-hour batch to near-real-time without changing the source system.
- Risk: Datastream requires network connectivity from the on-prem Oracle host to GCP. Phase 0 network assessment will determine if a VPN or Interconnect is needed.

---

**Q7: What's your strategy for schema evolution — what if Brand A changes their source schema?**

Key points:
- dbt staging models declare expected columns explicitly. If Brand A adds a column: the staging model ignores it (configurable behavior). If Brand A renames or removes a column: the dbt test fails immediately, alerting the platform team before the canonical layer is affected.
- Schema version contracts: every source table has a `schema_version` tag in Data Catalog. Changes require a review process.
- For BigQuery schema evolution: BigQuery supports backward-compatible schema changes (adding nullable columns). Breaking changes (rename, remove, type change) → handled as a new version of the table with a migration period.
- **The real answer:** proactive — we embed a data steward from each brand's engineering team in our weekly platform sync. Schema changes are surfaced before they're deployed.

---

**Q8: What's your disaster recovery strategy for this architecture?**

Key points:
- **GCS:** multi-region bucket for raw landing zone (US multi-region). Objects replicated automatically. RPO: near-zero.
- **BigQuery:** built-in cross-zone replication within a region. For critical tables, scheduled snapshots to a separate GCS bucket (daily). BigQuery point-in-time recovery: 7-day table snapshot history available natively.
- **Dataflow:** stateless by design — if a worker fails, Beam checkpointing allows restart from last committed offset in Pub/Sub.
- **Pub/Sub:** messages retained for 7 days by default. If Dataflow goes down for hours, it replays from the retained offset. No message loss.
- **Cloud Composer (orchestration):** managed HA. DAGs stored in GCS — recoverable.
- **RPO/RTO targets for this customer:** RPO 1 hour for raw data, 24 hours for canonical warehouse. RTO 2 hours for streaming, 4 hours for batch pipelines restored.

---

**Q9: How do you handle PII across 3 brands that may have different compliance requirements?**

Key points:
- **Uniform treatment:** All PII fields are tagged at the column level in Data Catalog: `customer_name`, `email`, `phone`, `IP_address`, `loyalty_number` → `sensitivity_class: PII`
- **Encryption:** at-rest encryption is default (Google-managed). Sensitive brands can opt into CMEK (Customer-Managed Encryption Keys).
- **Dynamic data masking:** non-prod environments have BigQuery column-level security policies that mask PII for analysts. Only approved roles see raw PII.
- **Right to erasure (GDPR / CCPA):** scheduled dbt job that nullifies PII columns by `customer_key` across all canonical + mart tables when a deletion request is received. Downstream mart tables are refreshed within the SLA window.
- **Brand-specific compliance:** some brands may have stricter requirements (HIPAA if they sell health products, CCPA for CA-based brands). Dataplex governance policies are brand-scoped — Brand B can have stricter masking rules without affecting Brand A.

---

**Q10: How does your BigQuery ML demand forecast model work technically?**

Key points:
- Uses `ARIMA_PLUS` model type in BigQuery ML — designed for time-series forecasting with built-in holiday effects, seasonality, and trend components
- Training data: 2+ years of historical weekly sales by product × store × brand (from the canonical `order` table)
- The model runs entirely in SQL — no Python, no separate cluster:
  ```sql
  CREATE OR REPLACE MODEL `portfolio.ml.demand_forecast`
  OPTIONS (model_type='ARIMA_PLUS', time_series_timestamp_col='week_start',
           time_series_data_col='units_sold', data_frequency='WEEKLY',
           holiday_region='US') AS
  SELECT week_start, brand_id, product_id, store_id, SUM(units_sold) AS units_sold
  FROM `portfolio.mart.weekly_sales`
  GROUP BY 1,2,3,4;
  ```
- Forecast output via `ML.FORECAST()` — generates point forecast + confidence intervals per product per store per week
- Accuracy metric: `ML.EVALUATE()` returns MAE, MAPE, RMSE. Target: MAPE < 15% for weekly product-level forecast.
- **Why not Vertex AI custom model?** ARIMA_PLUS is sufficient for the 12-month board deliverable. Move to Vertex custom training with gradient boosting if accuracy target isn't met.

---

**Q11: How would you test the pipeline before going live in production?**

Key points:
- **Schema + data quality:** dbt tests on staging models before any canonical layer write. Fail fast.
- **Load testing:** Dataflow streaming pipeline tested at 10x expected peak load using a load generator (synthetic POS event publisher). Monitor worker autoscaling and dead-letter queue growth.
- **Integration testing:** end-to-end test using 1 week of real Brand A historical data through the full pipeline in a staging GCP project. Compare output to known Brand A analytics numbers.
- **Parallel run:** run old system + new system simultaneously for 30 days before switching BI tools to the new platform. Compare key metrics daily. Acceptable divergence threshold defined in Phase 0.
- **User acceptance testing:** 2 weeks with brand analytics leads using the Looker Studio dashboard before it becomes the primary source of truth.

---

**Q12: What happens if Pub/Sub falls behind during a Black Friday peak?**

Key points:
- Pub/Sub is serverless — it scales virtually unlimited on the ingest side. The bottleneck is at the Dataflow consumer level.
- Dataflow autoscales workers up to a configurable `maxWorkers` limit. We set this limit to balance throughput vs cost.
- If Dataflow falls behind: Pub/Sub retains unacknowledged messages for up to 7 days. When Dataflow catches up, messages are replayed in order.
- **Dead-letter strategy:** messages that fail processing 5× → dead-letter topic. These are investigated after peak subsides. For Black Friday, we pre-scale Dataflow workers to 2× expected normal load (scheduled scaling).
- **Monitoring:** Cloud Monitoring alert fires if `oldest_unacked_message_age` in Pub/Sub exceeds 5 minutes. On-call engineers can manually trigger Dataflow worker scale-up.

---

## PART 2: Business & Strategy Questions (VP of Strategy Lens — 13 Questions)

**Q13: What's the total cost of this architecture, and what's the ROI?**
→ See `business-value.md` for the full cost framework. Key answer: "I'd size this at $15,000–30,000/month for Phase 1 scale, scaling with data volume. But the right comparison isn't 'what does this cost?' — it's 'what are we spending today on 3 separate legacy stacks plus data integration overhead?' In most cases, the unified platform is cost-neutral within 6 months."

**Q14: What happens if we go over budget or timeline on Phase 1?**
→ "Phase 1 is scoped conservatively: the first deliverable is a cross-brand dashboard from raw data in BigQuery — that's achievable in 3–4 months even with scope creep. The bigger risk is Phase 0 discovery surfacing unexpected data quality issues in Brand B or C. If that happens, we scope-gate Phase 1 to Brand A first, deliver the first dashboard with 1 brand, and bring in Brands B and C in a rolling schedule. Value is delivered before full migration is complete."

**Q15: What's our risk if we don't do this architecture — if we stay siloed?**
→ "Within 12 months: the board's AI activation mandate fails because you can't train a cross-brand model on siloed data. Within 24 months: the talent gap widens — your data engineers are maintaining 3 separate legacy systems while competitors have unified platforms. Within 3 years: any new acquisition takes 2+ years to integrate instead of 6 weeks. The cost of inaction compounds."

**Q16: What does competitive differentiation look like — how is this hard to replicate?**
→ "The data moat is the canonical customer_360. It takes 12 months to build. Every day you're building it, you're widening the gap. A competitor who starts 12 months from now has 12 months less cross-brand purchase history to train their models. The architecture itself can be replicated — the data asset built on top of it cannot."

**Q17: Can we monetize this data externally? What does that look like?**
→ "Three paths: (1) internal data product — brand marketing teams self-serve campaign targeting off the customer_360, reducing agency costs. (2) CPG partner insights — anonymized cross-brand purchase patterns sold as a retail intelligence product to your CPG suppliers. (3) Privacy-safe data collaboration — using Google Ads Data Hub (clean room), you can collaborate with advertising partners using your first-party data without sharing raw PII. All three require the architecture we're building."

**Q18: What if we want to move away from Google Cloud in 3 years?**
→ "Smart question. Two mitigations: (1) Apache Beam (the Dataflow SDK) is open-source and runs on Flink and Spark — the pipeline code is portable. (2) dbt models are SQL — database-agnostic. The canonical schema in BigQuery exports to Parquet in GCS, which loads into Snowflake, Redshift, or Databricks with no transformation. The strategic lock-in is BigQuery ML — if we use Vertex AI custom models, those are also exportable (ONNX format). I'd scope the exit cost at 4–6 months of migration work — significant but not prohibitive."

**Q19: How do we measure success at 6 months?**
→ "At the 6-month board checkpoint I'd show: (1) All 3 brands' data flowing into the canonical warehouse — provable with a row count and freshness dashboard. (2) Cross-brand sales dashboard live and adopted by the analytics teams — measured by weekly active users. (3) Zero data quality incidents — Dataplex DataScan evidence. (4) Phase 2 ML use cases scoped and ready to build. The 6-month goal isn't AI yet — it's the foundation that makes AI possible in the second half."

**Q20: What are the top 3 risks to the 1-year timeline?**
→ "(1) Brand B on-prem Oracle connectivity — this is the hardest technical integration and sits on the critical path. Mitigation: parallel-track this with a batch CSV fallback in Phase 0. (2) Canonical schema disagreement between brand tech leads — this is a people/governance problem, not a technical one. Mitigation: CIO escalation clause in the Phase 0 governance charter. (3) Talent availability — do we have the GCP-native pipeline engineers to execute Phase 2 in the second half? Mitigation: assess in Phase 0, hire or partner with a certified Google Cloud partner if there's a gap."

**Q21: Does this architecture support future brand acquisitions?**
→ "By design. The canonical schema has a `brand_id` column in every table. Adding a 4th brand means: (1) a 2-day data discovery workshop (same as Phase 0 but scoped to 1 brand), (2) building the staging models for the new brand's source system — 2–4 weeks of data engineering, (3) running the new brand's data through the existing canonical transformation. Total: 6–8 weeks for a new brand onboard. That's the M&A integration advantage."

**Q22: How does this impact the headcount we need for the data team long-term?**
→ "In the near term: you need to staff up temporarily for the migration. Phase 0–1 requires 2 platform engineers + 1 data engineer + 1 analytics engineer (dbt). Phase 2 adds 1 data scientist. After Phase 2: the steady-state team shrinks because you've unified 3 separate data stacks into 1. Instead of 3 brand data teams maintaining separate systems, 1 centralized platform team maintains one. Rough estimate: current state = 4–6 engineers per brand = 12–18 total. Future state = 6–8 centralized platform + 1 per brand for domain embedding = ~10."

**Q23: What does 'data monetization' actually mean in practice for the board?**
→ "The board used that phrase to mean: data that generates revenue beyond its use in internal operations. Three practical models: (1) sell portfolio-level retail insights to CPG suppliers (e.g. which product categories grow when launched together across brands). (2) Better advertising ROI — use the unified customer_360 for first-party audience targeting; media spend efficiency improvement of 20–40% is common when you move from cookies to first-party data. (3) New services — 'powered by data' personalization as a differentiator for premium customer tiers across all 3 brands. The architecture we're building makes all three possible within 12–18 months."

**Q24: How do we build internal trust in the new platform's data accuracy?**
→ "This is actually the hardest problem — not technical, cultural. Three practices: (1) Parallel run — run old dashboards and new dashboards side-by-side for 60–90 days, publicly comparing key metrics daily. This builds trust before we switch anyone over. (2) Data quality SLA dashboard — make Dataplex DataScan results visible to business users. They should be able to see that their data passed validation this morning. (3) Brand data stewards — embed one person from each brand's analytics team in the platform team as a domain expert and trust bridge."

**Q25: What's your recommended first action after this presentation?**
→ "Three things this week: (1) Schedule the 2-day data discovery workshop for Brand A — it's the most mature stack and the safest starting point. (2) Have your CIO send a data governance charter to all 3 brand CTOs — they need to know what's expected of them in Phase 0. (3) Stand up the GCP project structure with basic IAM — this takes 1 day and lets the platform team start immediately. Everything else can wait for Phase 0 to define. The risk of delay here is that momentum from this meeting dissipates. Keep it moving."

---

## Q&A Drill: Night-Before Practice

Read through each question. Give yourself 30 seconds to outline your answer mentally before reading the scripted response. If you blank on any answer, review the corresponding section in `architecture.md`, `business-value.md`, or `roadmap.md`.

Top 5 most likely probes from William:
1. Q1: BigQuery vs Snowflake
2. Q3: Identity resolution
3. Q13: Total cost and ROI
4. Q19: How do we measure success at 6 months?
5. Q25: First action after the presentation
