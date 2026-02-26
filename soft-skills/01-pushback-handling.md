# 🥊 Pushback Handling — 15 Real Scenarios

> **The golden rule:** Never fight pushback. Validate → Explore → Redirect.  
> Fighting a customer's concern makes them defend it harder.  
> Validating it makes them feel heard — then you can move together.

---

## The VERA Framework (Use This Every Time)

```
V — Validate    "That's a fair concern / I hear that a lot / That makes sense."
E — Explore     "Can I ask what's driving that? / What's the concern specifically?"
R — Reframe     "Here's how I'd look at it..." / "What I've seen in similar situations..."
A — Anchor      Tie back to their business goal, not your product feature.
```

**What NOT to do:**
- ❌ "Actually, that's not right..." (combative)
- ❌ "But BigQuery is much better than..." (defensive)
- ❌ Silence + deer-in-headlights look
- ❌ Over-explaining with 5 minutes of technical detail

---

## The 15 Scenarios

---

### Scenario 1: "BigQuery is too expensive."

**Context:** Mid-conversation. CFO or technical lead is comparing sticker prices.

**Pushback:** *"We looked at the pricing page. BigQuery on-demand is $6.25 per terabyte. Our data team runs hundreds of queries a day. This is going to cost us a fortune."*

**VERA Response:**

> **V:** "That's a completely fair thing to look at first — pricing page math is the natural starting point."  
> **E:** "Can I ask — when you say hundreds of queries, do you know roughly how much data each query is scanning today?"  
> **R:** "Here's the thing: the $6.25/TiB is the maximum you'd pay with zero optimization. In practice, most teams reduce their scanned bytes by 60–80% just by adding partition filters and selecting specific columns. So a query that looks like it costs $10 often costs $0.50 after tuning. Beyond that, once your spend crosses roughly $2,000/month, a capacity commitment cuts costs by 20–40%. I'd love to run a quick TCO comparison with your actual query patterns — that usually looks very different from the sticker price."  
> **A:** "The real question is: what's the cost of your current infrastructure — including the ops team managing it?"

**If they push again:** *"We already have Snowflake and it's cheaper."*
> "Snowflake and BigQuery are priced very differently — Snowflake charges per credit (compute time), BigQuery charges per byte scanned. Which is cheaper depends entirely on your query patterns. Teams with many concurrent short queries often find BigQuery cheaper; teams running long serial queries sometimes prefer Snowflake's model. Can we look at a specific workload together?"

---

### Scenario 2: "We're already on AWS. We don't need another cloud."

**Context:** Early discovery. Customer has significant AWS investment.

**Pushback:** *"We've spent three years building on AWS. Everything is in S3, we use Redshift and Glue. Why would we add GCP?"*

**VERA Response:**

> **V:** "Three years of AWS investment is real — I'm not here to suggest you rip and replace anything."  
> **E:** "What are the workloads you're happiest with on AWS? And where are the friction points?"  
> **R:** "What most multi-cloud companies do is pick the best tool for each workload. AWS is strong broadly, but BigQuery and GCP's AI/ML stack are consistently where teams land when they need serious analytics scale or Vertex AI capability. You don't need to choose — BigQuery can query data sitting in S3 directly via BigQuery Omni, so you'd get BigQuery's analytics power without moving a single byte."  
> **A:** "The question isn't AWS vs GCP. It's: are there workloads where your team is frustrated, slow, or over-spending? That's where GCP typically wins a foothold."

---

### Scenario 3: "We're worried about vendor lock-in."

**Context:** Technical architect or CTO pushback during architecture discussion.

**Pushback:** *"Last time we bet on a proprietary platform, we were trapped for six years. We're not doing that again."*

**VERA Response:**

> **V:** "That's one of the most common — and legitimate — concerns I hear, especially from teams that have been through a vendor lock-in experience. That instinct is right."  
> **E:** "What specifically are you worried about being locked into — the data format, the SQL dialect, the APIs?"  
> **R:** "Let me address each: BigQuery supports Apache Iceberg natively — your data can sit in Parquet files on Cloud Storage that any engine can read. The SQL dialect is ANSI-standard. If you wanted to leave tomorrow, your data is in open files, your SQL runs elsewhere. The only lock-in is the managed service itself — you'd give up the serverless convenience, but you'd keep your data and your code."  
> **A:** "Honestly, the bigger lock-in risk is staying on on-premise Hadoop — those environments are very hard to migrate out of once teams build years of jobs on them."

---

### Scenario 4: "We have a Hadoop cluster and it works fine."

**Context:** Mid-size company with existing on-prem infrastructure.

**Pushback:** *"Our Hadoop cluster handles our workloads. Our team knows it. Why fix what isn't broken?"*

**VERA Response:**

> **V:** "If it's truly working well, I respect that — not every environment needs to change."  
> **E:** "When you say 'works fine' — what does your team spend the most time on? Is it running jobs, or maintaining the cluster itself?"  
> **R:** "The pattern I see most often is that the jobs work, but the ops burden is significant — patches, capacity planning, hardware refreshes, dependency conflicts. The team that could be building analytics capabilities is spending 30–40% of their time on cluster maintenance. Dataproc doesn't require you to rewrite your Spark jobs — it runs the same code, but on ephemeral clusters you spin up and tear down in 90 seconds. You pay only for what you use."  
> **A:** "The real question is: what could your team build if they had that maintenance time back?"

---

### Scenario 5: "We don't trust the cloud with our sensitive data."

**Context:** Financial services, healthcare, or government prospect.

**Pushback:** *"Our data has PII and financial records. We can't put that in the cloud — our compliance team would never approve it."*

**VERA Response:**

> **V:** "Security and compliance are non-negotiable — your instinct to protect that data is exactly right."  
> **E:** "Which compliance frameworks are you working under — GDPR, SOC 2, PCI-DSS, HIPAA?"  
> **R:** "Google Cloud has certifications for all of those. BigQuery Enterprise Plus edition includes Assured Workloads — that's the framework for regulated industries including FedRAMP High, HIPAA, PCI-DSS, and ISO 27001. Specifically for PII: column-level access control means your analysts can query a table without ever seeing the actual PII values — they see masked data unless they have explicit permission. Data never leaves your chosen region. Customer-managed encryption keys mean Google can't access your data even if compelled to."  
> **A:** "The compliance conversation is actually easier than most teams expect. Would it help if I connected you with our compliance team to walk through your specific framework requirements?"

---

### Scenario 6: "Your competitor is cheaper / better / already here."

**Context:** A competitor is already in the deal — Snowflake, Databricks, Redshift.

**Pushback (Snowflake):** *"We're evaluating Snowflake and they're offering us a significant discount."*

**VERA Response:**

> **V:** "Snowflake is a strong product — I'd expect them to compete hard on price."  
> **E:** "What's driving the evaluation — is it purely cost, or are there capability gaps you're trying to address?"  
> **R:** "Here's where BigQuery tends to differentiate: if your team is also working on AI and ML, BigQuery is the only data warehouse where you can run Gemini and Vertex AI models directly in SQL — no separate platform. If you have global data residency requirements, BigQuery's global queries let you query EU + APAC + US data in one SQL statement. And BigQuery's serverless model means no warehouses to size, no credits to manage — you pay for what you scan, and scale is infinite."  
> **A:** "The discount is real now — but what does Snowflake cost at 3x your current data volume? That's usually where the conversation changes."

**Pushback (Databricks):** *"Our data science team is already using Databricks."*

> "Great — Databricks and BigQuery complement each other well in many architectures. Databricks Spark for ML training on raw data, BigQuery for the analytics layer and BI reporting. We're not asking you to replace Databricks for ML — we're asking whether BigQuery can serve your analytics and SQL users better than whatever they're using today."

---

### Scenario 7: "This is too complex for our team."

**Context:** Mid-market customer with a small team.

**Pushback:** *"We're a team of 5 data engineers. We don't have the bandwidth to learn a new platform."*

**VERA Response:**

> **V:** "That's a real constraint — a small team can't afford a long migration or steep learning curve."  
> **E:** "What does your team spend the most time on right now? And which skills do they already have?"  
> **R:** "Here's what I'd say about the learning curve: BigQuery uses standard SQL. If your team can write SQL today, they can be productive in BigQuery in a week. There's no cluster to configure, no HDFS to manage, no YARN to tune. The serverless model means the hardest operational work just disappears. For your Spark jobs, Dataproc runs the same PySpark code with minimal changes — it's not a rewrite."  
> **A:** "The question is whether the 2-week investment to migrate a first workload is worth getting back the time your team spends on cluster maintenance. For a 5-person team, that time is especially valuable."

---

### Scenario 8: "We had a bad experience with Google before."

**Context:** Customer has prior negative experience with a Google product or sales process.

**Pushback:** *"Honestly, we used Google Workspace before and the support was terrible. I'm not sure I trust Google as a vendor."*

**VERA Response:**

> **V:** "I appreciate you being direct about that — past experience with a vendor matters, and I'm not going to dismiss it."  
> **E:** "What specifically was the issue — was it product quality, response time, or the relationship itself?"  
> **R:** "Google Cloud and Google Workspace operate very differently — GCP has dedicated enterprise support tiers with SLAs, named TAMs (Technical Account Managers), and 24/7 P1 response. The business model is also different: GCP's revenue depends on you growing on the platform, so the incentive to support you is much more direct. That said — I'd rather show you than tell you. Can we agree on a proof-of-concept with a defined timeline and support commitment in writing?"  
> **A:** "Let me make you a specific commitment: here's what support looks like, here are the SLAs, here is how to escalate. Judge us on that."

---

### Scenario 9: Pushback in the middle of a whiteboard — "That won't scale."

**Context:** You're drawing an architecture diagram. A technical stakeholder challenges it.

**Pushback:** *"Your architecture puts all the data through a single Pub/Sub topic. That's going to be a bottleneck at our volume — 10 million events per second."*

**VERA Response (in-the-moment):**

> **V:** "That's a sharp observation — and you're right to flag it."  
> **E:** "What's your peak events-per-second today, and do you have spiky patterns or is it more consistent?"  
> **R:** "Pub/Sub is actually designed for this — it auto-scales to millions of messages per second without any configuration. The published limit is 10 GB/s per topic per region, and ordering keys let you maintain sequence within partitions. If you need cross-region, you'd use regional topics with Pub/Sub Lite for the highest throughput tier. Let me adjust the diagram — [start drawing] — here's how we'd structure it for your volume with ordering guarantees..."  
> **A:** "The design is actually stronger than I showed — let me make that explicit."

**If you don't know the answer:**
> "That's a specific number I want to make sure I get right rather than guess. Can I note that and come back to you with the exact throughput specs by end of day? I don't want to design around a number I'm not certain of."

---

### Scenario 10: "You're just trying to sell me something."

**Context:** Skeptical buyer, often mid-deal when they feel pressure.

**Pushback:** *"Look, I know you're here to sell GCP. Everything you're saying sounds great, but of course it does — you work for Google."*

**VERA Response:**

> **V:** "You're right — I represent Google, so you should hold that in mind when you evaluate what I say."  
> *(Pause — let that land.)*  
> **E:** "Let me ask you something: what would it take for you to trust the recommendation? What evidence would be meaningful to you — not from me, but from somewhere else?"  
> **R:** "I'd rather give you the real picture, including where GCP isn't the best fit. For example: if your workload is 90% OLTP — high-QPS transactional writes — BigQuery isn't the right choice; Cloud Spanner or Cloud SQL would be. I gain more credibility by being honest about that than by over-promising. What I am confident in is that for analytics workloads at your scale, BigQuery's economics and performance are hard to match. But let the data make the case — can we run a proof of concept on a real workload and let you measure it yourself?"  
> **A:** "I'm not asking you to trust me. I'm asking for the chance to prove it."

---

### Scenario 11: "The migration risk is too high."

**Context:** Customer has critical production workloads they're afraid to touch.

**Pushback:** *"We have 200 Spark jobs that run our nightly ETL. If even one fails, we miss our SLA. We can't risk migrating those."*

**VERA Response:**

> **V:** "Production SLA risk is the most important thing to get right — that concern is completely valid."  
> **E:** "Of the 200 jobs, how many are truly critical-path? And what does a failed SLA look like — business impact, financial penalty?"  
> **R:** "The typical approach is a shadow migration: run the new GCP pipeline in parallel with your existing jobs for 4–8 weeks. You compare outputs, measure performance, and don't cut over until you've proven equivalence at least 30 consecutive days. Dataproc runs the same PySpark code — in many cases we've migrated jobs with zero code changes. We'd start with a non-critical job, prove the pattern, then work up to the critical-path ones with full rollback capability at every stage."  
> **A:** "The goal is to make the migration lower risk than staying on aging infrastructure — not zero risk, because nothing is, but lower than the status quo."

---

### Scenario 12: "Our CTO / CISO hasn't approved this."

**Context:** Champion is sold, but faces internal blockers.

**Pushback:** *"I love the solution, but our CISO is very conservative. I don't think I can get this approved."*

**VERA Response:**

> **V:** "Internal approval is often the hardest part of any technology decision — I've seen great projects stall there."  
> **E:** "What is your CISO most likely to challenge — data residency, encryption, access controls, or compliance certifications?"  
> **R:** "I'd like to help you make the case internally. Let me give you a security brief specifically written for CISO review — it covers data residency commitments, encryption in transit and at rest, CMEK, VPC Service Controls, and all the compliance certifications relevant to your industry. I can also offer a security-focused reference call with a CISO at a company similar to yours who's already on GCP."  
> **A:** "You shouldn't have to fight this battle alone. Let's build the internal deck together."

---

### Scenario 13: "I've heard BigQuery has hidden costs."

**Context:** After pricing discussion — customer has heard anecdotes from the community.

**Pushback:** *"I talked to someone at another company who said their BigQuery bill was 10x what they expected. What am I missing?"*

**VERA Response:**

> **V:** "That's a real thing that happens — and I'd rather you know about it upfront than discover it after you've signed."  
> **E:** "Did they mention what specifically drove the surprise? I want to understand if it's the same risk you'd face."  
> **R:** "The most common causes: 1) No partition filters on large tables — a single 'SELECT * FROM 10TB table' with no WHERE clause on the partition column scans the whole thing. 2) Exploratory analysts running ad-hoc queries without understanding bytes scanned. Both are solved with the same thing: require_partition_filter set to TRUE on large tables, and Requester Pays for shared datasets. I'd also recommend setting up budget alerts on your first month — set a hard cap at 2x what you expect, so you catch any anomalies early. Transparency upfront is part of why I'm telling you this now."  
> **A:** "The cost controls exist — they just need to be turned on deliberately."

---

### Scenario 14: "We want everything on-premise for data sovereignty."

**Context:** European or government customer with strict data sovereignty laws.

**Pushback:** *"Our legal team says all data must stay within [Country X]. We cannot use a US company's cloud."*

**VERA Response:**

> **V:** "Data sovereignty is a legal requirement, not a preference — I take that completely seriously."  
> **E:** "Is the concern about data leaving the country, or about the legal jurisdiction the company is subject to — even if the data stays in-country?"  
> **R:** "GCP has data center regions in [relevant country]. Data stored in those regions stays there by default — it doesn't replicate outside without your explicit configuration. For the legal jurisdiction question: Google Cloud is subject to US law, which is a legitimate concern some regulators have. For those situations, Sovereign Cloud offerings exist — in Germany and France for example, GCP is operated by a local entity (T-Systems in Germany) meaning Google employees in the US cannot access the infrastructure. That's the path forward for the strictest requirements."  
> **A:** "This isn't a blocker — it's a configuration and commercial question. Let me connect you with our public sector team who specializes in exactly this."

---

### Scenario 15: "Just send me a proposal and we'll decide."

**Context:** Customer is trying to end the conversation before you've understood the real need.

**Pushback:** *"This is interesting. Can you just put together a proposal and pricing and send it over?"*

**VERA Response (slow down, don't comply immediately):**

> **V:** "Absolutely — I want to make sure that proposal is actually useful to you rather than a generic document."  
> **E:** "Before I put that together: I want to make sure I'm proposing the right architecture for your situation. Can I ask you three quick questions so I don't waste your time with something generic? [Wait for yes.] What's the workload you're looking to solve first? What's the timeline pressure — is there a date driving this? And who else on your side would be involved in the decision?"  
> **R:** *(After getting answers)* "Perfect — that helps me tailor this significantly. I'll have something specific to your situation over by [date]. Would it also be useful to include a comparison of two or three sizing options so you can see the trade-offs?"  
> **A:** "A good proposal takes one more conversation to do right. You'll get a much more useful document — and I'll be asking better questions than a generic template."

---

## Quick Reference: The 5 Deflection Phrases (Memorize These)

| Situation | What to Say |
|-----------|------------|
| You don't know the answer | *"That's a specific detail I want to get right — let me confirm and follow up by end of day."* |
| Customer makes a wrong technical claim | *"That's a common misconception — let me show you what we actually see..."* |
| Customer is comparing to a competitor | *"Both are strong in different areas — let me show you the specific dimension where this matters for your workload."* |
| Customer is rushing to a decision | *"I want to make sure this is the right decision for you, not just the fastest one — can we take 10 more minutes?"* |
| Room is going off-topic | *"That's a great point — let me park it here [write on whiteboard] and we'll come back to it. For now, let me finish this thread..."* |

---

## Practice Drill: 5-Minute Pushback Sprint

Set a timer. Have a partner throw you random scenario numbers. Respond using VERA.

Scoring:
- ✅ Validated first (no immediate counter-argument)
- ✅ Asked an exploratory question
- ✅ Reframed without being defensive
- ✅ Anchored to business value, not product feature
- ✅ Under 90 seconds total
