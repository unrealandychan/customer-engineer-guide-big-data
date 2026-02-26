# Lesson 2 — Core Beam Concepts

> **Official docs:** https://beam.apache.org/documentation/programming-guide/

---

## The Four Core Abstractions

Every Beam pipeline is built from four concepts. Learn these cold — everything else builds on them.

```
┌─────────────────────────────────────────────────────────────────┐
│                         PIPELINE                                │
│                                                                 │
│  PCollection ──> PTransform ──> PCollection ──> PTransform ──> │
│                                                                 │
│  Read(IO) ──────────────────────────────────── Write(IO)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Pipeline

The `Pipeline` object represents your **entire data processing task** — from reading input to writing output. It's also where you set execution options: which runner to use, the project, temp location, etc.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

# Create pipeline with options
options = PipelineOptions([
    '--runner=DataflowRunner',
    '--project=my-project',
    '--region=us-central1',
    '--temp_location=gs://my-bucket/temp/',
])

with beam.Pipeline(options=options) as p:
    # everything inside this block is part of the pipeline
    ...
# pipeline runs (and blocks) when the `with` block exits
```

**Key properties:**
- The pipeline object is a **DAG** (Directed Acyclic Graph) of transforms
- It doesn't execute until `.run()` is called (or the `with` block exits)
- The runner determines WHERE and HOW it executes

---

## 2. PCollection

A `PCollection` is Beam's distributed dataset. Every pipeline reads data INTO a PCollection and writes transforms OUT to a new PCollection.

```python
# Reading creates a PCollection
lines = p | 'Read' >> beam.io.ReadFromText('gs://my-bucket/input.txt')

# lines is a PCollection[str]
# Each element is one line of the file
```

### PCollection Properties

| Property | Detail |
|----------|--------|
| **Distributed** | Data is spread across many worker machines — you never load it all in RAM |
| **Immutable** | You never modify a PCollection; transforms always create a NEW one |
| **No random access** | You can't do `collection[0]`; you can only apply transforms |
| **Bounded vs Unbounded** | Bounded = finite data (file, table); Unbounded = infinite stream (Pub/Sub, Kafka) |
| **Element type** | Each element is an arbitrary Python object — string, dict, custom class |
| **Timestamps** | Each element carries an implicit timestamp (critical for streaming windowing) |

### Bounded vs Unbounded

```
Bounded PCollection (Batch):           Unbounded PCollection (Streaming):
┌───────────────────┐                  ┌──────────────────────────────────
│ ■ ■ ■ ■ ■ ■ ■ ■  │                  │ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ...
│ (finite, complete)│                  │ (infinite, keeps arriving)
└───────────────────┘                  └──────────────────────────────────
  GCS file, BQ table                     Pub/Sub topic, Kafka, Kinesis
```

---

## 3. PTransform

A `PTransform` is a **data processing operation**. It takes one or more PCollections as input and produces one or more new PCollections as output.

```python
# Syntax: pcollection | 'Label' >> TransformName(args)

words = (
    lines
    | 'Split into words' >> beam.FlatMap(lambda line: line.split())
    | 'Lowercase' >> beam.Map(str.lower)
    | 'Filter short' >> beam.Filter(lambda w: len(w) > 3)
)
```

### Rules for Transforms
- **Labels are required** when using the same transform more than once — they must be unique
- Transforms are **lazy** — defining them doesn't execute them; only `.run()` does
- A transform can have **multiple inputs** (merge) or **multiple outputs** (fan-out)

### Pipeline Shapes

**Linear (simple chain):**
```
Read ──> Transform A ──> Transform B ──> Write
```

**Branching (fan-out — one PCollection feeds two transforms):**
```
                 ──> Transform A ──> Write A
Read ──> Parse ─┤
                 ──> Transform B ──> Write B
```

**Merging (multiple sources):**
```
Read A ─┐
        ├──> Flatten ──> Transform ──> Write
Read B ─┘
```

---

## 4. I/O Transforms

Beam includes a library of built-in transforms for reading and writing external systems. These are just PTransforms that interact with I/O.

| System | Read | Write |
|--------|------|-------|
| **Text files (GCS)** | `beam.io.ReadFromText(path)` | `beam.io.WriteToText(path)` |
| **BigQuery** | `beam.io.ReadFromBigQuery(...)` | `beam.io.WriteToBigQuery(...)` |
| **Pub/Sub** | `beam.io.ReadFromPubSub(topic=...)` | `beam.io.WriteToPubSub(topic=...)` |
| **Avro** | `beam.io.ReadFromAvro(path)` | `beam.io.WriteToAvro(path)` |
| **Kafka** | `ReadFromKafka(...)` (in beam.io.kafka) | `WriteToKafka(...)` |

```python
# BigQuery read example
rows = (
    p
    | 'Read BQ' >> beam.io.ReadFromBigQuery(
        query='SELECT user_id, amount FROM `proj.dataset.orders`',
        use_standard_sql=True
    )
)

# BigQuery write example
rows | 'Write BQ' >> beam.io.WriteToBigQuery(
    table='proj:dataset.output_table',
    schema='user_id:STRING, total:FLOAT',
    write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
)
```

---

## How a Pipeline is Executed

When you call `p.run()` (or exit the `with` block):

```
1. Beam SDK validates your pipeline graph (no cycles, types match)
2. Serializes the pipeline definition to a JSON/protocol buffer
3. If DataflowRunner:
      a. Uploads your code + dependencies to GCS staging bucket
      b. Submits job to Dataflow API
      c. Dataflow allocates worker VMs
      d. Workers execute pipeline stages in parallel
      e. Dataflow autoscales, rebalances work
      f. Job completes → workers auto-terminate
4. If DirectRunner:
      Executes everything locally in the current Python process
      (single-threaded, in-memory — for testing only)
```

---

## Labels and the `>>` Operator

In Python, the `|` and `>>` are overloaded operators:

```python
# Full form:
result = p.apply('My Label', MyTransform(args))

# Pythonic Beam syntax (same thing):
result = p | 'My Label' >> MyTransform(args)

# The label is a string — it must be UNIQUE within the pipeline
# Labels appear in the Dataflow monitoring UI as stage names
```

---

## Putting It All Together — First Pipeline

```python
import apache_beam as beam

with beam.Pipeline() as p:  # DirectRunner by default
    (
        p
        | 'Create' >> beam.Create(['Alice 100', 'Bob 200', 'Alice 300', 'Bob 50'])
        | 'Parse' >> beam.Map(lambda line: line.split())
        | 'To KV' >> beam.Map(lambda parts: (parts[0], int(parts[1])))
        | 'Sum by key' >> beam.CombinePerKey(sum)
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]}: {kv[1]}')
        | 'Print' >> beam.Map(print)
    )

# Output:
# Alice: 400
# Bob: 250
```

This single pipeline demonstrates all four concepts:
- `Pipeline` (the `with p:` block)
- `PCollection` (the output of each `|` step)
- `PTransform` (Map, CombinePerKey, etc.)
- I/O (Create at start; in production this would be ReadFromText or ReadFromPubSub)

---

## Practice Q&A

**Q1: What is a PCollection and how is it different from a Python list?**
<details><summary>Answer</summary>
A PCollection is Beam's distributed dataset. Unlike a Python list, it's distributed across many machines, you can't access elements by index, it's immutable (transforms create new ones), and it can be unbounded (infinite stream). A list lives in memory on one machine.
</details>

**Q2: What does "bounded" and "unbounded" mean for a PCollection?**
<details><summary>Answer</summary>
Bounded = finite data set (GCS file, BigQuery table) — batch processing. Unbounded = infinite, data keeps arriving (Pub/Sub, Kafka) — streaming processing.
</details>

**Q3: What is the role of the Pipeline object?**
<details><summary>Answer</summary>
The Pipeline object is the root of your entire data processing graph. It holds all the transforms and connections, carries execution options (runner, project, region), and coordinates execution. It doesn't run until `.run()` is called.
</details>

**Q4: A customer asks: "Do I need to manage worker VMs for Dataflow?" How do you answer?**
<details><summary>Answer</summary>
No. Dataflow is fully managed. When you submit a job, Dataflow automatically allocates worker VMs, scales them during execution, and deletes them when the job is done. You're only billed for the compute used.
</details>

**Q5: What is the difference between DirectRunner and DataflowRunner?**
<details><summary>Answer</summary>
DirectRunner executes the pipeline locally in the current Python process — for development and unit testing, not production. DataflowRunner submits the pipeline to Google Cloud Dataflow, which executes it on a managed fleet of worker VMs at scale.
</details>
