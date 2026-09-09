"""Summarize complete workflow runs, including failed and repeated calls.

Input is JSONL: workflow, task_id, passed, latency_ms, calls[{cost_usd}].
The bundled data is synthetic; this script does not call a model or train one.
"""

import csv
import json
import math
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


def summarize(rows):
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["workflow"], row["task_id"])
        if key in seen:
            raise ValueError(f"duplicate workflow/task pair: {key}")
        seen.add(key)
        if type(row["passed"]) is not bool:
            raise ValueError("passed must be a boolean")
        latency = float(row["latency_ms"])
        costs = [Decimal(str(call["cost_usd"])) for call in row["calls"]]
        if not math.isfinite(latency) or latency < 0 or not costs:
            raise ValueError("invalid latency or missing calls")
        if any(not c.is_finite() or c < 0 for c in costs):
            raise ValueError("cost must be finite and non-negative")
        groups[row["workflow"]].append((row["task_id"], row["passed"], latency, sum(costs)))
    if not groups:
        raise ValueError("empty input")
    task_sets = [{row[0] for row in values} for values in groups.values()]
    if any(tasks != task_sets[0] for tasks in task_sets):
        raise ValueError("workflows must cover the same task set")
    results = []
    for name, values in sorted(groups.items()):
        count = len(values)
        passed = sum(row[1] for row in values)
        total_cost = sum(row[3] for row in values)
        latencies = sorted(row[2] for row in values)
        results.append({
            "workflow": name,
            "tasks": count,
            "passed": passed,
            "accuracy": f"{passed / count:.3f}",
            "total_cost_usd": f"{total_cost:.3f}",
            "cost_per_correct_usd": f"{total_cost / passed:.4f}" if passed else "NA",
            "p95_latency_ms": f"{latencies[math.ceil(0.95 * count) - 1]:.0f}",
        })
    return results


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("synthetic-runs.jsonl")
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    report = summarize(rows)
    writer = csv.DictWriter(sys.stdout, fieldnames=report[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(report)
