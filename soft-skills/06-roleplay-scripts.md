# 🎭 Roleplay Scripts — Full Mock Conversations

> **How to use this file:**  
> Read the customer lines out loud. Pause. Then respond — **without reading the consultant lines first**.  
> Only check the consultant lines after you've said your own version.  
> The goal is not to memorize these scripts. It's to build the muscle memory of staying calm, structured, and curious under pressure.

---

## Script 1: Initial Discovery Call (30 Minutes)

**Scenario:** First call with a mid-size e-commerce company. They reached out after attending a GCP webinar. You know almost nothing about them. Your job: listen, map pain, set up a deeper technical session.

**Attendees:** You (Consultant) | Alex (Head of Data Engineering) | Sam (VP Engineering, joins for first 10 min)

---

**[00:00 — Opening]**

**SAM:** Thanks for jumping on. We're evaluating a few cloud data platforms. I have 10 minutes and then I'll drop — Alex will take it from there.

**CONSULTANT:** *(Adapt to the rushed exec — lead with the recommendation ask)*
> *"Appreciate you making time. Before I tell you anything about us — can I ask: what's the one problem that made you agree to this call in the first place? That'll shape everything."*

**SAM:** Our pipelines are unreliable. We process about 8 billion events a day around peak season and our current system falls over. We've had SLA misses that cost us revenue.

**CONSULTANT:** *(Anchor the business impact — get the number)*
> *"SLA misses — do you have a rough sense of what a one-hour outage costs the business? Even a ballpark."*

**SAM:** Probably $50–80K per incident. We had three last quarter.

**CONSULTANT:** *(Do the math, briefly)*
> *"So roughly $150–240K in direct impact last quarter. That's the number I'll keep in mind as we talk. Alex, I'll dig into the technical detail with you — Sam, before you drop, is there anything else that's top of mind?"*

**SAM:** Just make sure we're not trading one set of problems for another. *(drops)*

---

**[10:00 — Technical Discovery]**

**ALEX:** So our stack right now is Kafka on EC2, Spark on EMR, and Redshift for the warehouse. We've had it for 4 years.

**CONSULTANT:** *(Situation question — draw it out)*
> *"Got it. How does data flow today — from the event producers all the way through to Redshift? Walk me through a typical pipeline."*

**ALEX:** Events hit Kafka, Spark jobs consume them and do transformation, land in S3, then we load to Redshift every hour with COPY commands.

**CONSULTANT:** *(Problem question — where does it break?)*
> *"Where does that break down? Is it the Kafka layer, the Spark jobs, the S3 → Redshift load?"*

**ALEX:** Mostly the Spark jobs. During peak we have 50 concurrent jobs and the EMR clusters can't scale fast enough. We're auto-scaling but it takes 15 minutes and by then we've already missed the window.

**CONSULTANT:** *(Implication question)*
> *"When a job misses its window — what downstream thing breaks? Is it reports, ML models, customer-facing features?"*

**ALEX:** All three. Our recommendation engine pulls from Redshift every 30 minutes. If the data's stale, we serve bad recommendations — and our team doesn't even know until a customer complains.

**CONSULTANT:** *(Need-payoff question)*
> *"So if the pipeline was reliable at 8 billion events with no scaling lag — what would that unlock for your team?"*

**ALEX:** We'd actually be able to build new features instead of firefighting. We've had the same three engineers on incident response for six months.

**CONSULTANT:** *(Summarize and hypothesize)*
> *"Let me reflect back what I heard: you have a fixed-capacity Spark cluster that can't auto-scale fast enough at peak, which creates stale data downstream, which impacts recommendations and causes SLA misses — and your best engineers are stuck in firefighting mode instead of building. Does that capture it?"*

**ALEX:** Yeah, that's exactly it.

**CONSULTANT:** *(Propose the next step — don't pitch yet)*
> *"I have a hypothesis about how GCP would address this, but I want to make sure I've seen your actual job patterns before I propose an architecture. Can we schedule a 45-minute technical session where you share some query/job stats and we design something together?"*

---

## Script 2: Technical Deep-Dive With a Skeptical Audience

**Scenario:** Second meeting. You're presenting a proposed Dataflow + BigQuery architecture. The team includes one very skeptical senior engineer (Jordan).

**Attendees:** You | Alex | Jordan (Senior Data Engineer, skeptic)

---

**[Opening the whiteboard]**

**CONSULTANT:**
> *"I sketched an architecture based on what Alex shared. Before I walk through it — Jordan, you know this environment. I'd actually like you to challenge whatever doesn't look right."*

**JORDAN:** *(immediately)* What's the throughput guarantee on Pub/Sub? We're at 8 billion events a day — peaks at 2 million per second.

**CONSULTANT:** *(Answer precisely — don't round)*
> *"Pub/Sub is designed for exactly this scale. The per-topic throughput limit is 10 GB/s per region — at 2 million events/second, if your average message is 1KB, you're at 2 GB/s peak, well within limits. For ordering requirements we'd use ordering keys within partitions. Do you have ordering requirements across the full event stream or per-entity?"*

**JORDAN:** Per user session.

**CONSULTANT:**
> *"Then ordering keys on session ID handles that precisely. Pub/Sub guarantees delivery order within a key. Let me draw that — [draws] — here's the session key routing."*

**JORDAN:** What about exactly-once semantics? Kafka gives us that. Does Pub/Sub?

**CONSULTANT:** *(Be honest about the nuance)*
> *"Pub/Sub gives you at-least-once delivery by default. Exactly-once is handled at the Dataflow layer — Dataflow's streaming runner has built-in exactly-once semantics with the Streaming Engine. So you'd have at-least-once at the bus, exactly-once at processing. Is the concern about duplicate events downstream, or upstream?"*

**JORDAN:** Downstream. We're billing based on event counts.

**CONSULTANT:**
> *"Then the right place to deduplicate is Dataflow before the data hits BigQuery — we'd use a session window with a dedupe key. That's one step in the pipeline. Here — [draws dedup step on whiteboard]. Would this satisfy your billing accuracy requirement?"*

**JORDAN:** *(pause — less hostile)* ...probably. What's the latency look like end-to-end?

**CONSULTANT:**
> *"With Streaming Engine, Dataflow median end-to-end latency is typically sub-second for small payloads — your 1KB messages should be in BigQuery within 1–2 seconds of being published. I can pull benchmark data specific to your message size if that's useful."*

**JORDAN:** That's actually better than what we have now.

**CONSULTANT:** *(Don't spike the ball — stay collaborative)*
> *"Good. What else would you poke at?"*

---

## Script 3: Pushback-Heavy Executive Presentation

**Scenario:** You're 15 minutes into a presentation with a VP and CFO. It's not going well.

**Attendees:** You | Morgan (VP Data, your champion) | Chris (CFO, skeptical, numbers-only)

---

**[15 minutes in — Chris interrupts]**

**CHRIS:** I'm going to stop you right there. I looked at the pricing page. At our data volume — 500TB queries per month — we're looking at $3,000 a month just in query costs. That's $36K a year. We spend $12K a year on Redshift. Why would I pay 3x more?

**CONSULTANT:** *(Validate the math — don't dismiss it)*
> *"That's the right question and the math on the pricing page is real — at face value, $6.25 per TiB scanned, 500TB scanned, that's $3,125/month. Let me show you why that number changes significantly in practice, because I've seen this exact comparison a dozen times."*

**CHRIS:** Go ahead.

**CONSULTANT:**
> *"Two adjustments. First: at your query patterns — based on what Morgan shared — roughly 70% of your queries are against partitioned tables with date filters. You're scanning about 150TB effective, not 500TB. So on-demand is closer to $940/month, not $3,125. Second: at $940/month, you're above the threshold where Flat-Rate Reservations save you money — a 100-slot commitment is $2,000/month and covers your full workload with no byte scanning cost. But here's the number I'd actually compare: what does Redshift cost including the ops team managing it?"*

**CHRIS:** What do you mean?

**CONSULTANT:**
> *"Redshift requires cluster sizing, vacuuming, snapshot management, and at your scale, a DBA or data engineer spending 30–40% of their time on maintenance. What's a senior data engineer fully-loaded cost — $150K? 35% of that is $52K/year in ops cost that doesn't exist on BigQuery. Add Redshift's license plus EC2, and the total cost of Redshift is probably $70–80K/year. BigQuery at Flat-Rate is $24K/year plus near-zero ops. That's the comparison."*

**CHRIS:** *(pause)* Can you put that in a spreadsheet?

**CONSULTANT:**
> *"I'll send a TCO model tonight with your actual numbers. Morgan — can you share the query volume breakdown and current team allocation so I can make it specific to you, not a generic estimate?"*

**CHRIS:** *(to Morgan)* Send them whatever they need.

---

**[Morgan's internal pressure — after the meeting]**

**MORGAN:** *(privately, after Chris leaves)* Thanks for that — I wasn't sure how to handle Chris. But my CTO is also skeptical. He's worried about lock-in.

**CONSULTANT:**
> *"Good to know early. What specifically — data format lock-in, or the legal/contractual kind?"*

**MORGAN:** He's burned before. Previous vendor made it impossible to export data.

**CONSULTANT:**
> *"Then BigQuery actually has a good story here — and it's not marketing. Your data can live in Parquet files on Cloud Storage, readable by any engine. BigLake lets you query them from BigQuery without importing. If you leave tomorrow, your data is in open files. I'd suggest we include a one-page 'exit strategy' document in the proposal — not because you'll need it, but because showing the CTO the exit door builds trust that we're not trapping him."*

**MORGAN:** That's... actually a great idea.

---

## Script 4: Whiteboard Session Gone Off the Rails

**Scenario:** You're in a technical whiteboard session. It's 20 minutes in. Two engineers are arguing with each other, you've lost the room, and the clock is ticking.

---

**[Engineers arguing — room is chaotic]**

**ENGINEER 1 (Taylor):** We should keep Kafka. Moving to Pub/Sub is a huge migration risk.

**ENGINEER 2 (Riley):** Kafka on-prem is killing us on ops. We spend more time running Kafka than building features.

**TAYLOR:** That's a training issue, not a Kafka issue.

**CONSULTANT:** *(Step in — don't take sides)*

> *[Walk to whiteboard, pick up marker, draw a box labeled "Current State"]* 

> *"Both of you are right about different things — and I think we're actually talking about two separate decisions. Let me put them on the board so we don't conflate them."*

> *[Draw two columns: "Migration Risk" and "Operational Cost"]*

> *"Taylor — your concern is here [point to Migration Risk]. That's real — any Kafka migration has a cutover risk period. Riley — your concern is here [point to Ops Cost]. Also real — Kafka on-prem has significant ops overhead. These are two different questions: can we solve the ops problem without the migration risk? And separately, what is the migration risk actually — is it 2 weeks or 6 months?"*

**TAYLOR:** The risk is the consumer offsets. We have 400 consumers. Re-registering all of them is not trivial.

**CONSULTANT:**
> *"Okay — so the migration risk is about consumer offset management. Let me write that specifically [writes on board]. That's a solvable engineering problem — Pub/Sub has a Kafka compatibility layer called the Pub/Sub Kafka Connector. Your consumers don't change. They keep using the Kafka protocol. The migration is at the broker level, not the consumer level. Does that change the risk calculus?"*

**TAYLOR:** *(pausing)* ...I didn't know about the Kafka connector.

**CONSULTANT:**
> *"Let me draw the migration path — [draws] — here's what changes and here's what stays the same. Riley, does this address your ops concern? Taylor, does this reduce the migration risk you're worried about?"*

**RILEY:** Yes — if my consumers don't change, I'm in.

**TAYLOR:** I want to read more about the connector. Can you share the docs?

**CONSULTANT:**
> *"I'll put it in the follow-up today. For now — can we agree that the connector is worth evaluating as the migration path, and we come back in a week with a spike result? That way we're making decisions on real data, not assumptions."*

**BOTH:** *(nodding)* Yeah.

**CONSULTANT:** *(to the room)*
> *"Good. Let's keep going — [redirect to whiteboard] — we had the data flow 70% drawn. Let me pick up where we were..."*

---

## Practice Protocol

### Solo practice
1. Cover the consultant lines with a piece of paper
2. Read the customer line out loud
3. Pause for 5 seconds — respond naturally
4. Compare your answer to the consultant line — not to memorize it, but to notice the structure

### With a partner
1. Partner reads customer lines — optionally ad-libs new objections
2. You respond in real time
3. Partner scores using the VERA rubric (see `01-pushback-handling.md`)
4. Debrief: what did you validate well? where did you get defensive?

### Record yourself
The most uncomfortable and most effective practice:
1. Record a 5-minute mock using one of these scripts
2. Play it back — listen only for:
   - Did you validate before reframing?
   - Did you ask a question after an objection?
   - How long was your average response? (Target: ≤90 seconds)
   - Did your voice stay calm?
