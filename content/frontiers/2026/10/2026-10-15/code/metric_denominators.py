"""Synthetic example. No model call, real benchmark or inferred task verdict."""
import json
import platform
from pathlib import Path
from statistics import mean

ROWS = [
    {"task": "A", "correct_steps": 10, "total_steps": 10, "task_success": True},
    {"task": "B", "correct_steps": 10, "total_steps": 10, "task_success": True},
    {"task": "C", "correct_steps": 39, "total_steps": 40, "task_success": False},
    {"task": "D", "correct_steps": 39, "total_steps": 40, "task_success": False},
]

def summarize(rows):
    if not rows:
        raise ValueError("empty evaluation")
    if len({r["task"] for r in rows}) != len(rows):
        raise ValueError("duplicate task id")
    for r in rows:
        if (type(r["correct_steps"]) is not int or type(r["total_steps"]) is not int
                or not 0 <= r["correct_steps"] <= r["total_steps"] or r["total_steps"] == 0
                or type(r["task_success"]) is not bool):
            raise ValueError("invalid row")
    correct = sum(r["correct_steps"] for r in rows)
    steps = sum(r["total_steps"] for r in rows)
    successes = sum(r["task_success"] for r in rows)
    return {
        "micro_step_accuracy": {"numerator": correct, "denominator": steps, "rate": correct / steps},
        "macro_step_accuracy": {"denominator": len(rows), "rate": mean(r["correct_steps"] / r["total_steps"] for r in rows)},
        "task_success_rate": {"numerator": successes, "denominator": len(rows), "rate": successes / len(rows)},
    }

if __name__ == "__main__":
    summary = summarize(ROWS)
    # Verify analytical values and reject a zero-denominator input.
    assert summary["micro_step_accuracy"]["rate"] == 0.98
    assert abs(summary["macro_step_accuracy"]["rate"] - 0.9875) < 1e-12
    assert summary["task_success_rate"]["rate"] == 0.5
    try:
        summarize([{"task": "bad", "correct_steps": 0, "total_steps": 0, "task_success": False}])
    except ValueError:
        zero_rejected = True
    else:
        raise AssertionError("zero denominator accepted")
    result = {"synthetic": True, "python": platform.python_version(), "rows": ROWS,
              "metrics": summary, "checks": {"analytical_values": "pass", "zero_denominator_rejected": zero_rejected}}
    output = Path(__file__).with_name("metric-results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
