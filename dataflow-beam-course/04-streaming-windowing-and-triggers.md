# Lesson 4 — Streaming, Windowing, and Triggers

> **Official docs:** https://beam.apache.org/documentation/programming-guide/#windowing

---

## Batch vs Streaming — The Mental Model

In **batch processing**, data has a clear beginning and end. You read a file, process every record, write the result. Done.

In **streaming processing**, data is an **infinite sequence** — events keep arriving. You need to answer questions like:
- "How many orders were placed in the last minute?"
- "What was the average sensor temperature in the last 5 minutes?"

To answer these questions over an infinite stream, you must divide the stream into **finite chunks** — this is called **windowing**.

```
Infinite stream of events:
──■──■───■─■──■────■─■──■──■────■─■──■──► (forever)

After windowing into 1-minute buckets:
│ ■ ■ ■ │ ■ ■ ■ ■ │ ■ ■ ■ │ ■ ■ ■ ■ │ ...
│ min 1  │  min 2  │  min 3 │  min 4  │
```

---

## Event Time vs Processing Time

This is one of the most important concepts in streaming — and a common interview question.

| | Event Time | Processing Time |
|--|------------|-----------------|
| **Definition** | When the event actually occurred (timestamp embedded in the data) | When the event arrives at the processing system |
| **Example** | User clicked a button at 14:00:05 | The click event arrived at Dataflow at 14:00:08 |
| **Problem** | Events can arrive late (network delays, mobile devices offline) | Processing time is always "now" |
| **Beam uses** | Event time by default for windowing | Available but less useful for analytics |

```
Event timeline (what ACTUALLY happened):
14:00:00  14:00:01  14:00:02  14:00:03  14:00:04  14:00:05
   ■──────────■────────■──────────────────────────■

Processing timeline (when Dataflow SEES events — delayed/out of order):
14:00:02  14:00:03  14:00:04  14:00:05  14:00:08 (late!)
   ■──────────■────────────────■────────────■
```

**Why it matters:** An event with a 14:00:00 timestamp that arrives at 14:00:45 should be counted in the 14:00 window, not the 14:00 window it arrived in. Without event-time processing, your analytics would be wrong.

---

## The Four Window Types

### 1. Fixed Windows (Tumbling Windows)

Non-overlapping, equal-duration time buckets.

```
│── 1 min ──│── 1 min ──│── 1 min ──│── 1 min ──│
│   window  │   window  │   window  │   window  │
│   [0-60s) │  [60-120s)│[120-180s) │[180-240s) │
```

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows

windowed = (
    events
    | 'Window' >> beam.WindowInto(FixedWindows(60))  # 60-second windows
    | 'Count per window' >> beam.CombineGlobally(beam.combiners.CountCombineFn()).without_defaults()
)
```

**Use case:** "Count orders per hour", "Aggregate metrics per day"

### 2. Sliding Windows

Overlapping windows — each element may belong to multiple windows. Produces **moving averages**.

```
│─────── 2 min ──────│
      │─────── 2 min ──────│
            │─────── 2 min ──────│
```

```python
from apache_beam.transforms.window import SlidingWindows

windowed = (
    events
    | 'Window' >> beam.WindowInto(
        SlidingWindows(
            size=120,    # 2-minute window size
            period=60    # new window starts every 60 seconds
        )
    )
)
```

**Use case:** "30-day rolling average revenue", "CPU utilization over the last 5 minutes"

### 3. Session Windows

Windows are defined by **gaps in activity**, not fixed time periods. A session closes when there's been no activity for a specified gap duration.

```
User A events:  ■──■─────■      │gap > 5min│  ■──■
               [── session 1 ──]            [─ s2 ─]
```

```python
from apache_beam.transforms.window import Sessions

windowed = (
    user_events
    | 'Window' >> beam.WindowInto(Sessions(gap_size=300))  # 5-minute inactivity gap
    | 'Group by user' >> beam.GroupByKey()
)
```

**Use case:** "User session analytics", "How long does a user browse before purchasing?"

### 4. Global Window (Default)

All data goes into a single window — the default for batch processing.

```python
from apache_beam.transforms.window import GlobalWindows

# This is the default; you rarely set it explicitly
windowed = events | beam.WindowInto(GlobalWindows())
```

**Use case:** Batch jobs where you want one final result for all data.

---

## Watermarks — The Key to Late Data

### The Problem

Events arrive **out of order**. A Pub/Sub message sent at 14:00:00 might arrive at Dataflow at 14:00:45 due to network delay or a mobile device coming back online.

When should Dataflow "close" the 14:00 window and emit results? If it waits forever, results are never produced. If it doesn't wait, results are wrong (missing late events).

### The Solution: Watermarks

A **watermark** is the system's estimate of "all events with timestamps before this time have likely arrived." It's a signal that says: "I'm confident the 14:00 window is now complete."

```
Event time timeline:
14:00:00  14:00:30  14:01:00  14:01:30  14:02:00
    ■─────────■─────────■─────────■─────────►

Watermark (Dataflow's guess about completeness):
   🚩 (at 14:00:00, processing time 14:00:45)
      "I'm now confident all events before 14:00:00 have arrived"

When watermark passes 14:01:00:
   → Close the [14:00, 14:01) window
   → Emit results for that window
```

### How Dataflow Determines Watermarks

- For **Pub/Sub**: uses Pub/Sub's built-in message timestamps
- For **custom sources**: your source provides a watermark estimate
- Dataflow tracks the **minimum event timestamp** across all unfinished work

---

## Late Data

Even with watermarks, some events arrive after the window is closed. These are **late data**.

```python
windowed = (
    events
    | 'Window' >> beam.WindowInto(
        FixedWindows(60),
        allowed_lateness=beam.transforms.window.Duration(seconds=300)  # accept up to 5 min late
    )
)
```

With `allowed_lateness`:
- Events up to 5 minutes late will be **included** in their original window
- A corrected (updated) result is emitted for the window
- Events more than 5 minutes late are **dropped**

---

## Triggers — Controlling When Results Are Emitted

By default, Beam emits window results exactly once — when the watermark passes the end of the window. **Triggers** give you control over this.

### Default Trigger (AfterWatermark)
Emit once when the watermark passes the window end.

```python
from apache_beam.transforms import trigger as trigger_module

windowed = events | beam.WindowInto(
    FixedWindows(60),
    trigger=trigger_module.AfterWatermark(),
    accumulation_mode=trigger_module.AccumulationMode.DISCARDING
)
```

### Early Firings (Speculative results)
Emit partial results BEFORE the window closes — for low-latency dashboards:

```python
windowed = events | beam.WindowInto(
    FixedWindows(60),
    trigger=trigger_module.AfterWatermark(
        early=trigger_module.AfterProcessingTime(10)  # fire every 10 seconds of processing time
    ),
    accumulation_mode=trigger_module.AccumulationMode.ACCUMULATING
)
```

### Accumulation Modes

| Mode | Behavior | Use when |
|------|----------|----------|
| `DISCARDING` | Each firing emits only new elements since last firing | You want deltas |
| `ACCUMULATING` | Each firing emits ALL elements seen so far in the window | You want running totals |

---

## Putting It Together — Streaming Pipeline Example

```
Pub/Sub topic (events)
      ↓
ReadFromPubSub
      ↓
Parse JSON
      ↓
WindowInto(FixedWindows(60))  ← bucket by event time, 1-minute windows
      ↓
GroupByKey (user_id)           ← group within each window
      ↓
CombinePerKey(sum)             ← sum per user per window
      ↓
WriteToBigQuery
```

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows
import json

def parse_event(message):
    data = json.loads(message.decode('utf-8'))
    return beam.window.TimestampedValue(
        (data['user_id'], data['amount']),
        data['event_timestamp']  # use event time, not arrival time
    )

with beam.Pipeline(options=pipeline_options) as p:
    (
        p
        | 'Read PubSub' >> beam.io.ReadFromPubSub(topic='projects/proj/topics/orders')
        | 'Parse' >> beam.Map(parse_event)
        | 'Window' >> beam.WindowInto(FixedWindows(60))
        | 'Sum per user' >> beam.CombinePerKey(sum)
        | 'Format' >> beam.Map(lambda kv: {'user_id': kv[0], 'total': kv[1]})
        | 'Write BQ' >> beam.io.WriteToBigQuery(
            'proj:dataset.user_totals_per_minute',
            schema='user_id:STRING, total:FLOAT',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )
    )
```

---

## Streaming vs Batch — Key Differences

| | Batch | Streaming |
|--|-------|-----------|
| **PCollection** | Bounded | Unbounded |
| **Data source** | GCS, BigQuery table | Pub/Sub, Kafka |
| **Processing** | Process all, then write | Continuously process + write |
| **Windows** | Global window (default) | Fixed, sliding, session |
| **Watermarks** | Not needed | Critical for correctness |
| **Latency** | High (run periodically) | Low (seconds to minutes) |
| **Cost model** | Per job cost | Per streaming unit (continuous) |

---

## Practice Q&A

**Q1: What is the difference between event time and processing time?**
<details><summary>Answer</summary>
Event time is when the event actually occurred (embedded in the event data). Processing time is when the event arrives at the processing system. They differ because of network delays, device offline periods, etc. Beam uses event time for windowing to produce correct results.
</details>

**Q2: What is a watermark in Dataflow?**
<details><summary>Answer</summary>
A watermark is the system's estimate that all events with timestamps before a given point have arrived. When the watermark passes the end of a window, Dataflow closes that window and emits results.
</details>

**Q3: What are sliding windows and when do you use them?**
<details><summary>Answer</summary>
Sliding windows overlap — a new window starts every period, and each window spans a larger duration. Each element may belong to multiple windows. Use for rolling/moving averages (e.g., "average revenue over the last 30 days, updated daily").
</details>

**Q4: A customer wants real-time counts from Pub/Sub with partial results every 10 seconds but final results when the window closes. How do you configure this?**
<details><summary>Answer</summary>
Use FixedWindows with an AfterWatermark trigger that has early firings set to AfterProcessingTime(10). Use ACCUMULATING mode so each early firing includes all data seen so far. The window final result fires when the watermark passes the window end.
</details>

**Q5: What is the difference between ACCUMULATING and DISCARDING accumulation modes?**
<details><summary>Answer</summary>
ACCUMULATING: each trigger firing emits all elements seen so far in the window (running total). DISCARDING: each firing emits only the new elements since the last firing (delta). Use ACCUMULATING when you want to replace previous results; DISCARDING when you want to add to them.
</details>
