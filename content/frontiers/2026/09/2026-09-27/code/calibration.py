"""Synthetic illustration only: no model is called and no real users are sampled."""
import json
import platform
from pathlib import Path

rows = []
for predicted in (1, 0):
    for i in range(10):
        actual = predicted if i < 8 else 1 - predicted
        rows.append({"predicted": predicted, "actual": actual})

results = []
for name, confidence in (("A", 0.99), ("B", 0.80)):
    probabilities = [confidence if r["predicted"] else 1 - confidence for r in rows]
    assert all(0 <= p <= 1 for p in probabilities)
    correct = sum(r["predicted"] == r["actual"] for r in rows)
    brier = sum((p - r["actual"]) ** 2 for p, r in zip(probabilities, rows)) / len(rows)
    accepted = [r for r in rows if confidence >= 0.9]
    results.append({
        "name": name, "count": len(rows), "correct": correct,
        "accuracy": correct / len(rows), "confidence": confidence,
        "confidence_accuracy_gap": confidence - correct / len(rows),
        "brier": round(brier, 6), "accepted_at_0_9": len(accepted),
        "coverage_at_0_9": len(accepted) / len(rows),
        "accuracy_at_0_9": (sum(r["predicted"] == r["actual"] for r in accepted) / len(accepted)) if accepted else None,
        "positive_probabilities": probabilities,
    })
output = {"synthetic": True, "python": platform.python_version(), "rows": rows, "results": results}
Path(__file__).with_name("calibration-results.txt").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps({"synthetic": True, "python": platform.python_version(), "results": results}, indent=2))
