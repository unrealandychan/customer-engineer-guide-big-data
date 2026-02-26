# 🖊️ Whiteboard Facilitation — Running Sessions Under Pressure

> **The person holding the marker controls the conversation.**  
> Your goal: take the pen early, keep the narrative moving, and make everyone feel heard — even when the session goes sideways.

---

## Why Whiteboard Sessions Fail

1. No one takes ownership → everyone talks at once → nothing gets drawn
2. A dominant engineer hijacks the session with a "better" design
3. The consultant loses the thread when interrupted
4. The diagram becomes a mess that no one understands
5. You run out of time before reaching a conclusion
6. The customer's concerns are never visually acknowledged

---

## Taking Control of the Pen

**Do this at the start of every session:**

> *"Would it be okay if I drive on the whiteboard? I find it helps keep things organized — and please jump in anytime to correct me."*

This does three things:
1. Establishes you as the session leader without being combative
2. Gives them permission to challenge (which they'll do anyway, but now it's invited)
3. Sets the expectation that the diagram is collaborative, not your personal pitch

**If someone else grabs the marker first:**
> *"Great — I love it. [Let them draw for 60 seconds.] Can I add the data flow on top of that? I want to make sure we capture the integration layer."*

Take the pen naturally mid-drawing. Never fight for it.

---

## The 5-Zone Whiteboard Layout

Reserve sections of the board before you start drawing. This keeps the session from becoming chaos.

```
┌─────────────────────────────────────────────────────┐
│  CURRENT STATE (left)     │  FUTURE STATE (right)   │
│                            │                         │
│  [Draw their world first] │  [Your proposed arch]   │
│                            │                         │
├────────────────────────────┴─────────────────────────┤
│  OPEN QUESTIONS (bottom strip — add throughout)      │
└──────────────────────────────────────────────────────┘
```

**Why this layout works:**
- Starting with their current state shows you're listening, not pitching
- Open questions prevents tangents from derailing the main flow — park them visually
- Side-by-side comparison makes the value obvious without you having to say it

---

## The Opening 3 Minutes (Script)

> *"Before I draw anything, let me make sure I understand your current setup correctly. Can I sketch what you told me in our earlier conversation, and you tell me where I have it wrong?"*

*[Draw a rough current state — intentionally imperfect]*

> *"Is this roughly right? Where would you correct it?"*

This is the fastest trust-builder in a whiteboard session. You're drawing their world, not yours. They will correct you — and that correction is exactly the information you need.

---

## Handling Interruptions

### Type 1: The Tangent

*Customer mid-session: "Actually, before we go further — can you explain how your pricing works for storage vs. compute?"*

**Don't stop drawing. Park it.**

> *"Great question — let me put that on our parking lot [write it in the Open Questions zone], and I'll make sure we get to it before the end. I want to finish this thread first so we don't lose context."*

Then **return to the main thread immediately** — don't let the parking lot item derail you.

### Type 2: The Technical Challenge

*Engineer: "That design won't work. You can't do cross-region queries in real time."*

**Stop drawing. Give full attention.**

> *"Tell me more — what's the constraint you're seeing?"*

*Listen carefully. Two possibilities:*

**If they're right:**
> *"You're correct — let me adjust. [Erase and redraw.] What you're describing is actually a good point for why we'd separate the real-time path from the analytics path. Here's how..."*

Admitting they're right in front of the room builds enormous credibility.

**If they're partially right:**
> *"I hear the concern — and to your point about latency, you're right that true real-time cross-region has limits. What I'd suggest here is [explain]. Does that address the constraint?"*

**If you don't know:**
> *"That's a specific technical detail I want to get right rather than guess. Can I note it here [write on board] and come back with a confirmed answer today? I don't want to design the architecture around something I'm not certain of."*

### Type 3: The Dominant Engineer

They're drawing on the board, talking over you, rewriting your diagram.

**Let them for 90 seconds.** Then:

> *"I love where you're going with this — [genuine]. Can I build on that? [Take the pen.] What if we extended your design to include the streaming layer here..."*

You're not fighting. You're elevating their idea and steering it.

---

## The "Anchor and Bridge" Technique

When the session goes completely off-topic:

**Anchor:** Reference the last agreed-upon point on the whiteboard.  
**Bridge:** Connect it to where you need to go.

> *"Let's anchor back to what we agreed on here [point to diagram] — the data lands in GCS. From there, the question we were exploring was how to get it into BigQuery. Let me finish that thread and then we can take the pricing question..."*

The physical whiteboard is your anchor. Always point to something on the board when redirecting.

---

## When You're Asked Something You Don't Know

**Never guess.** Never say "I think" when you mean "I don't know."

The 3-part response:

> *"That's exactly the kind of specific detail where I want to give you an accurate answer rather than an approximate one. Let me [1] note it here [write on board], [2] confirm with engineering by end of day, and [3] make sure the answer is reflected in the architecture doc we send you after this session."*

**Why this works:**
- It shows intellectual honesty (builds trust)
- It gives a concrete next step (not just "I'll check")
- The follow-up becomes an excuse to re-engage

---

## Time Management During the Session

### 60-Minute Session Pacing

```
00:00 – 10:00  Current state (their world) — draw, listen, correct
10:00 – 25:00  Pain points and requirements — write them on the board
25:00 – 45:00  Proposed architecture — draw incrementally, explain each layer
45:00 – 55:00  Q&A, objections, refinement
55:00 – 60:00  Summary + next steps (ALWAYS end here)
```

**The 10-minute warning:**
> *"We have about 10 minutes left. Let me make sure we cover the most important parts. What's the one thing you want to make sure we address before we close?"*

This does two things: manages time AND surfaces their top concern.

### If You're Running Out of Time

> *"I want to respect your time — we have 5 minutes. Let me give you the bottom line: [30-second summary]. We have 3 open items on the board. Would you prefer to schedule a 20-minute follow-up, or should I send you a doc that addresses them?"*

Don't rush through the remaining material. Cut gracefully.

---

## Drawing Under Pressure — Architecture Shortcuts

You don't need to be an artist. Use boxes, lines, and labels consistently.

```
Standard symbols to practice:
[ ] = Storage (GCS, BigQuery table)
( ) = Processing (Dataflow, Spark job)
{ } = External system or user
→  = Data flow direction
⇌  = Bidirectional
// = Queue / message bus (Pub/Sub)
△  = Alert / monitoring
```

**The "Rough Draft" Frame:**
> *"I'm going to draw a rough sketch here — we can refine it. The goal is to get the main components on the board, not a perfect diagram."*

This lowers the stakes for you AND for them to add/correct things.

---

## Closing a Whiteboard Session

**Never walk out of a session without these three things:**

1. **Photo of the whiteboard** — take it yourself, in front of them.
   > *"Before we wrap, let me grab a photo of the board — I'll include this in the follow-up notes."*

2. **Named action items** — with owners and dates.
   > *"From today's session: [you] will send the architecture doc by [date], [them] will share their data volume numbers by [date]. Does that capture it?"*

3. **Clear next step** — not "let's stay in touch."
   > *"Let's schedule a 30-minute technical deep dive on [specific topic] — can we do [date]?"*

---

## Practice Drills

### Drill 1: 5-minute Architecture Sketch
Set a timer for 5 minutes. Draw a complete GCP data pipeline on paper using only boxes, lines, and labels. Include: ingestion → processing → storage → analytics → alerting.

### Drill 2: Interrupted Whiteboard
Have a partner throw interruptions at you every 60 seconds while you draw. Practice parking and anchoring without losing your place.

### Drill 3: "Correct My Diagram"
Draw an intentionally wrong architecture. Present it to a partner and ask them to correct it. Practice taking corrections gracefully and incorporating them smoothly.

### Drill 4: Unknown Question
Have a partner ask you a technical question you genuinely can't answer. Practice the "note + confirm + follow-up" response without visible discomfort.
