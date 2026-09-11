"""Compare paired evaluation outcomes using Python's standard library only.

Run without arguments for synthetic data, or pass two JSONL files.
Each row: {"id": "case-1", "passed": true, "latency_ms": 1200}
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def index_rows(rows: list[dict]) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each row must be an object")
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("A nonempty string id is required")
        if case_id in indexed:
            raise ValueError(f"Duplicate case id: {case_id}")
        if type(row.get("passed")) is not bool:
            raise ValueError(f"passed must be a JSON boolean: {case_id}")
        latency = row.get("latency_ms")
        if (type(latency) not in (int, float)
                or not math.isfinite(latency) or latency < 0):
            raise ValueError(f"Invalid latency_ms: {case_id}")
        indexed[case_id] = row
    if not indexed:
        raise ValueError("No evaluation cases")
    return indexed


def compare(before_rows: list[dict], after_rows: list[dict]) -> dict:
    before, after = index_rows(before_rows), index_rows(after_rows)
    if before.keys() != after.keys():
        missing = sorted(before.keys() - after.keys())
        extra = sorted(after.keys() - before.keys())
        raise ValueError(f"Case sets differ; missing={missing}; extra={extra}")
    groups = {"kept_pass": [], "regressed": [], "improved": [], "kept_fail": []}
    labels = {(True, True): "kept_pass", (True, False): "regressed",
              (False, True): "improved", (False, False): "kept_fail"}
    for case_id in sorted(before):
        pair = before[case_id]["passed"], after[case_id]["passed"]
        groups[labels[pair]].append(case_id)
    count = len(before)
    old_rate = sum(row["passed"] for row in before.values()) / count
    new_rate = sum(row["passed"] for row in after.values()) / count
    return {
        "cases": count,
        "before_pass_rate": round(old_rate, 6),
        "after_pass_rate": round(new_rate, 6),
        "delta_percentage_points": round(100 * (new_rate - old_rate), 3),
        "before_mean_latency_ms": round(mean(r["latency_ms"] for r in before.values()), 3),
        "after_mean_latency_ms": round(mean(r["latency_ms"] for r in after.values()), 3),
        "transitions": groups,
        "needs_regression_review": bool(groups["regressed"]),
    }


def load_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def demo() -> tuple[list[dict], list[dict]]:
    ids = ["format", "citation", "arithmetic", "old-tool", "new-tool", "long-input"]
    before = [True, True, True, True, False, False]
    after = [True, True, True, False, True, True]
    return (
        [{"id": key, "passed": value, "latency_ms": 1000 + i * 100}
         for i, (key, value) in enumerate(zip(ids, before))],
        [{"id": key, "passed": value, "latency_ms": 800 + i * 100}
         for i, (key, value) in enumerate(zip(ids, after))],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", metavar="JSONL")
    args = parser.parse_args()
    if len(args.files) not in (0, 2):
        parser.error("Provide zero files for the demo, or two JSONL files")
    try:
        pair = tuple(load_jsonl(path) for path in args.files) if args.files else demo()
        print(json.dumps(compare(*pair), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Evaluation comparison failed: {exc}\n")


if __name__ == "__main__":
    main()
