# Interview D — Presentation Delivery Guide
**William (Hiring Manager) · 30-min present + 10–15-min Q&A · Google Meet**

---

## The Setup You Need

### Technology Checklist (Do This 48 Hours Before)
- [ ] Test Google Meet screensharing on your actual machine
- [ ] Know which monitor you'll share — share the one with your slides, not your notes
- [ ] Test your camera + lighting — face a window or use a ring light; don't backlight
- [ ] Test your microphone — AirPods can interfere with Meet audio; use them or test both
- [ ] Close all notifications (Focus Mode / Do Not Disturb on macOS)
- [ ] Have your POC demo environment open and tested before the interview starts
  - BigQuery console → `transform_canonical.sql` ready to run
  - `streaming_pipeline.py` tested in a GCP project
  - `demand_forecast_notebook.ipynb` opened and cells pre-run (outputs visible)
- [ ] If using notes: put them in a second window/doc, NOT on the same screen you share

### Before You Start Presenting
William will open the meeting 1–2 minutes early. He may want to chat briefly.

**Use that chat time to:**
1. Confirm the format: "I have a 30-minute presentation followed by Q&A — does that work for you?"
2. Frame the demo: "I'll be sharing my screen for parts of the technical section — I have a live BigQuery environment set up."
3. Set the scene: "For context, I'm presenting in the role of the specialist CE who has been engaged to solve the technical blocker for the retail customer's CIO."

---

## 30-Minute Slide-by-Slide Timing Script

Use this as your internal timekeeper. Have a clock visible to you (not on the shared screen).

### Section 1 — Title & Context (2 min | Target: Stop at 2:00)

**What to say:**
> "Good [morning/afternoon] — I'm Eddie. For today's session, I'm playing the role of the Data Analytics Specialist CE who's been brought in to solve a specific technical blocker for our retail portfolio customer. My audience today is both the customer's domain expert — that's the technical stakeholder — and their VP of Strategy.

> Here's the challenge in one line: Three brands. Three data stacks. One board mandate: AI activation in 12 months.

> I'll walk you through six sections in about 30 minutes, and then I'd love to get into Q&A."

**Then show your agenda slide and move immediately to Section 2.**

---

### Section 2 — The Specialist Challenge (4 min | Target: Stop at 6:00)

**What to say for Slide 3 (Why Specialist Required):**
> "Let me explain why this isn't solved by an off-the-shelf tool — because that's the most important thing to establish.

> First: **identity resolution failure.** Each brand has a different customer ID — Brand A uses an internal integer key, Brand B uses a UUID from SAP, Brand C uses a loyalty number. A customer who shops at all three brands appears as three unrelated people. You can't personalize or forecast at the portfolio level if you can't see the portfolio customer.

> Second: **schema heterogeneity.** The Order tables across three brands are structurally incompatible — different timestamp formats, different discount models, different product taxonomies. You can't simply union them.

> Third: **batch and streaming duality.** Physical stores generate real-time POS events. eCommerce platforms do nightly batch exports. Most tools handle one or the other cleanly — not both.

> Fourth — and this is the board constraint — **the one-year mandate means phased delivery is required.** A big-bang migration of three legacy stacks takes two to three years. We need to deliver business value in stages."

**Then show Slide 4 (The Unblocker) briefly — one sentence on what you'll build — and move to Section 3.**

---

### Section 3 — Technical Deep-Dive + Demo (12 min | Target: Stop at 18:00)

This is the heart of the presentation. Spend your time here.

**Slide 5 — Architecture Overview (2 min):**
> "Here's the five-layer target architecture. I'll go through each layer briefly, then demo three of them.

> Layer one: Ingestion — Pub/Sub for real-time POS events, GCS buckets for batch loads — one per brand.
> Layer two: Storage — a GCS raw zone for all landing data, and BigQuery as the canonical warehouse with three dataset tiers: raw, canonical, and mart.
> Layer three: Processing — Dataflow for streaming transform, dbt for batch transformation and identity resolution.
> Layer four: Serving — Looker Studio for BI, BigQuery ML for in-place demand forecasting.
> Layer five: Governance — Dataplex as the unified governance layer with automated data quality rules."

**Slide 6 + Demo 1 — Identity Resolution (4 min):**
> "Let me show you the schema challenge and how we solve it."

*[Share screen → BigQuery console → show the 3 brand source schemas briefly → run transform_canonical.sql → show output customer_360 table]*

> "What you're seeing here is the canonical customer table. Brand A's cust_id, Brand B's UUID, Brand C's loyalty number — they're all mapped to a single canonical customer_key using a deterministic SHA-256 hash of brand_id plus source_id. For cross-brand matching — identifying that Brand A customer #123 is the same person as Brand C loyalty member #456 — we use probabilistic matching on normalized email and phone hashes."

**Slide 7 + Demo 2 — Streaming Pipeline (4 min):**
> "Now let me show you the real-time path."

*[Run streaming_pipeline.py publisher → show Pub/Sub messages → show records landing in BigQuery streaming_orders table]*

> "Brand A's POS system publishes events to a Pub/Sub topic. Dataflow subscribes, validates schema, applies first-level normalization, and writes to BigQuery in five-minute windows. Late-arriving data — say a POS system that buffered during a network outage — is accepted up to a two-minute watermark. Beyond that, it goes to a dead-letter table for async reprocessing. Exactly-once semantics are guaranteed at the Dataflow level, not Pub/Sub — an important distinction."

**Slide 8 + Demo 3 — BigQuery ML (4 min):**
> "Finally, the AI activation layer."

*[Open demand_forecast_notebook.ipynb → show the CREATE MODEL SQL → show EXPLAIN_FORECAST output]*

> "This demand forecast model runs entirely in SQL — no Python, no separate cluster. BigQuery ML's ARIMA_PLUS handles seasonality, holiday effects, and trend components. Any SQL-proficient analyst can query, evaluate, and redeploy this model. That's how you scale AI activation across three brands in twelve months without hiring an army of ML engineers."

---

### Section 4 — Architectural Decisions & Trade-offs (5 min | Target: Stop at 23:00)

**Slide 9 — Trade-off Table:**
> "Let me turn to the architectural decisions and what I gave up."

Walk through the 5 key decisions briefly:
- BigQuery over Snowflake: "Serverless, no cluster sizing, native streaming, BigQuery ML in-place."
- Dataflow over Spark: "Unified batch and stream in one Apache Beam framework — one codebase, not two."
- Dataplex over custom governance: "Federated governance across GCS and BigQuery natively; data quality rules with no code."
- Looker Studio for POC: "Free, instant, connects directly to BigQuery. Production moves to Looker with semantic layer."
- BigQuery ML over Vertex custom: "Sufficient for ARIMA in Phase 2; upgrade path to Vertex is clear if accuracy target isn't met."

**Key phrase:** *"I'd choose differently if the customer had a deep Snowflake investment — in that case, Snowflake serves as the warehouse and only the ingestion and governance layers change."*

**Slide 10 — Risk Register:**
> "Three risks I'd put on the CIO's radar:"
1. Brand B on-premise Oracle connectivity — critical path, have CSV batch fallback ready
2. Canonical schema disagreement — this is a people problem, not a technical one; needs CIO escalation path in Phase 0
3. Black Friday streaming peak — Dataflow autoscaling tested at 10x load; dead-letter queue monitored with Cloud Monitoring alert

---

### Section 5 — Business & Strategic Value (4 min | Target: Stop at 27:00)

**Slide 11 — ROI Table:** Walk through each claim with the assumption stated:
> "Real-time portfolio reporting — moving from seven-day manual consolidation to same-day. This frees roughly thirty analyst-hours per week across three brands.

> Cross-brand recommendation engine — with five percent average order value lift on twenty percent of digital sessions, and assuming five hundred million dollars in annual digital revenue, we're looking at approximately five million dollars in incremental annual revenue. I'm using conservative industry benchmarks — happy to model your actual numbers.

> Demand forecasting — fifteen percent reduction on fifty million dollars in inventory carrying costs: seven point five million dollars per year in waste reduction.

> And future M&A: the canonical schema has a brand_id in every table. Onboarding a fourth brand is a six-to-eight week project, not an eighteen-month program."

**Slide 12 — Strategic Moat:** Three bullets, delivered with conviction:
> "One: portfolio-level AI is impossible without unified data. Full stop. Each brand could do segmented AI independently — but cross-brand personalization, portfolio demand forecasting, and a true customer 360 can only exist with this architecture.

> Two: first-mover advantage. Your competitors who haven't done this merger integration yet can't offer cross-brand personalization. You can — within twelve months.

> Three: the next acquisition is a data integration project that takes six weeks, not two years. That changes M&A economics fundamentally."

---

### Section 6 — Implementation & Next Steps (3 min | Target: Stop at 30:00)

**Slide 13 — Roadmap Visual:** 
> "Three phases. Phase Zero — two months of discovery, no code: canonical schema defined, GCP project stood up, Brand A connectivity proven.

> Phase One — the foundation. Four to six months. All three brands in BigQuery, cross-brand sales dashboard live, streaming pipeline running for Brand A.

> Phase Two — AI activation. Six to twelve months. Demand forecast and recommendation engine in production. Two of three legacy stacks decommissioned. Data monetization blueprint ready for the board."

**Slide 14 — Call to Action (last words of the 30 minutes):**
> "Three things this week, if you're ready to move:
> One: schedule the two-day data discovery workshop for Brand A — it's the safest starting point.
> Two: have the CIO send a data governance charter to all three brand CTOs — they need to know their role in Phase Zero.
> Three: stand up the GCP project structure with basic IAM — this takes a day and means we start on Monday.
>
> That's the presentation. I look forward to your questions."

---

## Q&A Delivery Mechanics

### Before Q&A Starts
Stop sharing your screen after the presentation slides. Return to camera view.

Opening line:
> "Great — I'm ready for questions. Feel free to push me on any layer — I'm happy to go deeper technically or higher-level strategically."

### During Q&A
- **Pause before answering.** 2–3 seconds. Show you're thinking, not firing back.
- **Clarify if needed.** "Are you asking about the BigQuery layer specifically, or the broader cost model?"
- **Be direct.** Don't hedge every answer with "it depends" without naming what it depends on.
- **Welcome technical pressure.** If William probes harder: "That's the right question — let me go deeper there." Shows confidence.
- **If you don't know:** "I don't have that exact figure in front of me, but here's how I'd think through it..." — then reason out loud.

### Signs William Is Playing the Business Stakeholder
- Questions about ROI, cost, board impact
- Questions about timeline risk, what happens if it's late
- Questions about competitive differentiation
- Questions about data monetization

Switch register: use business language, avoid jargon, lead with dollar figures and strategic outcomes.

### Signs William Is Playing the Technical Stakeholder
- Questions about specific architectural choices (BigQuery vs Snowflake, Dataflow vs Spark)
- Questions about edge cases (late data, schema evolution, Black Friday peak)
- Questions about the POC code specifically

Switch register: go deep, name specific technical decisions, use correct terminology (watermark, exactly-once, ARIMA_PLUS, etc.).

---

## The 3 Hardest Moments and How to Handle Them

### "That's not how Google does it" / "We have a different approach"
> "That's useful context — I'd love to understand the difference. In my design, I went with [X] because [reason]. If [Google's approach] handles [constraint] differently, I'd want to know more about your thinking there."

Never defensive. Curious + open.

### Long silence after a question
Narrate the silence:
> "Let me think through this..." → then think out loud → then answer.

Never sit in silence for more than 5 seconds without narrating.

### "Why didn't you use [X product/approach] here?"
> "Good question — I did consider [X]. The reason I went with [Y] instead is [specific reason]. If [constraint they named] were different, I'd reconsider [X] because [when it would win]."

Show you considered the alternative — you have a defensible reason, not a gap.

---

## Timing Failure Modes and Recovery

| Scenario | Likely cause | Recovery |
|---|---|---|
| You're at 20 minutes but still in Section 3 | Demo took too long / too much narration | Skip Section 4 detail — say "In the interest of time, I'll summarize the trade-offs" and give 2 bullets only |
| You finish Section 4 at 22 minutes (ahead) | Good speed — don't rush | Expand Business Value section; add a concrete story to one of the ROI claims |
| William interrupts with a question mid-presentation | He's engaged — that's good | Answer it, land the answer cleanly, then say "Let me come back to that in Q&A — I have a few more things to show you first." OR "Great question — actually that segues nicely into my next section." |
| You forget a number during the ROI slide | Expected — numbers under pressure are hard | "Let me give you the framework — I can follow up with the exact model. The key assumption is [X] which drives the output to [roughly Y]." |

---

## The Night Before Checklist

- [ ] Run through the full 30 minutes at least once — out loud, with a timer
- [ ] Open all demo environments and verify they work: BQ console, streaming_pipeline.py output, notebook
- [ ] Test Google Meet screenshare one more time
- [ ] Review Q&A bank — answer 5 questions out loud without notes
- [ ] Sleep ≥ 7 hours — cognitive performance under Q&A pressure degrades significantly without sleep
