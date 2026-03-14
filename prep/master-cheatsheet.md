# Master Cheat Sheet — All 3 Remaining Interviews
**Print this. Read it the morning of each interview.**

---

## Who You Are Talking To

| Round | Interviewer | Their Job | What They're Optimizing For |
|---|---|---|---|
| B — GCA | Gene | Data Analytics Field Sales Team Manager | "Can this person structure and solve problems rigorously with data?" |
| C — G&L | Andy | Platform CE Team Manager | "Would I put this person in front of my best customers? Are they Googley?" |
| D — Presentation | William | Your Hiring Manager | "Can this person do the actual job — build things, sell ideas, handle tough Q&A?" |

---

## The One Thing They All Want to See

> **You think before you speak. You use data. You own outcomes. You learn.**

Every question in every round is testing a version of that sentence.

---

## Round B — GCA: Quick Reference

### The Two Question Types
1. **Behavioral** ("Tell me about a time...") → Use **STAR + Lessons**
2. **Hypothetical** ("How would you...") → Use **Clarify → Decompose → Deep Dive → Conclude + Metric**

### STAR in 60 Seconds
```
S (10%) — Set the scene fast: company, team size, stakes
T (10%) — YOUR task, not the team's — say "I"
A (50%) — The BULK: what you did, step by step, key decision you made
R (15%) — Specific number + business impact
L (15%) — What you'd do differently (never skip this — it's the differentiator)
```
**Total: 3–4 minutes. One number minimum in Result.**

### Hypothetical in 60 Seconds
```
1. CLARIFY (30s)  — "Before I answer, let me make sure I understand the goal..."
2. DECOMPOSE (45s) — "I see this as 3 parts: X, Y, Z" — name them before diving
3. DEEP DIVE (2.5min) — Go deep on the highest-impact bucket. Use data flow template if it's a system.
4. CONCLUDE (30s) — Summarize recommendation + name 1 trade-off + "I'd measure success by..."
```

### Data Flow Template (CE/Data Hypotheticals)
```
User/Stakeholder → what decisions at what latency?
Ingest → Store → Process → Serve → Govern
Constraints: Cost | Time | Risk | Compliance
Phased Plan: MVP → Scale → Optimise
```

### GCP ↔ AWS Quick Map (Say the analogue, then explain what's different)
| GCP | AWS | Key Difference |
|---|---|---|
| Pub/Sub | Kinesis | Pub/Sub is serverless (no shards) |
| Dataflow (Beam) | Kinesis Analytics / Glue | Beam runs batch + streaming in one framework |
| BigQuery | Redshift | BQ is serverless; no cluster sizing |
| Dataplex | Lake Formation | Dataplex covers quality + lineage, not just permissions |
| Vertex AI | SageMaker | Vertex Pipelines more unified; tighter BQ integration |
| Looker / Looker Studio | QuickSight | Looker Studio is free; Looker has LookML semantic layer |

### 5 Most Likely Questions for Gene
1. "Tell me about a time you faced technical and people challenges simultaneously."
2. "How would you design an analytics platform for a retail customer merging 3 brands?"
3. "Tell me about a time you made a decision with incomplete data."
4. "How would you convince a GCP customer to expand their services?"
5. "Tell me about a time you were the end-to-end owner of a project."

### Critical Rules — Never Break These
- **Clarify before answering** — always ask at least 1 question first
- **Think out loud** — say your reasoning, not just your conclusion
- **Use numbers** — estimate if you don't have exact figures; state your assumption
- **Name trade-offs** — every recommendation gives something up. Name it.
- **Close with a metric** — "I'd measure success by..."
- **End behavioral with Lessons** — never skip the "what I'd do differently" line

---

## Round C — G&L: Quick Reference

### The 8 Googleyness Traits — and Trigger Phrases

| Trait | Say This Naturally |
|---|---|
| Ambiguity | "Requirements were unclear, so I defined a first version and invited feedback..." |
| Intellectual Humility | "I was initially wrong — the data showed me..." |
| Bias for Action | "Instead of waiting, I shipped an experiment to validate the assumption..." |
| Do the Right Thing | "I held the line because our users deserved..." |
| Taking Ownership | "I stepped in because no one else was going to..." |
| High Standards | "I built it so it could scale to 10x without rework..." |
| Challenge Status Quo | "I asked why we'd always done it that way. Turns out..." |
| Fun + Collaboration | "When we finally shipped, I made sure we celebrated..." |

**Rule:** Work at least 2 traits into every behavioral answer. Make it natural, not mechanical.

### Google's Definition of Leadership
> "Stepping up to get things done and taking ownership of a project or process" — NOT organizational seniority.

Leadership questions are about **initiative + ownership + follow-through**, not titles.

### SPSIL (G&L version of STAR)
```
S — Situation (context)
P — Problem (the specific obstacle/challenge)
S — Solution (what YOU did — steps, decisions)
I — Impact (quantified outcome)
L — Lessons (what you learned / would do differently)
```
Same as STAR but "Problem" is explicitly named — forces you to make the obstacle clear before jumping to solution.

### 5 Most Likely Questions for Andy
1. "Tell me about a time you handled trade-offs and ambiguity simultaneously."
2. "Tell me about a time you had an ethical dilemma or were pressured to cut corners."
3. "Tell me about a time you demonstrated leadership even though you weren't the manager."
4. "What makes a great Customer Engineer? What makes a bad one?"
5. "Where do you see your career going? What would you learn at Google?"

### What Makes a Great/Bad CE (Have This Ready)
**Great:** Deep technical credibility + customer empathy + ability to translate between technical and business audiences + bias for building concrete solutions (POCs, prototypes, not slide decks alone).

**Bad:** Either (a) order-taker with no initiative — just executes requests without adding insight, or (b) brilliant engineer who can't make their ideas land with a customer.

### "Why Google / Why This Role?" — Use This Frame
> "What draws me to this specialist CE model is the mandate to go deeper than a generalist can. I want to be the person who steps in on the hardest problem — the one a standard solution can't solve — and builds the thing that unblocks the deal. At Google scale, I'd work on problems I couldn't access anywhere else, alongside the engineers who built the products I'd be deploying."

---

## Round D — Presentation: Quick Reference

### The 6-Section Flow (30 min + 10–15 min Q&A)
```
1. Title & Context          — 2 min — One-liner problem. Agenda.
2. Specialist Challenge     — 4 min — Why off-the-shelf fails (4 reasons). What you'll build.
3. Technical Deep-Dive      — 12 min — 5-layer architecture + 3 live demos
4. Architectural Decisions  — 5 min — Trade-off table. Risk register.
5. Business Value           — 4 min — ROI table. 3 strategic moat arguments.
6. Implementation Roadmap   — 3 min — Phase 0/1/2 visual. CTA 3 bullets.
```

### The 4 Reasons Off-the-Shelf Fails (Know Cold)
1. **Identity resolution** — 3 different customer IDs across 3 brands; no cross-brand customer exists
2. **Schema heterogeneity** — incompatible Order/Product/Store schemas; can't union raw tables
3. **Batch + Streaming duality** — POS streams + eCommerce batch loads; most tools do one or the other
4. **1-year mandate = phased required** — big-bang is 2–3 years; board needs ROI in 12 months

### 5-Layer Architecture — Say Without Notes
```
L1: Ingest    — Pub/Sub (streaming) + GCS buckets (batch) per brand
L2: Store     — GCS raw zone + BigQuery canonical (raw → canonical → mart datasets)
L3: Process   — Dataflow (streaming transform) + dbt (batch transform, identity resolution)
L4: Serve     — Looker Studio/Looker (BI) + BigQuery ML / Vertex AI (ML)
L5: Govern    — Dataplex (unified governance, DQ, lineage) + Data Catalog + Column-level security
```

### Identity Resolution — The Key Technical Differentiator
- **Deterministic:** SHA-256 hash of `(brand_id + source_customer_id)` → `canonical customer_key`
- **Probabilistic (cross-brand overlap):** normalized email hash + phone hash → same person detected
- Lives in `dbt int_canonical_customer.sql` — transparent, testable, auditable

### ROI Numbers — Say These With Confidence
| Claim | Value | Assumption |
|---|---|---|
| Reporting latency | 7 days → same day | 3 brands × 2 analysts × 5h/week = 30h/week saved |
| Recommendation engine AOV lift | ~$5M/year | $500M digital rev × 20% exposed × 5% lift |
| Demand forecast inventory savings | ~$7.5M/year | $50M carrying cost × 15% waste reduction |
| M&A new brand onboarding | 6–8 weeks vs 18+ months | `brand_id` column in every canonical table |

*State the assumptions — "this uses conservative industry benchmarks; happy to model your actual numbers."*

### Top 5 Q&A Questions + One-Line Openers
1. **BigQuery vs Snowflake** → "BQ is serverless — no cluster to size during a migration where volumes are unknown."
2. **Identity resolution** → "Deterministic SHA-256 hash of brand_id + source_id; probabilistic email/phone matching for cross-brand overlap."
3. **Total cost / ROI** → "Phase 1 ~$15K–30K/month GCP; compare to 3 legacy stacks + analyst time. Usually cost-neutral within 6 months."
4. **Measure success at 6 months** → "All 3 brands in BQ, cross-brand dashboard live with ≥3 users, zero PII violations, Phase 2 scoped."
5. **First action after presentation** → "Schedule 2-day data discovery workshop per brand this week; CIO sends governance charter; stand up GCP project structure."

---

## Universal Anti-Patterns — Never Do These

| Anti-Pattern | What to Do Instead |
|---|---|
| Jump straight to answer | Clarify first — "Before I answer, let me make sure I understand..." |
| Say "we" throughout | Say "I" for your actions — "we" only for context |
| Give a number-free result | Estimate if needed, but always land a number |
| Skip the Lessons line | Always end behavioral answers with what you'd do differently |
| Argue with the interviewer | Incorporate their pushback — "That's a good point — if we go that route..." |
| Oversimplify the trade-off | Every architectural choice has a cost — name it |
| Over-memorize answers | Know the structure cold; let the specific content breathe |
| Panic in silence | Use think-out-loud: "Let me work through this..." shows structured thinking |

---

## 2025–2026 Product Updates — Know These Cold

These were announced at Google Cloud Next '25 (April 2025). Naming them signals you're current. Full details in `google-cloud-2026.md`.

| Update | What to Say |
|---|---|
| BigQuery = "autonomous data-to-AI platform" | Never say "just a warehouse." BQ now = ingestion + storage + SQL + ML + AI inference + governance. |
| Gemini in BigQuery (GA) | Analysts query in natural language. 350% usage growth. Code assist accepts rate >60%. |
| BigQuery Continuous Queries (GA) | SQL-based real-time streaming — simpler alternative to Dataflow for straight-through processing. |
| TimesFM model in BQ ML (Preview) | Google Research's pretrained time-series model. Better than ARIMA_PLUS for heterogeneous multi-series. Phase 2 demand forecast upgrade. |
| BigQuery universal catalog | New name for Dataplex Catalog. Includes Business Glossary (GA) — define shared meaning of "customer" across brands. |
| BigQuery vector search (GA) | Native embedding search in SQL. No Pinecone/Weaviate needed. Powering recommendation engine in your architecture. |
| BigQuery managed DR (GA) | Auto cross-region failover with near-real-time replication. Replaces manual snapshot strategy. |
| BigQuery Iceberg tables (Preview) | Open lakehouse — Databricks/Spark teams can query same data via BQ SQL. M&A onboarding path. |
| dbt Cloud on Google Cloud | dbt now natively integrated. Strengthens the dbt-in-BQ transformation story. |

**Key rebrand:** "Dataplex" = still the governance surface. The catalog layer inside it is now called **BigQuery universal catalog**. Say "BigQuery universal catalog" in your presentation — it's current.

---

## New Files Added to This Prep Deck

| File | What's In It |
|---|---|
| `prep/b-gca/open-ended-scripts.md` | Scripted answers: "Why Google," "Tell me about yourself," "Favorite Google product," "Sundar coffee," "Strengths/Weaknesses," "First 30/60/90 days," "Great/Bad CE" |
| `prep/google-cloud-2026.md` | Full detail on all 2025–2026 GCP updates — what to say, when to say it, how to respond to follow-up probes |
| `prep/d-presentation/retail-context.md` | Realistic 3-brand scenario with source systems (Lightspeed, Oracle Retail, Shopify), identity resolution specifics, competitor analysis |
| `prep/d-presentation/qa-bank-supplement.md` | 8 new Q&A pairs: AI/Gemini questions, "ChatGPT vs BigQuery," "cost/ROI number," "biggest technical risk," "what AI activation actually means" |
| `prep/c-gl/missing-stories.md` | SPSIL templates: "Received difficult feedback," "Developing/retaining a team member," "What if they said no" probe script, "Competing priorities" |
| `prep/interview-day-checklist.md` | Day-of logistics, mental prep rules, round-specific calibrations, questions to ask each interviewer, follow-up email template |

---

## Day-Of Logistics Reminder (from recruiter email)

- **Format:** Google Meet — practice screensharing before Interview D
- **Notes:** You can use them, but if you screenshare, William may see them. Know core content without notes.
- **Each interview is an elimination round** — B, C, D in no particular order.
- **Presentation:** 30 min present + 10–15 min Q&A = ≤ 45 min total. William plays both technical and business stakeholder.

---

## The 5-Minute Morning Ritual (Day of Each Interview)

1. Read the "5 Most Likely Questions" for that round
2. Answer 1 question out loud (1 time) — no notes — in your car, bathroom, wherever
3. Read the trigger phrases for Googleyness traits once
4. Say the one-line opener for "Why Google / Why this role?" once
5. Take a breath. You're prepared.
