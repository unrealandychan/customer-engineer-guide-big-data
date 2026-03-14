# Interview D — Presentation: Slide Outline + Logistics

**Interviewer:** William (Hiring Manager)
**Format:** 30-minute presentation + 10–15 min Q&A. Total mock customer meeting ≤ 45 min.
**Audience:** You are presenting to William, who plays two roles: a Technical Stakeholder (Gene-style deep probes) and a VP of Strategy (business ROI questions).

---

## The Prompt (Quick Reference)

> "A retail customer is merging with 2 other brands to form a new Portfolio Company. The CIO is now CIO for all 3. Each brand has different cloud and on-prem data platforms for Physical Stores and Digital eCommerce. The CIO is chartered by the Board to deliver a One Year plan for AI activation and Data monetization."
>
> Your deliverable: an architecture that handles batch and real-time streaming, prepares data for traditional analytics AND AI training, and a migration/consolidation recommendation.

---

## Presentation Structure (30-Minute Time Budget)

| Section | Slides | Time | Purpose |
|---|---|---|---|
| 1. Title & Context | 1–2 | 2 min | Introductions, setting the stage |
| 2. The Specialist Challenge | 3–4 | 4 min | Define the blocker — why off-the-shelf fails |
| 3. Technical Deep-Dive + Live Demo | 5–8 | 12 min | Architecture + POC demo |
| 4. Architectural Decisions & Trade-offs | 9–10 | 5 min | Defend design to technical stakeholder |
| 5. Business & Strategic Value | 11–12 | 4 min | ROI for VP of Strategy |
| 6. Implementation & Next Steps | 13–14 | 3 min | 1-year roadmap, quick wins, call to action |
| **Total** | **14 slides** | **30 min** | |

---

## Section-by-Section Slide Notes

### Section 1 — Title & Context (2 min)

**Slide 1:**
- Title: e.g. "Unified Data & AI Platform for a Multi-Brand Retail Portfolio"
- Your name, role framing (Practice Specialist CE for Data Analytics)
- One-line problem statement: "Three brands. Three data stacks. One mandate: AI activation in 12 months."

**Slide 2:**
- Scene-setting: the customer situation in 3 bullets
  - 3 brands post-merger, each with different cloud/on-prem footprints
  - CIO chartered by the Board for 1-year AI activation + data monetization
  - Physical store + digital eCommerce data streams, none currently integrated
- Agenda preview (show the 6-section flow)

---

### Section 2 — The Specialist Challenge (4 min)

**Slide 3: Why This Requires a Specialist**
- The board's mandate is off-the-shelf impossible because:
  1. **Identity resolution failure** — CustomerID is Brand A's internal key; not portable across brands. No unified customer across the portfolio.
  2. **Schema heterogeneity** — Product, Order, Store tables differ per brand (see poc/schema/ for the actual SQL). No canonical customer journey exists.
  3. **Streaming + batch divergence** — Physical POS generates event streams; eCommerce has daily batch loads from 3 different platforms. No unified ingestion layer.
  4. **1-year mandate = phased approach required** — Big-bang cutover is too high-risk under a board timeline. Must deliver value in phases.
- Key line: *"An off-the-shelf warehouse tool solves none of the identity, schema, or migration sequencing challenges. That's why a specialist is engaged."*

**Slide 4: The Unblocker We'll Build**
- A canonical multi-brand data architecture that:
  - Resolves customer identity across 3 brand schemas
  - Ingests both batch (nightly) and real-time streaming (POS events)
  - Serves both traditional analytics (reporting) and AI training (feature pipelines)
  - Enables the board's 1-year AI + monetization agenda
- Visual: simple before/after — 3 siloed stacks → 1 unified platform

---

### Section 3 — Technical Deep-Dive + Live Demo (12 min)

**Slide 5: 5-Layer Target Architecture Overview**
- One clean diagram (no vendor logos):
  - Layer 1: Ingestion (Pub/Sub for streaming, GCS for batch landing)
  - Layer 2: Central Lake + Warehouse (GCS raw zone + BigQuery canonical)
  - Layer 3: Processing (Dataflow streaming + dbt batch transformation)
  - Layer 4: Serving (Looker/Looker Studio for BI, Vertex AI for ML)
  - Layer 5: Governance (Dataplex + Data Catalog)
- See `architecture.md` for full narrative

**Slide 6: Data Ingestion + Identity Resolution (Demo entry point)**
- Show the 3 brand schemas (poc/schema/) — the different CustomerID structures
- Show `canonical_schema.sql` — how we define brand_id, customer_key, and the canonical Customer/Order/Product tables
- **Live demo:** share screen → BigQuery console → run `transform_canonical.sql` → show the `customer_360` output table
- Key talking point: "The identity resolution step is where most platforms fail. We handle it here in the transformation layer with a deterministic mapping: brand_id + source_customer_id → canonical customer_key."

**Slide 7: Streaming Pipeline (Demo)**
- Architecture: Pub/Sub → Dataflow → BigQuery
- Key design decisions to name:
  - Exactly-once semantics via Beam's shuffle (explain this in 1 sentence)
  - 5-minute fixed windows for near-real-time aggregations
  - Late-arriving data tolerance: 2-minute watermark (show the code comment)
  - Output partitioned by event_date, clustered by brand_id + customer_id
- **Live demo:** run `streaming_pipeline.py` publisher → show messages arriving in Pub/Sub → show records landing in BigQuery `streaming_orders` table

**Slide 8: ML / AI Activation Layer (Demo)**
- BigQuery ML `ARIMA_PLUS` demand forecast model
- **Live demo:** open `demand_forecast_notebook.ipynb` → show the `CREATE MODEL` SQL → run `EXPLAIN_FORECAST` output
- Key talking point: "No separate infrastructure — the model trains directly on BigQuery data using SQL. This is accessible to data analysts, not just ML engineers. That's how you scale AI activation across 3 brands in 12 months."

---

### Section 4 — Architectural Decisions & Trade-offs (5 min)

**Slide 9: Why These Choices**

| Decision | What we chose | What we gave up | When you'd choose differently |
|---|---|---|---|
| Warehouse | BigQuery | Snowflake (familiar to some teams) | If customer is deeply Snowflake-invested and migration risk > benefit |
| Streaming | Dataflow (Beam) | Spark Structured Streaming | If team has strong Spark expertise and latency > 5 min is acceptable |
| Governance | Dataplex | Custom tagging + manual catalog | If customer has < 3 data domains and low compliance burden |
| Serving | Looker Studio (free) for POC → Looker for prod | Tableau (may have existing licenses) | If customer has Tableau contracts — connect to BQ natively |
| ML | BigQuery ML | Vertex AI custom training | For advanced models > ARIMA, move to Vertex Pipelines |

**Slide 10: Technical Risk Register**
- Top 3 risks and mitigations:
  1. Identity resolution completeness — customers who exist in only 1 brand won't be in the cross-brand table. Mitigation: probabilistic matching for edge cases (email / phone hashing).
  2. Schema evolution — one brand changes their source schema mid-migration. Mitigation: dbt schema version contracts + automated CI validation tests.
  3. Peak load (Black Friday) on streaming pipeline. Mitigation: Pub/Sub dead-letter queue + Dataflow auto-scaling with max worker ceiling to cap cost.

---

### Section 5 — Business & Strategic Value (4 min)

**Slide 11: ROI for the VP of Strategy**
- See `business-value.md` for full content
- Key quantified claims:
  - Unified reporting: 7-day report latency → same-day
  - Recommendation engine: 5% AOV lift on 20% of digital transactions
  - Future M&A: the canonical multi-brand schema means any future acquisition integrates in weeks, not years

**Slide 12: Strategic Moat**
- 3 board-level arguments:
  1. AI activation foundation built for the whole portfolio, not just brand-by-brand
  2. Data monetization-ready: the unified customer 360 can be productized as a data product for partner brands or advertisers
  3. Competitive differentiation: unified demand forecasting + personalization at portfolio level is impossible with siloed data

---

### Section 6 — Implementation & Next Steps (3 min)

**Slide 13: 1-Year Roadmap**
- See `roadmap.md` for full content
- Visual: 3-phase timeline bar
  - Phase 0 (0–2 mo): Discover & Align
  - Phase 1 (2–6 mo): Foundation
  - Phase 2 (6–12 mo): AI Activation

**Slide 14: Call to Action**
- Immediate next steps (3 bullets — specific and time-bound):
  1. "Schedule a 2-day data discovery workshop with each brand's engineering lead — target: done in 30 days"
  2. "Stand up a Phase 0 GCP project with IAM for all 3 brand teams — this week"
  3. "Align on the canonical Customer schema — first joint working session in 2 weeks"
- Close: "The architecture and POC are ready. The open question is sequencing. I'd recommend starting with Brand A's eCommerce stream — it's the highest-value data and the most mature pipeline. What questions do you have?"

---

## Logistics Checklist (Do These BEFORE Interview Day)

- [ ] Practice presenting on Google Meet — test screen share with your slides open
- [ ] Test switching from slides → BigQuery console → notebook → back to slides smoothly
- [ ] Verify no confidential customer names or logos in the deck
- [ ] Practice the demo sequence cold: canonical SQL runs, streaming pipeline publishes, notebook executes
- [ ] Confirm your slides work in presentation mode via Meet (some tools take over the window)
- [ ] Practice presenting Section 3 (Technical Deep-Dive) without notes — it's the most complex section and where William will probe hardest
- [ ] Time yourself: target 28–32 min for the presentation. If you're running over, cut from Section 4 trade-offs table, not from Section 3 demo

---

## Final Presentation Tips

- Open every section by naming what you're about to cover: "Now I'll walk through the technical architecture, and I'll show this live in BigQuery."
- End every section with a bridge: "That covers the architecture. Next I'll show why we made these specific design choices."
- In Q&A: pause 3 seconds before answering. It signals confidence, not uncertainty.
- If William asks something your POC doesn't cover — don't pretend it does. "Great question — the POC demonstrates X, and the production extension for Y would work like this…"
