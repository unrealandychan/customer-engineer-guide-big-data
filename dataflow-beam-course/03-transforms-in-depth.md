# Lesson 3 — Transforms In Depth

> **Official docs:** https://beam.apache.org/documentation/programming-guide/#transforms

---

## The Six Core Transforms

Beam provides six fundamental transforms. Every complex pipeline is built from combinations of these.

| Transform | What it does |
|-----------|-------------|
| `ParDo` | Apply a function to each element (parallel do) |
| `GroupByKey` | Group a key-value PCollection by key |
| `CoGroupByKey` | Join two or more key-value PCollections |
| `Combine` | Aggregate values (sum, count, custom) |
| `Flatten` | Merge multiple PCollections into one |
| `Partition` | Split one PCollection into multiple outputs |

---

## 1. ParDo and DoFn

`ParDo` is the most general and powerful transform — it's Beam's parallel `for` loop. It applies a user-defined function to each element of the input PCollection.

The function is a **DoFn** (Do Function) — a class with a `process()` method.

```python
import apache_beam as beam

class ParseOrderFn(beam.DoFn):
    def process(self, element):
        # element is one item from the PCollection (e.g., a CSV line)
        parts = element.split(',')
        yield {
            'order_id': parts[0].strip(),
            'user_id': parts[1].strip(),
            'amount': float(parts[2].strip()),
        }

with beam.Pipeline() as p:
    orders = (
        p
        | 'Read' >> beam.io.ReadFromText('gs://bucket/orders.csv')
        | 'Parse' >> beam.ParDo(ParseOrderFn())
    )
```

### Why `yield` not `return`?
- `process()` uses `yield` because it can emit **zero, one, or many elements** per input
- This makes ParDo work as a filter (yield nothing), mapper (yield one), or exploder (yield many)

```python
class FilterAndExplodeFn(beam.DoFn):
    def process(self, element):
        # Filter: skip elements that don't match
        if element['amount'] <= 0:
            return  # yield nothing — element is dropped

        # Explode: emit multiple outputs for one input
        for tag in element.get('tags', []):
            yield (tag, element['amount'])
```

### DoFn Requirements
- **Serializable:** DoFn instances are serialized and sent to worker VMs — avoid storing non-serializable state in `__init__`
- **Thread-compatible:** Workers may call `process()` from multiple threads
- **Idempotent (recommended):** If the system retries an element, running it twice should have the same result

### Map and FlatMap Shortcuts (lambdas)

For simple one-to-one or one-to-many operations, use the shortcuts:

```python
# beam.Map: one input → one output (like ParDo that always yields one)
amounts = records | 'Get amount' >> beam.Map(lambda r: r['amount'])

# beam.FlatMap: one input → zero or many outputs
words = lines | 'Split' >> beam.FlatMap(lambda line: line.split())

# beam.Filter: keeps only elements where function returns True
big_orders = orders | 'Big only' >> beam.Filter(lambda r: r['amount'] > 1000)
```

### Side Inputs

A `DoFn` can receive additional data (not from the main PCollection) via **side inputs** — useful for lookup tables or config values:

```python
# side input: a dict loaded from BigQuery
user_region_dict = p | 'Load users' >> beam.io.ReadFromBigQuery(...) | beam.combiners.ToDict()

class EnrichFn(beam.DoFn):
    def process(self, element, user_map):
        region = user_map.get(element['user_id'], 'unknown')
        yield {**element, 'region': region}

enriched = orders | 'Enrich' >> beam.ParDo(EnrichFn(), user_map=beam.pvalue.AsSingleton(user_region_dict))
```

---

## 2. GroupByKey

`GroupByKey` groups a key-value PCollection by key — all values with the same key are collected into a list.

```
Input PCollection (KV pairs):         Output PCollection:
('cat', 1)                            ('cat', [1, 1, 2])
('dog', 5)          ──────────>       ('dog', [5])
('cat', 1)                            ('fish', [3])
('fish', 3)
('cat', 2)
```

```python
# Create key-value pairs first
kv = orders | 'Key by user' >> beam.Map(lambda r: (r['user_id'], r['amount']))

# Group all amounts per user
grouped = kv | 'Group' >> beam.GroupByKey()

# grouped PCollection: (user_id, [amount1, amount2, ...])
totals = grouped | 'Sum' >> beam.Map(lambda kv: (kv[0], sum(kv[1])))
```

> **Performance note:** `GroupByKey` triggers a shuffle — data is re-partitioned across workers by key. This is the most expensive operation in batch; design to minimize it.

---

## 3. CoGroupByKey

`CoGroupByKey` joins two or more key-value PCollections — like a SQL JOIN.

```python
# Two PCollections with the same key type
orders_kv = orders | 'Order KV' >> beam.Map(lambda r: (r['user_id'], r))
users_kv = users | 'User KV' >> beam.Map(lambda r: (r['user_id'], r))

# CoGroupByKey joins them
joined = {'orders': orders_kv, 'users': users_kv} | beam.CoGroupByKey()

# joined PCollection: (user_id, {'orders': [...], 'users': [...]})
def enrich(element):
    user_id, data = element
    user_list = data['users']
    if not user_list:
        return
    user = user_list[0]
    for order in data['orders']:
        yield {**order, 'email': user['email'], 'region': user['region']}

enriched = joined | 'Enrich' >> beam.FlatMap(enrich)
```

---

## 4. Combine

`Combine` aggregates values — sum, count, average, or custom combinations. Unlike `GroupByKey` → `Map(sum)`, Combine uses **combiner lifting** for efficiency.

```python
# Global combine (single value output)
total = amounts | 'Total' >> beam.CombineGlobally(sum)

# Per-key combine
totals = kv_amounts | 'Sum per user' >> beam.CombinePerKey(sum)

# Built-in combiners
from apache_beam import combiners

count = amounts | 'Count' >> beam.CombineGlobally(combiners.CountCombineFn())
mean = amounts | 'Mean' >> beam.CombineGlobally(combiners.MeanCombineFn())
top3 = amounts | 'Top 3' >> beam.CombineGlobally(combiners.TopCombineFn(3))
```

### Custom CombineFn

For complex aggregations, subclass `CombineFn`:

```python
class MaxAndCountFn(beam.CombineFn):
    def create_accumulator(self):
        return (float('-inf'), 0)  # (max, count)

    def add_input(self, accumulator, element):
        current_max, count = accumulator
        return (max(current_max, element), count + 1)

    def merge_accumulators(self, accumulators):
        maxes, counts = zip(*accumulators)
        return (max(maxes), sum(counts))

    def extract_output(self, accumulator):
        return {'max': accumulator[0], 'count': accumulator[1]}

result = amounts | 'MaxAndCount' >> beam.CombineGlobally(MaxAndCountFn())
```

### Combiner Lifting (Why Combine > GroupByKey + Map)

```
WITHOUT lifting (GroupByKey + Map):
Worker 1: sends ALL values to GroupByKey shuffle → network bottleneck

WITH combiner lifting:
Worker 1: pre-aggregates locally → (sub-total: 500, count: 200)
Worker 2: pre-aggregates locally → (sub-total: 300, count: 150)
         ↓
Shuffle now sends 2 small accumulators instead of 350 raw values
         ↓
Final merge: (800, 350)  → much faster!
```

Combiner functions must be **commutative and associative** so pre-aggregation order doesn't matter.

---

## 5. Flatten

`Flatten` merges multiple PCollections of the same type into one:

```python
# Two separate data sources
orders_2023 = p | 'Read 2023' >> beam.io.ReadFromText('gs://bucket/2023.csv')
orders_2024 = p | 'Read 2024' >> beam.io.ReadFromText('gs://bucket/2024.csv')

# Merge into one PCollection
all_orders = (orders_2023, orders_2024) | 'Merge' >> beam.Flatten()

# Now process uniformly
totals = all_orders | 'Parse' >> beam.ParDo(ParseOrderFn())
```

---

## 6. Partition

`Partition` splits one PCollection into multiple based on a partition function:

```python
def partition_by_tier(record, num_partitions):
    if record['amount'] > 10000:
        return 0  # partition 0 = high value
    elif record['amount'] > 1000:
        return 1  # partition 1 = medium value
    else:
        return 2  # partition 2 = low value

high, medium, low = (
    orders
    | 'Partition' >> beam.Partition(partition_by_tier, 3)
)

# Write each tier to a different sink
high   | 'Write high'   >> beam.io.WriteToBigQuery('proj:ds.high_value')
medium | 'Write medium' >> beam.io.WriteToBigQuery('proj:ds.medium_value')
low    | 'Write low'    >> beam.io.WriteToBigQuery('proj:ds.low_value')
```

---

## Composite Transforms

Composite transforms bundle multiple transforms into a reusable unit — like a function or class. This is the Beam equivalent of writing a reusable module.

```python
class ParseAndEnrichOrders(beam.PTransform):
    def __init__(self, user_data):
        self.user_data = user_data

    def expand(self, pcoll):
        return (
            pcoll
            | 'Parse CSV' >> beam.ParDo(ParseOrderFn())
            | 'Filter valid' >> beam.Filter(lambda r: r['amount'] > 0)
            | 'Enrich' >> beam.ParDo(EnrichFn(), users=beam.pvalue.AsSingleton(self.user_data))
        )

# Use it like any built-in transform
enriched_orders = raw_lines | 'Process orders' >> ParseAndEnrichOrders(user_pdata)
```

---

## Transform Decision Guide

```
Need to process each element independently?
  └─> ParDo / Map / FlatMap / Filter

Need to aggregate by key?
  └─> CombinePerKey (sum, count, mean)
  └─> GroupByKey (if you need ALL values for custom logic)

Need to join two datasets?
  └─> CoGroupByKey

Need to merge multiple data sources?
  └─> Flatten

Need to route elements to different outputs?
  └─> Partition

Need to aggregate globally?
  └─> CombineGlobally
```

---

## Practice Q&A

**Q1: What is the difference between ParDo and Map?**
<details><summary>Answer</summary>
Both apply a function to each element. `beam.Map` is a shortcut for ParDo where the function always emits exactly one output. ParDo (via DoFn) can emit zero, one, or many outputs per input. Use Map for simple transformations, ParDo for filtering, splitting, or complex logic.
</details>

**Q2: Why is CombinePerKey better than GroupByKey followed by a Map(sum)?**
<details><summary>Answer</summary>
CombinePerKey uses combiner lifting — it pre-aggregates values locally on each worker before the shuffle. This reduces the amount of data transferred across the network. GroupByKey must send ALL raw values across the network before aggregation.
</details>

**Q3: What are the requirements for a CombineFn?**
<details><summary>Answer</summary>
The combining function must be commutative and associative, so that partial results can be merged in any order. This allows pre-aggregation (combiner lifting) to work correctly.
</details>

**Q4: When would you use CoGroupByKey vs a simple join in BigQuery?**
<details><summary>Answer</summary>
CoGroupByKey is used when you need to join data in a streaming pipeline (where BigQuery joins aren't available) or when one dataset is too large to use as a side input. For batch jobs where both datasets can go to BigQuery, a SQL join in BigQuery is usually simpler.
</details>

**Q5: What is a Composite Transform and why create one?**
<details><summary>Answer</summary>
A Composite Transform bundles multiple transforms into a reusable PTransform subclass. You create them for reusability (use the same logic in multiple pipelines), readability (give a name to a group of transforms), and testability (test the composite independently).
</details>
