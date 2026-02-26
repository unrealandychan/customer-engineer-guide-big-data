"""
Exercise 02 — Apache Beam: Custom PTransforms & CombineFn
----------------------------------------------------------
Goal:
    - Build reusable composite PTransforms (encapsulate multi-step logic)
    - Implement a custom CombineFn for complex aggregations (avg, stddev)
    - Practice Beam's side input pattern
    - Understand CoGroupByKey for joining two PCollections

Interview relevance:
    "How do you structure reusable logic in a Beam pipeline?"
    → Composite PTransforms (like Spark's custom transformations)
    "How does Beam handle joins?"
    → CoGroupByKey (unlike SQL, done with key-based grouping)

Run:
    python ex02_custom_transforms.py --runner DirectRunner
"""

import argparse
import logging
import math
from typing import Dict, Any, Iterable, Tuple

import apache_beam as beam
from apache_beam import pvalue
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.core import CombineFn


# ---------------------------------------------------------------------------
# 1. Custom CombineFn — compute count, sum, mean, and variance in one pass
# ---------------------------------------------------------------------------

class StatsCombineFn(CombineFn):
    """
    Custom CombineFn that accumulates running statistics.

    CombineFn lifecycle:
      create_accumulator() → add_input() × N → merge_accumulators() → extract_output()

    Why use CombineFn over GroupByKey + Map?
      - Partial aggregation happens in parallel (like a combiner in MapReduce)
      - Much more efficient for large PCollections
    """

    def create_accumulator(self):
        """Return the initial accumulator state: (count, sum, sum_of_squares)."""
        return (0, 0.0, 0.0)

    def add_input(self, accumulator, element: float):
        """Add a single element to the accumulator."""
        count, total, sum_sq = accumulator
        return (count + 1, total + element, sum_sq + element ** 2)

    def merge_accumulators(self, accumulators):
        """
        Merge multiple partial accumulators (from different workers) into one.
        This is what makes CombineFn efficient — workers combine locally first.
        """
        counts, totals, sum_sqs = zip(*accumulators)
        return (sum(counts), sum(totals), sum(sum_sqs))

    def extract_output(self, accumulator) -> Dict[str, float]:
        """Convert the final accumulator into the output value."""
        count, total, sum_sq = accumulator
        if count == 0:
            return {"count": 0, "mean": 0.0, "variance": 0.0, "stddev": 0.0}
        mean = total / count
        variance = (sum_sq / count) - mean ** 2
        return {
            "count":    count,
            "sum":      total,
            "mean":     round(mean, 4),
            "variance": round(variance, 4),
            "stddev":   round(math.sqrt(max(variance, 0)), 4),
        }


# ---------------------------------------------------------------------------
# 2. Composite PTransform — encapsulates a multi-step "Parse & Enrich" flow
# ---------------------------------------------------------------------------

class ParseAndEnrichEvents(beam.PTransform):
    """
    Composite PTransform: parse CSV lines → filter → enrich with country metadata.

    Using a PTransform subclass:
      - Groups related steps under one named label in the Dataflow graph
      - Makes pipelines readable and testable (unit test the PTransform in isolation)
      - Reusable across different pipelines
    """

    def __init__(self, country_map_path: str, label: str = "ParseAndEnrichEvents"):
        super().__init__(label)
        self.country_map_path = country_map_path

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        """
        Define the internal pipeline graph.
        `pcoll` is the input PCollection; return the output PCollection.
        """
        # Side input: load country → region mapping from a file
        # In a real pipeline this would come from GCS or BigQuery
        country_map = (
            pcoll.pipeline
            | "ReadCountryMap" >> beam.Create(
                [("US", "NA"), ("GB", "EMEA"), ("DE", "EMEA"),
                 ("JP", "APAC"), ("IN", "APAC"), ("BR", "LATAM")]
            )
            | "BuildCountryDict" >> beam.combiners.ToDict()
        )

        parsed = (
            pcoll
            | "ParseCSV"    >> beam.ParDo(self._parse)
            | "FilterValid" >> beam.Filter(lambda e: e.get("amount", 0) > 0)
            | "EnrichRegion" >> beam.ParDo(
                self._enrich_with_region,
                country_map=pvalue.AsSingleton(country_map),  # Side input pattern
            )
        )
        return parsed

    @staticmethod
    def _parse(line: str):
        try:
            parts = line.strip().split(",")
            if parts[0] == "event_id":
                return
            yield {
                "event_id":   parts[0],
                "event_type": parts[2],
                "country":    parts[3],
                "amount":     float(parts[5]) if parts[5] else 0.0,
            }
        except Exception:
            pass

    @staticmethod
    def _enrich_with_region(element: Dict, country_map: Dict[str, str]):
        element["region"] = country_map.get(element.get("country", ""), "UNKNOWN")
        yield element


# ---------------------------------------------------------------------------
# 3. CoGroupByKey — join two PCollections by key
# ---------------------------------------------------------------------------

def demonstrate_cogroupbykey(p: beam.Pipeline) -> None:
    """
    CoGroupByKey is Beam's way to join two keyed PCollections.
    Equivalent to a full outer join in SQL.

    Result: {key: ([values_from_A], [values_from_B])}
    """
    # Simulated PCollections
    orders = p | "Orders" >> beam.Create([
        ("user_1", {"order_id": "O1", "amount": 100.0}),
        ("user_1", {"order_id": "O2", "amount": 200.0}),
        ("user_2", {"order_id": "O3", "amount": 50.0}),
    ])

    users = p | "Users" >> beam.Create([
        ("user_1", {"name": "Alice", "tier": "gold"}),
        ("user_2", {"name": "Bob",   "tier": "silver"}),
        ("user_3", {"name": "Carol", "tier": "bronze"}),  # No orders
    ])

    # TODO: Join orders and users by user_id using CoGroupByKey
    joined = (
        {"orders": orders, "users": users}
        | "CoGroupByKey" >> beam.CoGroupByKey()
    )

    def format_join(element: Tuple[str, Dict]) -> Dict:
        user_id, data = element
        user_list   = list(data["users"])
        order_list  = list(data["orders"])
        user_info = user_list[0] if user_list else {}
        return {
            "user_id":     user_id,
            "user_name":   user_info.get("name", "unknown"),
            "tier":        user_info.get("tier", "unknown"),
            "order_count": len(order_list),
            "total_spend": sum(o["amount"] for o in order_list),
        }

    result = joined | "FormatJoin" >> beam.Map(format_join)

    # In a real pipeline you'd write to BigQuery; here we log
    result | "LogResult" >> beam.Map(print)


# ---------------------------------------------------------------------------
# 4. Flatten — merge multiple PCollections of the same type
# ---------------------------------------------------------------------------

def demonstrate_flatten(p: beam.Pipeline) -> None:
    """
    beam.Flatten merges multiple PCollections into one.
    Use this when combining data from multiple sources (e.g., GCS + Pub/Sub).
    """
    source_a = p | "SourceA" >> beam.Create([{"source": "A", "val": 1}, {"source": "A", "val": 2}])
    source_b = p | "SourceB" >> beam.Create([{"source": "B", "val": 3}])
    source_c = p | "SourceC" >> beam.Create([{"source": "C", "val": 4}, {"source": "C", "val": 5}])

    # TODO: Use beam.Flatten to merge all three PCollections
    merged = (
        (source_a, source_b, source_c)
        | "Merge" >> beam.Flatten()
    )

    merged | "Print" >> beam.Map(print)


# ---------------------------------------------------------------------------
# Main — wire everything together
# ---------------------------------------------------------------------------

def run(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", default="DirectRunner")
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=options) as p:
        # Demo 1: CombineFn
        stats = (
            p
            | "SampleData" >> beam.Create([10.0, 20.0, 30.0, 40.0, 50.0, 100.0])
            | "ComputeStats" >> beam.CombineGlobally(StatsCombineFn())
        )
        stats | "PrintStats" >> beam.Map(lambda s: print(f"Stats: {s}"))

        # Demo 2: CoGroupByKey
        demonstrate_cogroupbykey(p)

        # Demo 3: Flatten
        demonstrate_flatten(p)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Extend StatsCombineFn to also track min and max in a single pass.
#    Accumulator becomes: (count, sum, sum_sq, min_val, max_val)
#
# 2. Implement a composite PTransform called "TopNByKey" that:
#    - Takes a keyed PCollection of (key, amount)
#    - Returns the top-3 amounts per key using beam.combiners.TopCombineFn
#
# 3. Modify demonstrate_cogroupbykey to perform a LEFT join:
#    - Only emit rows where the user has at least one order
#    - Filter the result of CoGroupByKey using beam.Filter
#
# 4. Add a tagged output (beam.pvalue.TaggedOutput) to ParseAndEnrichEvents:
#    - Emit malformed rows to a "dead_letter" output tag
#    - Log the dead_letter PCollection separately (counts, sample rows)
