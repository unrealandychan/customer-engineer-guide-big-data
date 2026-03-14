# Interview B — GCA: Hypothetical Question Bank

15 real hypothetical questions from Google interviews, organized by type.

**Rule:** Use the 4-step skeleton from `frameworks.md`. Always clarify first. Always close with a success metric.

---

## Category 1: General / Open (Any Role)

These test raw structured thinking. The topic doesn't matter — your process does.

1. **"How would you go about opening a pastry shop?"**
   - Decompose into: market (who are the customers?), supply (ingredients, staff, location), operations (regulatory, hours, pricing), marketing, success metrics
   - Key: don't skip customer/demand analysis. Start there.

2. **"If you were the chief traffic officer of New York City and someone asked you to reduce gridlock, how would you solve it?"**
   - Decompose: measure current state → root cause analysis (peak hours? specific corridors?) → short-term interventions (signal timing, congestion pricing) → long-term (infrastructure, public transit) → success KPI (avg commute time, gridlock incidents)
   - Key: data-first. What would you measure *first* before making any changes?

3. **"How would you measure the effectiveness of our employee referral program?"**
   - Decompose: what does "effective" mean? (cost per hire, quality of hire, retention, speed) → data sources (ATS, HR, manager ratings) → baselines → A/B test design
   - Key: define the metric before proposing the solution.

4. **"How would you design a customer support operation for 2 million Google Workspace businesses?"**
   - Decompose: customer segments (SMB vs enterprise have different needs), channels (self-serve docs, chat, phone, dedicated CSM), routing/triage logic, escalation path, metrics (CSAT, TTR, first-contact resolution)

5. **"How would you organize the grand opening event of a new Google office?"**
   - Decompose: stakeholders (employees, media, community, execs) → logistics (venue capacity, catering, A/V, security) → communications plan → success metrics → contingency

---

## Category 2: Role-Adjacent (CE / Data / Cloud)

These are most likely for your round. Practice these the most.

6. **"How would you convince a GCP customer to expand their cloud services?"**
   - Clarify: which services do they already use? What's their outcome goal (cost reduction, speed, capability)?
   - Decompose: current state assessment → TCO analysis → risk profile → phased expansion plan → quick wins to demonstrate value
   - Key CE skill: lead with business value, not product features.

7. **"How would you design an analytics platform for a retail customer merging 3 brands?"**
   - This is your Presentation scenario — answer using the Data Flow Template (Ingest → Store → Process → Serve → Govern)
   - Key: start with who needs what decisions at what latency. That drives everything.

8. **"How would you decide whether to migrate a customer's data platform to the cloud?"**
   - Decompose: assess current state (cost, reliability, scale ceiling) → migration readiness (skills, data volumes, compliance) → TCO comparison → risk analysis → phased approach
   - Key: it's not always "yes migrate." Show you can say "not yet, and here's when."

9. **"A customer says BigQuery is too expensive. How do you respond?"**
   - Clarify: expensive compared to what? What's the current spend pattern?
   - Decompose: on-demand vs reserved slots, query optimization (partitioning, clustering), materialized views, BI Engine for repeated queries, cross-SKU comparison
   - Key: never argue. First validate their concern with data.

10. **"How would you build a data governance framework for a customer with data in 3 different clouds?"**
    - Decompose: catalog (what data exists), classification (what's sensitive), access control (who can see what), lineage (where did data come from), audit (who accessed it)
    - GCP answer: Dataplex for unified governance layer; Data Catalog for metadata. AWS parity: Lake Formation + Glue Catalog.

---

## Category 3: Team / People Hypotheticals

These test leadership instinct and interpersonal maturity.

11. **"You have a coworker who is not comfortable working on the team. What do you do?"**
    - 1:1 first to understand root cause. Is it role fit? Interpersonal conflict? Unclear expectations? Then address systemically. Don't assume.

12. **"Your team isn't innovating. How do you analyze the situation and make them innovate?"**
    - Triangle Method: (1) diagnose root cause (fear of failure? lack of time? wrong incentives?), (2) create psychological safety for experimentation, (3) structure a time/space for innovation (e.g. 20% time, quarterly hackathon)
    - Key: don't jump to solutions before diagnosing.

13. **"Imagine your manager strongly believed in something and you did not. How do you manage it?"**
    - Disagree and commit — but disagree with data first. "I'd share my concern once, with evidence. If we still disagree, I'd commit to the decision and revisit with results."
    - Key: this is a Googleyness question disguised as a hypothetical. Show intellectual humility + bias for action.

14. **"A developer is not testing their work. How would you deal with this?"**
    - Triangle Method: (1) understand why (awareness? time pressure? unclear standards?), (2) address the systemic cause (add to definition of done, create a testing culture), (3) follow up with specific feedback to the individual
    - Key: don't go straight to escalation. Show problem-solving first.

15. **"What would you do if you were introduced to new technology you'd never used before and had to use it immediately?"**
    - "I'd start by understanding the conceptual model, not the syntax. Then find the analogue to something I already know — e.g. Pub/Sub is like SNS+SQS, Dataflow is like Kinesis Analytics." 
    - Key: this is about learning agility. Name your mental model for learning fast.

---

## Quick-Prep: Practice These Cold

The 3 most likely for your round with Gene (Data Analytics Sales Manager):

- Q6: "How would you convince a GCP customer to expand their cloud services?"
- Q7: "How would you design an analytics platform for a retail customer merging 3 brands?"
- Q13: "Your manager strongly believed in something and you didn't — how do you manage it?"

For each: timer on. Clarify → Decompose → Deep dive → Conclude + metric. No looking at notes.
