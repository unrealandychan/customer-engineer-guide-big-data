# Interview Day Checklist & Mental Prep

**Read this the night before, and again the morning of each interview.**
**Not a review document — a calibration document.**

---

## The Night Before

### Technical
- [ ] Presentation (Interview D only): open your slides in the meeting you'll share from. Test screen share on Google Meet.
- [ ] Confirm the Google Meet link is in your calendar invite
- [ ] If you have a POC demo: run it end-to-end once. Confirm BigQuery query works. Confirm streaming pipeline can be started.
- [ ] Close all irrelevant browser tabs on your demo machine

### Mental
- [ ] Do NOT study new material the night before. Consolidate; don't expand.
- [ ] Read the "One Thing They All Want to See" line from the master cheatsheet:
  > *"You think before you speak. You use data. You own outcomes. You learn."*
- [ ] Write out (by hand) the 3 things you most want to land in tomorrow's round — 3 bullets only
- [ ] Sleep at a reasonable hour. Being sharp is worth more than the last 90 minutes of review.

---

## Morning Of

### Physical
- [ ] Eat a real meal at least 90 minutes before the interview
- [ ] No caffeine spike — your normal level. You don't want hands shaking during a demo.
- [ ] Dress to feel sharp. Even for video interviews — what you wear affects how you feel.
- [ ] Set your phone to Do Not Disturb for the full interview window + 30 minutes buffer

### Environment (10 min before)
- [ ] Camera at eye level — use a box or laptop stand if needed
- [ ] Lighting is on your face, not behind you
- [ ] Headphones with microphone — test audio
- [ ] Water bottle next to you (not on camera if possible)
- [ ] A blank notepad and pen visible but off camera — you may sketch during hypotheticals

### Mental (15 min before)
Stand up. Say out loud:
> "I think before I speak. I use data. I own outcomes. I learn."

Then say out loud the 3 things you want to land today.

---

## The First 60 Seconds of Each Interview

**What to say when they join:**
> "Hi [Name] — great to meet you. Thanks for making time. I'm ready to go whenever you are."

Short. Warm. Signals you're not stiff or nervous.

**If they ask "How are you doing?" or small-talk:**
Don't go long. 1 sentence. Pivot. Example:
> "Doing well, thanks — I was just reviewing some retail demand forecasting patterns. Ready to jump in."

**If they open with "Tell me about yourself" (likely):**
You have the script in `b-gca/open-ended-scripts.md`. Do not recite it — tell it.
Target: 60–90 seconds. End with a forward hook.

---

## During the Interview — The 5 Rules

### Rule 1: Pause 3 seconds before every answer
This is the most important rule. A 3-second pause signals that you're thinking, not reciting. It also gives you time to activate the correct framework.

When asked a question:
- Nod. (Buys 1 second.)
- Say "Good question — let me think for a moment." (Buys 3 seconds and signals confidence.)
- Then answer.

### Rule 2: Name the structure before you use it
Before answering ANY hypothetical or complex behavioral:
> "I'd like to structure this as [behavioral/hypothetical frame]. Let me start with..."

This signals structured thinking before you've demonstrated it.

### Rule 3: One number in every behavioral result
Every STAR story must end with a specific number. If you don't have an exact number:
> "We didn't have a precise measurement at the time, but my estimate was approximately $X / N hours / Y percent..."

An approximate number you explain is infinitely better than no number.

### Rule 4: Close every hypothetical with a success metric
Before moving to the next question, end with:
> "I'd measure success on this by [KPI/measurement]. Is there a specific constraint you'd like me to optimize for?"

This closes the loop and invites a follow-up that you control.

### Rule 5: Incorporate pushback, never defend
If the interviewer challenges your architecture or story:
> "That's a really good point — if [their alternative] then [how I'd adjust]. The trade-off would be [X]..."

Never say "Actually, what I meant was..." — that sounds defensive. Incorporate the pushback as new information.

---

## Managing Silence and Uncertainty

**If you don't know something:**
> "I'm not certain of the exact [detail/number/product spec] — my best estimate is [X] based on [Y]. Happy to follow up with a more precise answer."

This is infinitely better than winging it and being wrong.

**If you're mid-answer and lose your thread:**
> "Let me step back for a moment — I want to make sure I'm addressing the right layer of this question."

Then re-anchor to the structure (STAR / Clarify-Decompose-Conclude).

**If they ask a question you haven't prepared for:**
Step 1: Clarify: "Before I answer — can I make sure I understand what you're looking for?"
Step 2: Think out loud: "Let me work through this..."
Step 3: Use the closest framework you have and tell them you're adapting: "This is adjacent to [X scenario] I know well — let me apply the same reasoning..."

---

## Round-Specific Calibrations

### Before Interview B (GCA — Gene)
- Gene is a sales leader. Land a business impact number in every answer.
- His probes will be data-specific: "What data did you use? What metric defined success?"
- Lead with the outcome first, then the approach. "We reduced reporting latency from 7 days to same-day — here's how."

### Before Interview C (G&L — Andy)
- Andy is a CE manager. He'll see through anything that doesn't ring true.
- Every story needs a real person's reaction. "Here's how my engineer reacted when I told them I was wrong."
- The "Values Protected" line matters. Before you answer any ethical question, identify what value you protected, then build the story to that point.
- Intellectual humility is NOT weakness at Google. Saying "I was wrong" clearly is a STRENGTH.

### Before Interview D (Presentation — William)
- William is your potential hiring manager. He's imagining working with you every day.
- The Q&A is where you're evaluated — treat every question as an opportunity to go one layer deeper than they expect.
- When he pushes back, don't defend the slide — adapt. Say "fair point — let me reconsider that trade-off."
- Look at the camera, not the screen, when you're making a key point. It reads as confidence.
- During the demo: narrate your THINKING, not just your clicks. "I'm running this BigQuery continuous query because... what I expect to see is... and here's what it tells us about the customer."

---

## End of Interview

### When they say "any questions for me?"

Prepare 2–3 real questions per round. Never say "No, I think we covered it all."

**For Gene (GCA):**
1. "What's the most common technical blocker you see when sales teams are trying to close enterprise data analytics deals?"
2. "What does a great first 90 days look like for a specialist CE on your deals — what are you hoping they change?"

**For Andy (G&L):**
1. "How does the specialist CE model interact with your platform CE team day-to-day — what's worked well and what creates friction?"
2. "What's one thing your best CEs do that your newer CEs take a year or two to learn?"

**For William (Presentation):**
1. "The CIO's board mandate is unusual — most customers we see want a 3-year roadmap, not 12 months. What does the customer landscape actually look like right now in terms of urgency?"
2. "What would I need to accomplish in my first year in this role for you to say it was a clear success?"
3. "What's the one type of problem this team is currently under-resourced to handle — where a specialist CE most fills a gap?"

### The Close

After the final question-answer exchange:
> "Thank you — this was a really good conversation. I'm genuinely excited about this role. I'd be happy to send any follow-up materials if that would be useful."

Short. No over-explaining. Let them end it.

---

## Post-Interview (Within 1 Hour)

1. Write down every question you were asked — before you forget
2. Note which answers landed well (you felt momentum) and which fell flat
3. Update `prep/missed-questions/` if anything new surfaced
4. Send a brief follow-up email to the recruiter (see template below)

### Follow-Up Email Template

**Subject:** Interview follow-up — [Your Name] — [Role Name]

> Hi [Recruiter name],
>
> I wanted to follow up after today's [Interview B / C / D] with [Gene / Andy / William]. The conversation was excellent — [one specific thing that was particularly interesting to you, e.g., "the discussion about streaming vs batch trade-offs for the retail scenario gave me a new angle I hadn't fully considered"].
>
> I remain very excited about this opportunity and appreciate the team's time.
>
> Happy to provide any additional materials or follow-up if that's helpful as the process continues.
>
> Best,
> Eddie

**Note:** Do NOT send this directly to Gene, Andy, or William — send it to your recruiter only. They control the communication flow.
