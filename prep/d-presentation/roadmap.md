# Interview D — Presentation: 1-Year Migration Roadmap

The board mandate: 1-year plan for AI activation and data monetization. This roadmap delivers value incrementally — each phase stands alone as useful, and Phase 2 AI activation builds on (but doesn't require 100% completion of) Phase 1.

---

## Phasing Principles

1. **Value before completeness** — don't wait for full migration to deliver business value. The first cross-brand dashboard ships in Phase 1, not Phase 2.
2. **Risk-sequenced migration** — start with the brand that has the most mature data infrastructure (least risk) to establish patterns, then apply to the harder brands.
3. **AI activation requires 6 months of unified data minimum** — training a cross-brand recommendation model on Phases 0+1 data means Phase 2 ML is better from day 1.
4. **Legacy decommission tied to value proof** — don't decommission a legacy stack until the new platform has demonstrably replaced its value.

---

## Phase 0 — Discover & Align (Months 0–2)

**Goal:** No code yet. Understand the full landscape and define the canonical schema before writing a single pipeline.

### Deliverables

| Deliverable | Owner | Target Date |
|---|---|---|
| Data inventory: all 3 brands' systems, data volumes, refresh rates, criticality | Data Platform Team + Brand Engineering Leads | Month 1 |
| Canonical schema v1: Customer, Order, Product, Store, Channel tables defined and agreed by all 3 brand tech leads | Architecture Lead | Month 1.5 |
| KPI definitions: agreed metrics for portfolio-level analytics | CIO + Brand Analytics Leads | Month 1.5 |
| GCP project structure + IAM design: folders, projects, service accounts | Platform Team | Month 1 |
| Brand A connectivity proof: at least one data source successfully landing in GCS | Platform Team | Month 2 |
| Data governance policy: PII classification, access control matrix, retention policy | Platform Team + Legal/Compliance | Month 2 |

### Key Activities
- 2-day data discovery workshop per brand (6 days total, spread across Month 1)
- Stakeholder interviews: Brand A CTO, Brand B data manager, Brand C engineering lead
- Evaluate migration tooling per brand: Datastream for Oracle/SAP CDC, Storage Transfer for S3, BigQuery Data Transfer for Snowflake
- Risk register: identify the top 5 migration risks per brand

### KPIs for Phase 0 Completion
- Canonical schema signed off by all 3 brand tech leads
- At least 1 brand's raw data ingesting into GCS on a scheduled basis
- GCP project structure live with brand-isolated IAM

---

## Phase 1 — Foundation (Months 2–6)

**Goal:** Unified data lake + first cross-brand analytics use case live. Prove the architecture works before investing in ML.

### Deliverables

| Deliverable | Owner | Target Date |
|---|---|---|
| All 3 brands' raw data landing in GCS on schedule | Platform Team | Month 3 |
| BigQuery canonical schema live: `customer`, `order`, `order_item`, `product` tables | Platform Team | Month 3.5 |
| dbt transformation models: 3-brand staging → canonical → customer_360 | Data Engineering | Month 4 |
| Cross-brand sales dashboard v1 (Looker Studio): daily revenue by brand, store, channel | Analytics | Month 4 |
| Streaming pipeline live for Brand A POS events (real-time orders landing in BQ) | Platform Team | Month 5 |
| Dataplex governance layer: all datasets tagged, data quality rules running nightly | Platform Team | Month 5 |
| Decommission plan drafted for Brand A's legacy analytics layer | Brand A Engineering | Month 6 |

### Key Activities
- Establish dbt project structure: one monorepo covering all 3 brand staging models + canonical marts
- Run first identity resolution: deterministic customer_key generation (brand_id + source_id → SHA-256 hash)
- Phase 1 data quality sprint: null rate, uniqueness, referential integrity tests for all canonical tables
- Train business users on Looker Studio cross-brand dashboard (change management)

### KPIs for Phase 1 Completion
- Cross-brand customer_360 table contains records from all 3 brands
- Cross-brand sales dashboard live and used by at least 3 business stakeholders
- Data freshness SLA met: batch data available by 6am daily; streaming data latency < 10 minutes
- Zero PII compliance violations detected by Dataplex DataScan

---

## Phase 2 — AI Activation (Months 6–12)

**Goal:** Production ML use cases driving measurable business value. Legacy stacks decommissioned. Data monetization foundation ready.

### Deliverables

| Deliverable | Owner | Target Date |
|---|---|---|
| BigQuery ML demand forecast model: ARIMA_PLUS per brand + cross-brand | Data Science | Month 7 |
| Cross-brand product recommendation engine v1: BigQuery ML matrix factorization | Data Science | Month 8 |
| Vertex AI Feature Store: RFM features, cross-brand affinity vectors available for serving | Data Science + Platform | Month 8 |
| Recommendation API: real-time product recommendations served to Brand C Shopify storefront | Engineering | Month 9 |
| Demand forecast integrated into Brand A + B inventory management systems | Engineering | Month 10 |
| Brand A legacy analytics stack decommissioned | Brand A Engineering | Month 10 |
| Brand B legacy DW decommissioned (after 90-day parallel run validation) | Brand B Engineering | Month 11 |
| Data monetization blueprint: unified customer 360 packaged as internal data product for brand marketing teams | CIO + Analytics | Month 12 |
| Brand C Snowflake/Databricks migration complete or on track for Month 14 completion | Platform Team | Month 12 |

### Key Activities
- Model evaluation cadence: retrain demand forecast weekly; evaluate recommendation relevance via A/B test (CTR, AOV lift)
- Vertex AI Pipelines: full MLOps lifecycle — feature computation → train → evaluate → deploy automated
- Parallel run for brand B legacy: run old and new systems simultaneously for 90 days; compare key metrics before decommission
- Stakeholder review at Month 9: show board-level KPIs in dashboard (AI-influenced revenue %, forecast accuracy %)

### KPIs for Phase 2 Completion
- Demand forecast: MAPE (Mean Absolute Percentage Error) < 15% for weekly demand at product level
- Recommendation engine: measurable AOV uplift in A/B test (target: 3–5% lift on recommendation-exposed sessions)
- At least 2 of 3 legacy stacks decommissioned or in formal decommission track
- Data monetization blueprint presented to board as part of 12-month retrospective

---

## Risk Tracker (Live This Through the Roadmap)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Brand B on-prem Oracle connectivity delay | Medium | High | Start Datastream POC in Month 1; have CSV export fallback ready |
| Identity resolution is incomplete (customers only in 1 brand) | High | Medium | Probabilistic matching (email hash + phone hash) as supplementary resolution; incomplete joins are acceptable in Phase 1 |
| Schema disagreement between brand tech leads | Medium | High | CIO escalation path defined in Phase 0 governance charter |
| Streaming pipeline falls behind on Black Friday peak | Medium | High | Dataflow autoscaling tested at 10x load; dead-letter queue monitored |
| Brand C migration complexity (Snowflake + Azure) | High | Medium | Brand C is last in sequence; Phase 2 completion stretched to Month 14 if needed |
| ML model performance below target | Low | Medium | Start with BigQuery ML (simpler, faster to iterate); move to Vertex custom training only if BQ ML underperforms |

---

## The 1-Year Summary Narrative (Use This in Slide 13)

> "In 12 months: three brands connected to a single data platform, the CIO has a real-time view of the entire portfolio, and two AI use cases — demand forecasting and cross-brand recommendations — are in production and driving measurable ROI. Two of three legacy stacks are decommissioned. The architecture is ready to onboard a fourth brand in under 3 months. That's the 1-year plan."
