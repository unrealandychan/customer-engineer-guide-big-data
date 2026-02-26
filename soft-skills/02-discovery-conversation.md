# 🔍 Discovery Conversations — Active Listening & Needs Mapping

> **Core mindset:** You are a doctor, not a salesperson.  
> A doctor doesn't prescribe before diagnosing.  
> A consultant doesn't propose before discovering.  
> Discovery is not a formality — it's the most important part of the engagement.

---

## The SPIN Framework

Developed by Neil Rackham (Huthwaite Research). The most evidence-backed discovery framework for complex technical sales.

```
S — Situation    "What does your current environment look like?"
P — Problem      "Where are the pain points?"
I — Implication  "What happens if this isn't fixed?"
N — Need-Payoff  "What would solving this mean for you?"
```

**Why the order matters:**  
Most consultants ask only Situation questions ("Tell me about your stack").  
The magic is in Implication — that's where the customer articulates *their own* urgency.  
You don't manufacture urgency. You help them discover it.

---

## Question Laddering (Surface → Depth)

Start broad. Narrow with each follow-up. Each question should come from the answer above.

```
Level 1 (Surface):   "Tell me about your current data platform."
Level 2 (Process):   "How does data get from source systems into your warehouse today?"
Level 3 (Pain):      "Where does that process break down or slow you down?"
Level 4 (Impact):    "When it breaks down, what happens — to the team? To the business?"
Level 5 (Emotion):   "How much of your team's time goes into managing that vs. building new things?"
Level 6 (Vision):    "If that problem didn't exist, what would your team be doing instead?"
```

**Rule:** Never skip levels. Jumping from Level 1 to Level 4 feels interrogative and breaks trust.

---

## The 5 Whys (Technical Discovery)

Use this to get from symptom to root cause. Especially effective with engineers.

**Example:**
```
Customer: "Our pipeline is slow."
Why 1: "Why is it slow?" → "The jobs take 4+ hours."
Why 2: "Why do they take that long?" → "We're running on a 3-node Hadoop cluster."
Why 3: "Why 3 nodes?" → "That's what we provisioned 5 years ago."
Why 4: "Why hasn't it been scaled?" → "We'd have to buy hardware and rack it."
Why 5: "Why does that matter now?" → "We're onboarding 10 new data sources next quarter."

Root cause: Fixed infrastructure that can't scale to meet upcoming demand.
The real pitch: Elastic compute (Dataproc / BigQuery) — not "it's faster."
```

---

## 30-Minute Discovery Call Structure

```
00:00 – 02:00  Opening & rapport
               "Thanks for your time — just to calibrate, I have us until [time]. 
                Before I tell you anything about GCP, I'd love to understand your 
                world first. Is that okay?"

02:00 – 08:00  Situation questions (S)
               Current stack, team size, data volumes, existing tools.
               
08:00 – 15:00  Problem + Implication questions (P + I)
               Where does friction exist? What breaks? What's the business cost?
               
15:00 – 20:00  Need-Payoff (N)
               "If we solved [pain], what would that unlock for you?"
               "What would success look like in 12 months?"
               
20:00 – 25:00  Your brief summary + hypothesis
               "Based on what you've told me, here's what I think is happening..."
               [Wait for them to correct or confirm]
               
25:00 – 30:00  Next steps
               "I'd like to propose a more detailed technical session. 
                Who else should be in that conversation?"
```

**The 70/30 rule:** Customer should be talking 70% of the time. If you're talking more, stop and ask a question.

---

## Active Listening Signals

### In-person
| Signal | What to do |
|--------|-----------|
| Customer leans forward | They're engaged — slow down, go deeper |
| Customer checks phone | You're losing them — ask a direct question |
| Arms crossed | Resistance — validate before continuing |
| Head tilt | Confusion — check in: *"Am I being clear on this?"* |
| Nodding | Agreement — this is your anchor point to return to |

### On video calls
| Signal | What to do |
|--------|-----------|
| Looking away from camera | Distracted — ask for their opinion |
| Camera off | Disengaged or multitasking — normalize returning |
| Long pause after your question | They're thinking — don't fill the silence |
| "Mm-hmm, yeah, yeah" (fast) | They want you to speed up or stop |
| "Interesting..." (pause) | They have a concern — ask what they're thinking |

**The most powerful active listening move:** Silence.  
After a customer answers, pause 3 seconds before responding.  
Most consultants fill the silence. That pause often produces the most honest next statement.

---

## Needs Mapping Template

Use this during or immediately after a discovery call.

```
CUSTOMER:  [Company name]
DATE:      [Date]
ATTENDEES: [Names + roles]

SITUATION (what they have)
- Current platform:
- Team size / structure:
- Data volumes (TB/day, events/sec):
- Key tools in stack:

PROBLEMS (what hurts)
- Pain 1:
- Pain 2:
- Pain 3:

IMPLICATIONS (cost of doing nothing)
- Business impact:
- Operational cost:
- Opportunity cost:

NEED-PAYOFF (what success looks like)
- Their words (quote):
- Timeline:
- Decision criteria:

HYPOTHESIS (your assessment)
- Root cause:
- Proposed approach:
- What I need to validate:

OPEN QUESTIONS (to follow up)
- [Question 1]
- [Question 2]
```

---

## The 5 Questions That Always Get Honest Answers

These are uncomfortable-but-gold questions. Use them carefully, after trust is established.

1. **"What would make you walk away from this project?"**  
   *(Surfaces hidden blockers. Better to know now.)*

2. **"Who on your team is most skeptical of this approach?"**  
   *(Reveals internal politics. Lets you prepare.)*

3. **"If budget wasn't a constraint, what would you do?"**  
   *(Reveals the ideal state. Work backwards from there.)*

4. **"What's happened in the past when your team has tried to solve this?"**  
   *(Uncovers prior failures that might repeat.)*

5. **"Is there something that would make you feel this is too risky to proceed?"**  
   *(The inversion question — often exposes concerns they wouldn't volunteer.)*

---

## Listening vs Waiting to Talk

| Waiting to Talk (Bad) | Active Listening (Good) |
|----------------------|------------------------|
| Planning your next point while they speak | Focused only on their words |
| Interrupting with "Right, yes, and..." | Letting them complete the thought |
| Jumping to solution immediately | Reflecting back: *"So what I heard is..."* |
| Generic follow-up questions | Questions that reference exactly what they said |
| Making notes about your talking points | Making notes about their pain points |

**Practice drill:**  
Record a 10-minute conversation with a friend. Play it back.  
Count how many times you interrupted. Count how many of your questions referenced their previous answer vs. were pre-planned.

---

## Mirroring Technique (FBI Negotiation Method)

Repeat the last 2–3 words of what someone said, as a question. It almost always unlocks more information.

> Customer: *"Our pipeline is really inconsistent."*  
> You: *"Inconsistent?"*  
> Customer: *"Yeah, sometimes it runs in 2 hours, sometimes 8 hours, and we have no idea why."*

Now you have the real problem. The first statement was a summary — the follow-up was the actual pain.

---

## SPIN in Practice — Full Example

**Customer:** *"We have a BigQuery environment but we're not sure we're using it optimally."*

```
S: "Can you tell me what your current BigQuery setup looks like — 
     roughly how many datasets, tables, and users?"
   → "We have about 50 datasets, 200+ tables, 30 analysts."

P: "Where does it feel like it's not working the way you expected?"
   → "Queries are slow for some analysts and we get surprise cost spikes."

I: "When those spikes hit, what happens — is there an alert, a budget freeze?"
   → "Last month we had to suspend a team's access for a week because 
      they burned through $15,000 in 3 days."
   "What did that mean for that team?"
   → "They missed a product launch deadline. It was a big deal."

N: "So if cost surprises like that didn't happen — what would that mean 
     for how your analytics team operates?"
   → "They'd have the confidence to run the analyses they need without 
      worrying about blowing the budget. We'd get faster insights."
```

**Now you're ready to recommend:**  
- `require_partition_filter` on large tables  
- Budget alerts + custom cost allocation  
- BigQuery Editions (Reservations) for predictable cost vs. on-demand  

You didn't propose any of that until you understood the business impact.
