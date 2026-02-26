# Lesson 5 — Writing Pipelines in Python

> **Official docs:**
> - https://beam.apache.org/documentation/sdks/python/
> - https://beam.apache.org/documentation/runners/dataflow/

---

## Setup

```bash
# Install the Apache Beam SDK with all GCP extras
pip install apache-beam[gcp]

# This includes:
# - apache-beam (core)
# - google-cloud-bigquery
# - google-cloud-storage
# - google-cloud-pubsub
# - google-cloud-dataflow
```

Verify installation:

```python
import apache_beam as beam
print(beam.__version__)
```

---

## Pipeline Options

Options control WHERE and HOW your pipeline runs. They can be set in code or passed as command-line arguments.

```python
from apache_beam.options.pipeline_options import (
    PipelineOptions,
    StandardOptions,
    GoogleCloudOptions,
    WorkerOptions,
    SetupOptions,
)

# --- Code-based options ---
options = PipelineOptions()

google_cloud_options = options.view_as(GoogleCloudOptions)
google_cloud_options.project = 'my-project'
google_cloud_options.region = 'us-central1'
google_cloud_options.job_name = 'my-pipeline-job'
google_cloud_options.staging_location = 'gs://my-bucket/staging'
google_cloud_options.temp_location = 'gs://my-bucket/temp'

options.view_as(StandardOptions).runner = 'DataflowRunner'
options.view_as(WorkerOptions).machine_type = 'n1-standard-4'
options.view_as(WorkerOptions).max_num_workers = 20

# Save main session so lambdas and globals are serialized correctly
options.view_as(SetupOptions).save_main_session = True
```

```bash
# --- Command-line args (same options as flags) ---
python my_pipeline.py \
  --runner=DataflowRunner \
  --project=my-project \
  --region=us-central1 \
  --staging_location=gs://my-bucket/staging \
  --temp_location=gs://my-bucket/temp \
  --job_name=my-pipeline-job \
  --max_num_workers=20
```

---

## Example 1 — Batch ETL: GCS Text → Transform → BigQuery

The classic batch pipeline: read a CSV from GCS, transform it, write to BigQuery.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import csv
import io

# --- Pipeline code ---
def parse_csv_line(line):
    """Parse a CSV line into a dict."""
    reader = csv.reader(io.StringIO(line))
    for row in reader:
        if len(row) == 3:
            return {
                'order_id': row[0].strip(),
                'user_id': row[1].strip(),
                'amount': float(row[2].strip()),
            }

def is_valid(record):
    """Filter: only keep valid records."""
    return record is not None and record['amount'] > 0

def run():
    options = PipelineOptions([
        '--runner=DataflowRunner',
        '--project=my-project',
        '--region=us-central1',
        '--temp_location=gs://my-bucket/temp',
    ])

    bq_schema = {
        'fields': [
            {'name': 'order_id', 'type': 'STRING'},
            {'name': 'user_id', 'type': 'STRING'},
            {'name': 'amount', 'type': 'FLOAT'},
        ]
    }

    with beam.Pipeline(options=options) as p:
        (
            p
            | 'Read CSV' >> beam.io.ReadFromText(
                'gs://my-bucket/data/orders-*.csv',
                skip_header_lines=1
            )
            | 'Parse' >> beam.Map(parse_csv_line)
            | 'Filter valid' >> beam.Filter(is_valid)
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
                table='my-project:my_dataset.orders',
                schema=bq_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

if __name__ == '__main__':
    run()
```

---

## Example 2 — Batch with Aggregation: WordCount (the "Hello World" of Beam)

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

def run(argv=None):
    pipeline_options = PipelineOptions(argv)

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'Read' >> beam.io.ReadFromText('gs://dataflow-samples/shakespeare/kinglear.txt')
            | 'Split words' >> beam.FlatMap(lambda line: line.lower().split())
            | 'Filter empty' >> beam.Filter(lambda w: len(w) > 0)
            | 'Pair with 1' >> beam.Map(lambda w: (w, 1))
            | 'Count per word' >> beam.CombinePerKey(sum)
            | 'Format' >> beam.Map(lambda kv: f'{kv[0]}: {kv[1]}')
            | 'Write' >> beam.io.WriteToText('gs://my-bucket/output/word-counts')
        )

if __name__ == '__main__':
    run()
```

---

## Example 3 — Streaming: Pub/Sub → Window → Aggregate → BigQuery

A streaming pipeline that reads from Pub/Sub, windows events by minute, and writes per-minute totals to BigQuery.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.transforms.window import FixedWindows
import json

def parse_message(message):
    """Parse Pub/Sub message bytes into a (user_id, amount) tuple."""
    data = json.loads(message.decode('utf-8'))
    # Attach event timestamp so Beam uses it for windowing
    return beam.window.TimestampedValue(
        (data['user_id'], data['amount']),
        data['event_timestamp']
    )

def format_result(kv):
    """Format (user_id, total) into a BigQuery row dict."""
    return {'user_id': kv[0], 'total': kv[1]}

def run():
    options = PipelineOptions([
        '--runner=DataflowRunner',
        '--project=my-project',
        '--region=us-central1',
        '--temp_location=gs://my-bucket/temp',
        '--streaming',  # required flag for streaming jobs
    ])
    options.view_as(StandardOptions).streaming = True

    bq_schema = 'user_id:STRING, total:FLOAT'

    with beam.Pipeline(options=options) as p:
        (
            p
            | 'Read PubSub' >> beam.io.ReadFromPubSub(
                topic='projects/my-project/topics/orders'
            )
            | 'Parse' >> beam.Map(parse_message)
            | 'Window 1 min' >> beam.WindowInto(FixedWindows(60))
            | 'Sum per user' >> beam.CombinePerKey(sum)
            | 'Format row' >> beam.Map(format_result)
            | 'Write BQ' >> beam.io.WriteToBigQuery(
                table='my-project:my_dataset.user_totals_per_min',
                schema=bq_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

if __name__ == '__main__':
    run()
```

---

## DirectRunner vs DataflowRunner

| | DirectRunner | DataflowRunner |
|--|-------------|----------------|
| **Use for** | Local development and unit tests | Production |
| **Runs on** | Your local machine | GCP-managed worker VMs |
| **Scale** | Limited by local RAM/CPU | Scales to thousands of workers |
| **Cost** | Free (uses local compute) | Billed per vCPU-hour |
| **How to invoke** | Default (no flag needed) | `--runner=DataflowRunner` |
| **Artifacts** | None | Uploads code to GCS staging bucket |

```python
# Development (DirectRunner — default)
with beam.Pipeline() as p:
    ...

# Production (DataflowRunner)
options = PipelineOptions(['--runner=DataflowRunner', ...])
with beam.Pipeline(options=options) as p:
    ...
```

---

## Packaging and Dependency Management

When running on Dataflow, your code and all its dependencies must be available on worker VMs.

### Option 1: requirements.txt (simple)

```bash
# requirements.txt
apache-beam[gcp]==2.55.0
pandas==2.0.0
scikit-learn==1.3.0
```

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --requirements_file=requirements.txt
```

### Option 2: Setup.py (for local modules)

When your pipeline imports local Python modules:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='my-pipeline',
    packages=find_packages(),
)
```

```bash
python my_pipeline.py \
  --runner=DataflowRunner \
  --setup_file=./setup.py
```

---

## Dataflow Templates

Templates let you run pre-built pipelines without writing code.

### Classic Templates (JAR/Python scripts compiled once)

```bash
# Google-provided template: GCS text to BigQuery
gcloud dataflow jobs run my-batch-job \
  --gcs-location gs://dataflow-templates/latest/GCS_Text_to_BigQuery \
  --region us-central1 \
  --parameters \
javascriptTextTransformFunctionName=transform,\
JSONPath=gs://my-bucket/schema.json,\
javascriptTextTransformGcsPath=gs://my-bucket/transform.js,\
inputFilePattern=gs://my-bucket/input/*.csv,\
outputTable=my-project:dataset.table,\
bigQueryLoadingTemporaryDirectory=gs://my-bucket/temp/
```

### Flex Templates (containerized — recommended)

Flex Templates package your pipeline in a Docker container, enabling dynamic parameters and private dependencies.

```bash
# Build and upload a Flex Template
gcloud dataflow flex-template build \
  gs://my-bucket/templates/my-pipeline.json \
  --image-gcr-path gcr.io/my-project/my-pipeline:latest \
  --sdk-language PYTHON \
  --flex-template-base-image PYTHON3 \
  --py-path my_pipeline.py \
  --metadata-file metadata.json

# Run a Flex Template
gcloud dataflow flex-template run my-job \
  --template-file-gcs-location gs://my-bucket/templates/my-pipeline.json \
  --region us-central1 \
  --parameters inputTopic=projects/my-project/topics/orders
```

---

## Testing Pipelines

### Unit test with DirectRunner

```python
import unittest
import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

class MyTransformTest(unittest.TestCase):
    def test_parse_csv_line(self):
        with TestPipeline() as p:
            input_data = ['order1,user1,100.0', 'order2,user2,200.0']
            expected = [
                {'order_id': 'order1', 'user_id': 'user1', 'amount': 100.0},
                {'order_id': 'order2', 'user_id': 'user2', 'amount': 200.0},
            ]
            result = (
                p
                | beam.Create(input_data)
                | beam.Map(parse_csv_line)
            )
            assert_that(result, equal_to(expected))

if __name__ == '__main__':
    unittest.main()
```

---

## Common Patterns Quick Reference

```python
# Read CSV from GCS
lines = p | beam.io.ReadFromText('gs://bucket/file.csv', skip_header_lines=1)

# Read from BigQuery SQL
rows = p | beam.io.ReadFromBigQuery(query='SELECT ...', use_standard_sql=True)

# Read from Pub/Sub (streaming)
messages = p | beam.io.ReadFromPubSub(topic='projects/proj/topics/topic')

# Write to BigQuery (append)
rows | beam.io.WriteToBigQuery(
    'proj:dataset.table',
    schema='col1:TYPE, col2:TYPE',
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
)

# Write to GCS text
results | beam.io.WriteToText('gs://bucket/output/prefix', file_name_suffix='.txt')

# Create test data
test_data = p | beam.Create([1, 2, 3, 4, 5])

# Simple aggregations
count = col | beam.combiners.Count.Globally()
mean = col | beam.combiners.Mean.Globally()
top_n = col | beam.combiners.Top.Largest(10)
```

---

## Practice Q&A

**Q1: What is `save_main_session = True` and when do you need it?**
<details><summary>Answer</summary>
When running on Dataflow, worker VMs need access to your pipeline code. `save_main_session` serializes the global namespace (functions defined at module level, lambdas, global imports) and ships them to workers. You need it when your DoFn or Map functions reference globals defined outside their class.
</details>

**Q2: How do you run a Beam pipeline locally for testing?**
<details><summary>Answer</summary>
By default (with no runner specified), Beam uses DirectRunner, which executes the pipeline locally in the current Python process. Use `TestPipeline` from `apache_beam.testing.test_pipeline` in unit tests, and `assert_that` with `equal_to` to validate outputs.
</details>

**Q3: What is the difference between Classic and Flex Templates?**
<details><summary>Answer</summary>
Classic Templates are compiled snapshots of a pipeline (JSON + staged artifacts). Flex Templates package the pipeline in a Docker container, allowing more flexible parameter handling, private dependencies, and support for streaming pipelines with dynamic parameters. Flex Templates are the recommended approach.
</details>

**Q4: A streaming pipeline needs to read from Pub/Sub. What option must you set?**
<details><summary>Answer</summary>
`--streaming` flag (or `options.view_as(StandardOptions).streaming = True`). Without this flag, Dataflow treats the job as batch and will error when reading from an unbounded source like Pub/Sub.
</details>

**Q5: How do you handle dependencies (e.g., pandas) in a Dataflow pipeline?**
<details><summary>Answer</summary>
Provide a `requirements.txt` file with `--requirements_file=requirements.txt`. For local Python modules, use a `setup.py` with `--setup_file=./setup.py`. Dataflow installs these on worker VMs before executing the pipeline.
</details>
