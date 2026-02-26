# Dataflow & Apache Beam Mini-Course

A structured, six-lesson course on **Apache Beam** and **Google Cloud Dataflow** built from the
[official Dataflow docs](https://cloud.google.com/dataflow/docs) and the
[Apache Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/).

---

## Course Map

| # | Lesson | What you will learn |
|---|--------|---------------------|
| 1 | [What is Dataflow & Beam?](01-what-is-dataflow-and-beam.md) | Dataflow vs Beam, use cases, runners, why it exists |
| 2 | [Core Beam Concepts](02-core-beam-concepts.md) | Pipeline, PCollection, PTransform, I/O, the programming model |
| 3 | [Core Transforms](03-core-transforms.md) | ParDo, DoFn, GroupByKey, Combine, Flatten, Partition |
| 4 | [Windowing & Streaming](04-windowing-and-streaming.md) | Event time, watermarks, fixed/sliding/session windows, triggers |
| 5 | [Writing Pipelines in Python](05-writing-pipelines-python.md) | Full Python pipeline: read, transform, aggregate, write to BQ |
| 6 | [Optimization, Pricing & Operations](06-optimization-pricing-and-operations.md) | Cost model, tuning, Dataflow vs Dataproc vs BigQuery, interview answers |

---

## Prerequisites

- Basic Python (you don't need prior Beam or Spark experience)
- Familiarity with what a data pipeline does (data in → process → data out)
- A Google Cloud project with billing enabled (for hands-on practice)

---

## Official Documentation Links

| Topic | URL |
|-------|-----|
| Dataflow Overview | https://cloud.google.com/dataflow/docs/overview |
| Apache Beam Programming Guide | https://beam.apache.org/documentation/programming-guide/ |
| Beam Python SDK | https://beam.apache.org/documentation/sdks/python/ |
| Dataflow Pricing | https://cloud.google.com/dataflow/pricing |
| Dataflow Templates | https://cloud.google.com/dataflow/docs/concepts/dataflow-templates |
| Dataflow Monitoring | https://cloud.google.com/dataflow/docs/guides/monitoring-overview |
| Exactly-Once Processing | https://cloud.google.com/dataflow/docs/concepts/exactly-once |
| Streaming Engine | https://cloud.google.com/dataflow/docs/streaming-engine |

---

## How to Use This Course

1. Read lessons in order — each builds on the previous.
2. Every lesson ends with **Practice Q&A** — try to answer before revealing.
3. Run the hands-on code in `exercises/06-dataflow-beam-python/` in this repo.
4. After Lesson 6, attempt the final design challenge.

---

## Companion Material in This Repo

| File | What it covers |
|------|---------------|
| `exercises/06-dataflow-beam-python/ex01_beam_pipeline.py` | Basic Beam pipeline with GCS read/write |
| `exercises/06-dataflow-beam-python/ex02_custom_transforms.py` | Custom PTransforms and DoFns |
| `exercises/07-terraform-gcp/` | Terraform for GCP infra including Dataflow |
