# 🎭 STAR Stories — Pre-Sales Interview Behavioral Framework

> Pre-sales interviews at Google are 40–60% behavioral.
> Every story needs: **Situation → Task → Action → Result**
> Add a **"Why GCP / What I learned"** coda for technical pre-sales roles.

---

## The STAR-G Framework (STAR + GCP Coda)

```
S — Situation   : Set the scene. Customer context, business problem, stakes.
T — Task        : Your specific responsibility in that situation.
A — Action      : What YOU did (not the team). Be specific and technical.
R — Result      : Quantified outcome. Business impact. Numbers where possible.
G — GCP link    : How this maps to a GCP capability or selling motion.
```

---

## Core Question Categories + Your Story Slots

Fill in your own experience in the `[YOUR STORY]` sections.
If you don't have a direct match, adapt a close one and be honest about the context.

---

### Category 1 — Convincing a Skeptical Customer / Stakeholder

**Typical question:**
> *"Tell me about a time you had to convince someone who was resistant to a new technology or approach."*

**What Google is testing:**
- Can you listen and empathize before pitching?
- Do you adapt your argument to the person, not just repeat features?
- Can you handle technical pushback without losing composure?

**Story template:**
```
S: [Customer type / industry] was evaluating [technology A] vs [technology B].
   The key stakeholder was [persona — CTO, data engineer, finance lead] who was
   skeptical because [specific objection — cost, complexity, lock-in, existing investment].

T: My role was to [run the PoC / lead the technical discovery / present the architecture].
   The deal was [size / strategic importance].

A: I first [acknowledged their concern and asked a clarifying question].
   Then I [reframed the comparison around their actual metric — TCO / time-to-insight / FTE hours].
   I [built a side-by-side cost model / ran a PoC on their actual data / brought in a reference customer].
   The turning point was [specific action that changed their view].

R: They [chose our solution / moved forward with a pilot / signed the deal].
   Business outcome: [X% cost reduction / Y months faster delivery / $Z in pipeline influenced].

G: This maps to BigQuery's [TCO story / partitioning/cost optimization / serverless model] —
   specifically the objection about [expensive / complex / lock-in].
```

**[YOUR STORY]:**
> *(Write your version here. Aim for 90 seconds when spoken aloud.)*

---

### Category 2 — Explaining a Complex Technical Concept to a Non-Technical Audience

**Typical question:**
> *"Give me an example of a time you translated a complex technical concept for a business audience."*

**What Google is testing:**
- Do you default to jargon or do you adapt to the listener?
- Can you use analogies? (Pre-sales lives on analogies)
- Do you check for understanding?

**Story template:**
```
S: I was presenting to [C-level / business team / finance] who needed to understand
   [partitioning / streaming vs batch / slot pricing] to make a decision about [project/budget].

T: I had [X minutes] and needed them to approve [investment / architecture / migration plan].

A: I avoided technical terms and instead used the analogy of [your analogy here].
   Example: "Think of BigQuery partitions like filing cabinets — instead of searching every drawer,
   we only open the one labeled with today's date."
   I then showed [a single number / one chart / a before/after comparison] to make it concrete.
   I paused and asked: "Does that match how you think about the problem?"

R: They [approved the budget / signed off on the architecture / asked smart follow-up questions
   that showed they understood].
   The decision unlocked [outcome].

G: In GCP pre-sales, this is the core skill — translating [BigQuery partitioning /
   Dataflow serverless / Storage Write API exactly-once] into business outcomes.
```

**Good analogies to have ready:**
| Technical concept | Analogy |
|---|---|
| Partitioning | Filing cabinet — only open the relevant drawer |
| Clustering | Index in a book — jump to the right page without reading everything |
| Columnar storage | Only pull the columns you asked for off the shelf — don't carry the whole row |
| Pub/Sub | Post office — sender drops off, doesn't wait for recipient; handles surges |
| Dataflow serverless | Hiring a taxi vs owning a car — pay only for the trip, not the idle time |
| Slots (flat-rate) | Reserved highway lane — guaranteed throughput regardless of traffic |
| Materialized views | A pre-cooked meal vs cooking from scratch every time someone asks |

**[YOUR STORY]:**
> *(Write your version here.)*

---

### Category 3 — Handling a Deal That Went Wrong / Losing to a Competitor

**Typical question:**
> *"Tell me about a time a deal didn't go the way you expected. What did you learn?"*

**What Google is testing:**
- Self-awareness and intellectual honesty
- Ability to diagnose root cause (not just blame the customer)
- Whether you improved based on it

**Story template:**
```
S: We were competing for [deal type] against [competitor — AWS/Azure/Databricks/Snowflake].
   We had [strong technical position / reference customers / PoC results].

T: I was responsible for [the technical proof / the commercial proposal / the executive presentation].

A: Despite our efforts, the customer chose [competitor] because [real reason — pricing / existing
   relationship / feature gap / internal politics].
   After the loss, I [did a post-mortem / called the customer for honest feedback / reviewed our
   discovery questions].

R: I learned that [we missed the real decision-maker / we led with features not business outcomes /
   we didn't surface the lock-in concern early enough].
   On the next similar deal, I [specific change] which led to [outcome].

G: In GCP terms, this maps to the [pricing objection / lock-in objection / AWS-already objection]
   in our battlecard — I now address [X] proactively in the first discovery call.
```

**[YOUR STORY]:**
> *(Write your version. Don't be afraid to own the loss — interviewers respect honesty.)*

---

### Category 4 — Cross-Functional Collaboration (Engineering + Business + Customer)

**Typical question:**
> *"Describe a time you had to work across multiple teams or functions to get something done."*

**What Google is testing:**
- Can you navigate between engineers, sales, product, and customers?
- Do you build credibility with technical teams?
- Can you drive alignment without direct authority?

**Story template:**
```
S: A customer needed [capability X] to close the deal, but it required [product team to confirm
   roadmap / engineering to run a custom PoC / legal to approve a BAA / SA team to design the arch].

T: I needed to coordinate [N parties] with conflicting priorities and no direct authority over any of them.

A: I [created a shared doc with the customer requirements mapped to each team's concern].
   I [set a 2-week decision deadline anchored to the customer's procurement cycle].
   With the product team: [I framed it as X customers with the same ask, not just one].
   With engineering: [I kept the PoC scope narrow — one data pipeline, not the full platform].
   With the customer: [I set weekly check-ins to show momentum and surface blockers early].

R: We [delivered the PoC in X weeks / got roadmap confirmation / closed the deal in the quarter].
   The customer outcome was [specific result].

G: Pre-sales at Google requires exactly this — a Dataproc migration PoC needs
   Solutions Architect + Customer Engineering + Product + the customer's data team
   all pulling in the same direction.
```

**[YOUR STORY]:**
> *(Write your version.)*

---

### Category 5 — Under Pressure / Tight Deadline

**Typical question:**
> *"Tell me about a time you had to deliver something important under significant time pressure."*

**Story template:**
```
S: [Customer / internal stakeholder] needed [deliverable] by [deadline] and we had [fraction of normal time].

T: My responsibility was [specific deliverable — architecture doc / PoC / cost model / demo].

A: I [ruthlessly prioritized — dropped X, kept Y].
   I [automated / reused / templated] to move faster.
   I [communicated scope changes proactively] instead of promising everything and missing.
   I [did the 80% version that addressed the core concern, not the 100% version].

R: We hit the deadline. The customer [approved the next phase / signed the deal / gave positive feedback].
   The trade-off I made was [acknowledged trade-off] — and [how you managed that].
```

**[YOUR STORY]:**
> *(Write your version.)*

---

### Category 6 — "Why Google?" / Motivation Questions

**Typical question:**
> *"Why do you want to work at Google specifically, and why this role?"*

**What Google is testing:** Genuine curiosity and alignment with Google's culture (not just "it's prestigious").

**Framework to answer:**
```
1. Specific product belief: "I've used/sold BigQuery and I believe it's genuinely the best
   analytics platform in the market because [concrete reason]."

2. Market timing: "The GCP data + AI platform is at an inflection point — customers are
   moving from lift-and-shift to genuinely cloud-native AI pipelines, and I want to be
   part of that motion."

3. Role fit: "Pre-sales is where I can combine technical depth with business impact —
   I don't want to just engineer; I want to help customers realize value."

4. Google-specific: "Google's culture of technical rigor [20% time / open-source contributions
   like Kubernetes, Beam, TensorFlow / data-driven decisions] aligns with how I think."
```

---

## Quick STAR Checklist — Before the Interview

- [ ] I have **5–6 stories** ready that can flex to different question types
- [ ] Each story is **60–90 seconds** spoken aloud (not longer)
- [ ] Every story has a **specific number** in the Result (%, $, time saved, deal size)
- [ ] I can tell each story **without notes**
- [ ] I've practiced the **GCP analogy table** above — I can explain any concept with a non-technical analogy in under 30 seconds
- [ ] I have an answer to **"Why Google?"** that doesn't start with "It's a great company"
- [ ] I've done **at least one full mock** (record yourself on your phone and replay)

---

## The 30-Second Rule

> If you can't summarize a STAR story in 30 seconds AND expand it to 2 minutes, you don't know it well enough.

Practice both:

**30-second version (elevator pitch):**
"I was selling [X] to a [customer type] who objected to [Y]. I reframed around [TCO/outcome/risk], ran a focused PoC, and they moved forward — which generated [result]."

**2-minute version:**
Full STAR with specific details, turning point, and GCP connection.
