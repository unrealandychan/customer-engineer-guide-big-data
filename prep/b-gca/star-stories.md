# Interview B — GCA: STAR Story Bank

6 deep stories. Each one must be personalized with YOUR real numbers. The structure is here — fill in the bracketed sections with your actual experience.

**Use the story reuse matrix in `behavioral-questions.md` to map these to question themes.**

---

## Story 1 — Failing / Delayed Project (Theme: Problem-Solving Under Pressure + Resilience)

**Backstory (what led to this — interviewers probe hard here):**
> [Describe the project, the team structure, what the original plan was, and what started going wrong. 2–3 sentences.]

**STAR:**

- **Situation:** [Describe the context — company, team size, timeline, what was at stake. Include the scale: "This was a $Xm project..." or "This affected N customers..."]

- **Task:** [Your specific responsibility. "I was the tech lead / sole owner / responsible for X deliverable by Y date."]

- **Action:**
  - Step 1: [What you did first — likely: assess the gap, communicate clearly, stop the bleeding]
  - Step 2: [What structural change you made — replanning, scope reduction, bringing in support]
  - Step 3: [How you rallied the team / stakeholders through the change]
  - Key decision: [The hardest call you made — this is what interviewers love. "I decided to cut X feature even though stakeholders wanted it, because..."]

- **Result:** [Specific outcome — "We delivered with a 2-week delay vs originally 3-month risk", "Reduced scope 30% but shipped 100% of core use cases on time", "Customer renewed at $XM despite the delay because of how we managed it"]

- **Lessons:** [What you'd do differently. "I'd have flagged the risk 2 weeks earlier when I first saw the warning signs. I was too optimistic. Now I apply a formal risk-review checkpoint at 30% of any project."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What would you have done differently?"* → [Your revised answer focusing on earlier risk identification]
2. *"How did others react to the delay?"* → [Names the emotional/political reality, shows EQ]
3. *"What would have happened if you'd done nothing?"* → [Shows you understand the counterfactual — "We would have missed by 3 months, lost the customer, and damaged the team's credibility with leadership."]

---

## Story 2 — Data Pipeline Design / Platform Build (Theme: Project Ownership + Data-Driven)

**Backstory:**
> [Describe why you needed to build this. What was the business pain? What was broken or missing? What was the scale of data or users affected?]

**STAR:**

- **Situation:** ["Our [data team / analytics function] was [spending X hours/week on manual reporting / couldn't trust data / couldn't scale past Y records]..."]

- **Task:** [Design, build, and ship a new data pipeline/platform. Owned end-to-end.]

- **Action:**
  - Step 1: [Discovery — what did you learn first? Existing data architecture, pain points, stakeholder needs]
  - Step 2: [Design decisions — what tech did you choose and why. What did you reject and why. This is your chance to show AWS/GCP depth.]
  - Step 3: [Implementation — how you phased it, how you validated, how you handled failure modes]
  - Key technical tradeoff: ["I chose X over Y because at our scale, Y would have cost $X/month more and had Y latency. The downside was we gave up Z capability, which I mitigated by..."]

- **Result:** ["Reduced data latency from 24h to 15 minutes", "Saved $X in infrastructure costs", "Enabled N analysts to self-serve, freeing X hours/week of engineering time"]

- **Lessons:** ["I underestimated the governance and documentation work. The pipeline worked but took 2 extra months to get adopted because we hadn't built trust in the data quality. Now I treat data quality validation as core to the pipeline, not an afterthought."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What would you build differently with today's tools?"* → [Show GCP knowledge: "I'd use Dataflow instead of... and Dataplex for governance from day one"]
2. *"How did you handle data quality issues?"* → [Show concreteness: row counts, schema validation, alerting strategy]
3. *"How did stakeholders react to the new system?"* → [Shows adoption/change management awareness]

---

## Story 3 — Production Incident (Theme: Problem-Solving + Influence + Resilience)

**Backstory:**
> [What system, what scale, what time of day/day of week, what failed. Give the drama a face: "This was Black Friday" or "This brought down our customer-facing dashboard for our top 10 enterprise accounts."]

**STAR:**

- **Situation:** ["Our [system] went down at [time]. It affected [N customers / $X revenue at risk / SLA of X hours violation if not fixed]."]

- **Task:** ["I was the on-call lead / I volunteered to own incident response / I was pulled in because I'd built the component."]

- **Action:**
  - Step 1: [How you triaged — what's the blast radius? Who's affected? What's the immediate mitigation?]
  - Step 2: [Root cause investigation — how you narrowed it down, what tools you used]
  - Step 3: [Fix + rollback/deploy + communication to stakeholders]
  - Key leadership moment: ["I made the call to roll back even though the fix was 80% ready, because the risk of a longer outage outweighed another 2-hour mitigation window."]

- **Result:** ["Restored service in X hours vs Y-hour SLA", "Wrote the post-mortem, identified 3 systemic gaps, shipped preventive fixes within 2 weeks", "Zero repeat incidents in the following 12 months"]

- **Lessons:** ["We had no runbook for this failure mode. I led the creation of runbooks for our top 10 failure scenarios afterward. Also, our alerting fired 45 minutes after the first anomalous signal — I reduced that to 5 minutes."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What systemic change did you make?"* → [Shows follow-through beyond just fixing the immediate issue]
2. *"How did customers/stakeholders react?"* → [Shows communication and accountability]
3. *"What was the hardest moment during the incident?"* → [Shows self-awareness under pressure]

---

## Story 4 — Decision With Incomplete Data (Theme: Data-Driven + Influence)

**Backstory:**
> [Describe the business decision that needed to be made, why data was incomplete or ambiguous, what the stakes were, and who else was involved in the decision.]

**STAR:**

- **Situation:** ["We had [N weeks] to decide whether to [migrate / launch / invest in X]. The data was incomplete because [reason: system hadn't been instrumented / we were in a new market / the relevant data existed in 3 silos that hadn't been joined]."]

- **Task:** ["I was responsible for the recommendation. The decision affected [N customers / $X budget / 6-month roadmap]."]

- **Action:**
  - Step 1: [What proxy data you used — be specific. "We didn't have churn data for this segment, so I used support ticket volume and NPS as leading indicators."]
  - Step 2: [How you quantified uncertainty — "I built a three-scenario model: bear/base/bull. I was clear that this was based on a key assumption: X. If X was wrong by 20%, our decision would flip."]
  - Step 3: [How you presented the recommendation — with confidence intervals, named assumptions, and a trigger condition to revisit]
  - Key intellectually honest moment: ["I told the exec team: 'I'm 70% confident in this recommendation. Here's the one assumption that could make it wrong, and here's how we'll know within 6 weeks.'"]

- **Result:** ["Decision was made, outcome was [X]. The [key assumption] turned out to be [right/wrong], and we [revised/stayed the course] because we'd set up the review checkpoint."]

- **Lessons:** ["I'd have pushed harder to instrument the missing data earlier in the project rather than working around it. The 2 weeks we spent on proxy analysis could have been avoided if we'd added the tracking 2 months earlier."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What if you'd been wrong?"* → [Show you had a fallback / reversal plan]
2. *"How did you communicate uncertainty to leadership?"* → [Show exec communication maturity]
3. *"Was there pressure to make a more confident call than the data supported?"* → [This is a Googleyness probe — "Do the right thing" under pressure]

---

## Story 5 — Influencing With Analytics (Theme: Influence + Data-Driven + Ownership)

**Backstory:**
> [Describe who you needed to influence, what they believed initially, and why the data you had was compelling but not immediately obvious to them. This story should have a "before and after" belief change.]

**STAR:**

- **Situation:** ["[Person/team] believed [X]. The consequence of acting on that belief was [Y, which I thought was wrong/suboptimal]. I had data that suggested [Z]."]

- **Task:** ["Convince [stakeholder] to change course without having formal authority over them."]

- **Action:**
  - Step 1: [Understand their frame first — what did they believe and why? Don't lead with your data.]
  - Step 2: [Build credibility — show you understand their view. "I agreed with them on [X]. The data diverged on [specific point]."]
  - Step 3: [Present data in their language — business outcomes, not technical metrics. "Instead of showing query latency, I showed it as: 'this means your analysts get answers in 15 min vs 24 hours.'"]
  - Key influence move: ["I proposed a 2-week experiment rather than asking them to commit. Lower stakes, faster feedback."]

- **Result:** ["[Stakeholder] agreed to [change / experiment / decision]. Outcome was [X]. The relationship [strengthened / led to further collaboration on Y]."]

- **Lessons:** ["I learned that data alone rarely changes minds. What changed their mind was framing the data in terms of outcomes they already cared about. I now always ask 'what does success look like to them' before presenting any analysis."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What if they'd still said no?"* → [Show you'd commit to their decision while preserving the relationship to revisit]
2. *"How did you handle it if they later claimed the idea was theirs?"* → [Shows no-ego Googleyness]
3. *"How do you handle data that proves you wrong?"* → [Key intellectual honesty signal]

---

## Story 6 — Difficult Stakeholder / Customer Conflict (Theme: Influence + Resilience + Ownership)

**Backstory:**
> [Describe the relationship, what went wrong, why it was emotionally or politically charged. Was it a customer threatening to churn? A senior internal stakeholder blocking your project? A peer who was undermining the team?]

**STAR:**

- **Situation:** ["[Stakeholder] was [unhappy / blocking / threatening X]. The stakes were [N customers / $X revenue / team morale / project timeline]."]

- **Task:** ["Repair the relationship and unblock the situation without escalating unnecessarily."]

- **Action:**
  - Step 1: [Listen first. What was the root cause of their frustration?]
  - Step 2: [Acknowledge before defending. What were they right about?]
  - Step 3: [Propose a concrete path forward — something measurable and time-bound. "I committed to [X] by [date] and followed up in writing."]
  - Key maturity moment: ["I resisted the urge to defend my team immediately. Their frustration was valid even if some of their specific claims were inaccurate."]

- **Result:** ["Relationship recovered. [Customer stayed / Stakeholder became an advocate / Project unblocked]. Specifically: [metric — e.g. 'Customer renewed at $XM', 'Project launched on time', 'Escalation was dropped']."]

- **Lessons:** ["I should have caught the warning signs 3 weeks earlier. There were signals I dismissed. Now I treat early disengagement or passive communication as a red flag and address it immediately."]

**3 Follow-Up Probes + Scripted Answers:**
1. *"What would you do if the stakeholder was unreasonable — factually wrong but powerful?"* → [Shows how you escalate professionally without burning bridges]
2. *"How did the rest of the team feel?"* → [Shows team-awareness and leadership]
3. *"Would you do anything differently now?"* → [Lessons line reinforced]

---

## Pre-Interview Checklist

Before Interview B, run through each story and verify:
- [ ] Does it contain at least one specific number in the Result?
- [ ] Does it have a Lessons line?
- [ ] Can you answer all 3 follow-up probes without looking at notes?
- [ ] Is the Action section clearly about what YOU did, not "we"?
- [ ] Is the answer under 4 minutes when spoken out loud?
