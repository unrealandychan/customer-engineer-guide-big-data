# Interview B — GCA: Answer Frameworks

Gene (Data Analytics Field Sales Team Manager) will run this session.
Two question types: **behavioral** and **hypothetical**. Each 45-min session typically contains 1 hypothetical + 1 behavioral + a series of follow-up probes.

---

## Framework 1 — STAR (Behavioral Questions)

Use for any "Tell me about a time…" question.

| Step | What to cover | Watch out for |
|---|---|---|
| **S**ituation | Minimum context — role, team, org, what was at stake. 2–3 sentences max | Don't over-narrate setup |
| **T**ask | Your specific responsibility, goal, or constraint | Make it clear it was YOUR task, not the team's |
| **A**ction | What YOU did — specific steps, decisions, trade-offs | Say "I", not "we". Go deep on your reasoning |
| **R**esult | Quantified outcome — numbers, percentages, timelines, business impact | If no number, explain the scale of impact |
| **L**essons | What you learned or would do differently | **This is the differentiator at Google.** Never skip it. |

### STAR Timing Guide
- Total answer: 3–4 minutes
- S+T: 30–45 seconds
- A: 90 seconds (the bulk)
- R: 30 seconds
- L: 30 seconds

### STAR Phrasing Starters
- S: "At [company], I was responsible for… The situation was that…"
- T: "My specific task was to… I owned…"
- A: "Step one: I started by… Then I… The key decision I made was…"
- R: "The outcome was [metric]. This translated to [business impact]."
- L: "Looking back, I'd… What I learned was…"

---

## Framework 2 — 4-Step Hypothesis Skeleton (Hypothetical Questions)

Use for "How would you…" or "What would you do if…" or scenario questions.

```
Step 1: CLARIFY & FRAME
  → Restate the goal, constraints, and success metrics
  → Ask 1–2 clarifying questions (never skip this)
  → "Before I answer, let me make sure I understand the goal…"

Step 2: DECOMPOSE
  → Break the problem into 3–5 logical buckets
  → State them out loud: "I see this as having three components: X, Y, Z"
  → Don't dive into any single bucket yet

Step 3: DEEP DIVE
  → Pick the 1–2 highest-impact buckets and go deep
  → For data/CE questions: follow the data flow template below
  → "I'll start with X because it has the highest risk/impact…"

Step 4: CONCLUDE + TRADE-OFFS
  → Summarise your recommendation
  → Name what you gave up and under what conditions you'd choose differently
  → Propose a success metric: "I'd measure this by…"
```

### Hypothetical Timing Guide
- Total answer target: 4–5 minutes
- Clarify: 30–45 seconds
- Decompose: 45 seconds
- Deep dive: 2.5–3 minutes
- Conclude: 30–45 seconds

---

## Framework 3 — Data Flow Template (CE/Data-specific hypotheticals)

When the hypothetical involves data systems, layer your answer using this spine:

```
1. USER / STAKEHOLDER
   Who needs this? What decisions do they make? What latency do they need?

2. DATA FLOW
   Ingest → Store → Process → Serve → Govern

3. CONSTRAINTS
   Cost | Time | Risk | Compliance | Skill availability

4. PHASED PLAN
   MVP (what delivers value fastest) → Scale → Optimise
```

**Example mapping for a GCP architecture question:**

| Stage | AWS equivalent (your depth) | GCP native |
|---|---|---|
| Ingest (streaming) | Kinesis | Pub/Sub |
| Ingest (batch) | S3 + Glue | GCS + Dataflow |
| Store | Redshift / S3 | BigQuery / GCS |
| Process | EMR / Glue | Dataproc / Dataflow |
| Serve (BI) | QuickSight | Looker / Looker Studio |
| Serve (ML) | SageMaker | Vertex AI |
| Govern | Lake Formation | Dataplex |

Say explicitly: *"This is the GCP approach — the AWS analogue would be X, which I have deep experience with."* This is explicitly endorsed in your recruiter prep materials.

---

## Framework 4 — Triangle Method (Hypothetical people/ambiguity questions)

When the hypothetical is about a person, team, or process situation:

```
Name 3 sub-points upfront → "There are three things I'd do: A, B, C"
Then go through each with one concrete action and one rationale.
Close with: "And I'd measure success by…"
```

Good for questions like: "What would you do if your team isn't innovating?" or "A developer isn't testing their work — what do you do?"

---

## Critical Rules (Apply to Every Answer)

1. **Clarify before answering** — even one question shows structured thinking
2. **Think out loud** — say your reasoning, not just your conclusion
3. **Use numbers** — Google interviewers love data. If you don't have exact numbers, say your estimate and explain your assumption
4. **Name trade-offs** — every recommendation has a cost. Name it. This shows senior thinking
5. **Close with a metric** — "I'd measure success by…" — always land this
6. **Lessons line** — every behavioral answer must end with what you learned or would do differently
