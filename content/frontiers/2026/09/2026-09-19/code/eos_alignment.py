"""Synthetic one-prefix EOS example. No model calls, sampling, or training."""
import json
import math
import platform
from pathlib import Path
from datetime import datetime, timezone

EOS = ("eos_a", "eos_b")
student = {"eos_a": 0.80, "eos_b": 0.01, "continue": 0.19}
cases = [
    ("same_stop_mass", {"eos_a": 0.01, "eos_b": 0.80, "continue": 0.19}),
    ("teacher_more_likely_to_stop", {"eos_a": 0.01, "eos_b": 0.89, "continue": 0.10}),
    ("teacher_less_likely_to_stop", {"eos_a": 0.01, "eos_b": 0.49, "continue": 0.50}),
]

def compare(teacher, pupil):
    for distribution in (teacher, pupil):
        assert all(0 < p < 1 for p in distribution.values())
        assert math.isclose(sum(distribution.values()), 1.0, abs_tol=1e-12)
    pupil_stop = sum(pupil[t] for t in EOS)
    teacher_stop = sum(teacher[t] for t in EOS)
    return {
        "student": pupil,
        "teacher": teacher,
        "student_stop_probability": pupil_stop,
        "teacher_stop_probability": teacher_stop,
        "token_log_ratio_if_eos_a_sampled": math.log(teacher["eos_a"] / pupil["eos_a"]),
        "semantic_stop_log_ratio": math.log(teacher_stop / pupil_stop),
    }

results = [{"case": name, **compare(teacher, student)} for name, teacher in cases]
assert math.isclose(results[0]["semantic_stop_log_ratio"], 0.0, abs_tol=1e-12)
assert results[1]["semantic_stop_log_ratio"] > 0 > results[2]["semantic_stop_log_ratio"]
report = {
    "kind": "synthetic one-prefix probability calculation, not model training",
    "runAt": datetime.now(timezone.utc).isoformat(),
    "python": platform.python_version(),
    "logBase": "natural",
    "sampleAssumption": "Condition on the student sampling eos_a; no sampling performed",
    "results": results,
}
output = Path(__file__).with_name("eos-results.json.txt")
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
