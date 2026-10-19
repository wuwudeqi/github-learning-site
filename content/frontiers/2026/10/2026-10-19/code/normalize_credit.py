"""Synthetic normalization example, not a DeltaTTG training reproduction."""
import json
import math
import platform
from pathlib import Path


def normalize(scores, lengths, cap=2.5):
    if len(scores) != len(lengths) or not scores:
        raise ValueError("scores and lengths must have the same nonzero size")
    if cap < 1 or any(n <= 0 for n in lengths) or any(s < 0 for s in scores):
        raise ValueError("positive lengths, nonnegative scores and cap >= 1 required")
    # A small uniform component ensures every free position has positive mass.
    if sum(scores) == 0:
        return [1.0] * len(scores)
    if any(s == 0 for s in scores):
        raise ValueError("use positive mixed scores, or the all-zero fallback")
    weights = [0.0] * len(scores)
    active = set(range(len(scores)))
    remaining = float(sum(lengths))
    while active:
        scale = remaining / sum(lengths[i] * scores[i] for i in active)
        clipped = {i for i in active if scale * scores[i] > cap}
        if not clipped:
            for i in active:
                weights[i] = scale * scores[i]
            break
        for i in clipped:
            weights[i] = cap
            remaining -= cap * lengths[i]
        active -= clipped
    return weights


def mean_token(values, lengths):
    return sum(v * n for v, n in zip(values, lengths)) / sum(lengths)


lengths = [5, 50, 10]
scores = [0.8, 0.1, 0.1]
step_mean = sum(scores) / len(scores)
naive = [s / step_mean for s in scores]
uncapped = [s / mean_token(scores, lengths) for s in scores]
capped = normalize(scores, lengths)
cases = [(scores, lengths), ([1, 1, 1], lengths), ([0, 0, 0], lengths),
         ([100, 0.01, 0.01], [1, 100, 1]), ([0.01, 20, 0.1], [100, 1, 30])]
for s, n in cases:
    w = normalize(s, n)
    assert math.isclose(mean_token(w, n), 1, rel_tol=1e-12, abs_tol=1e-12)
    assert all(0 <= x <= 2.5 + 1e-12 for x in w)
    for advantage in [2, -2]:
        a = [advantage * x for x in w]
        assert math.isclose(mean_token(a, n), advantage, abs_tol=1e-12)
        assert all(x * advantage >= 0 for x in a)

result = {
    "kind": "synthetic arithmetic example, not paper reproduction",
    "python": platform.python_version(), "lengths": lengths, "scores": scores,
    "step_mean_normalization": naive, "token_mean_of_naive": mean_token(naive, lengths),
    "token_normalization_uncapped": uncapped, "token_normalization_capped": capped,
    "token_mean_after_cap": mean_token(capped, lengths),
    "cap": 2.5, "positive_advantage": [2 * x for x in capped],
    "negative_advantage": [-2 * x for x in capped], "invariant_cases_passed": len(cases)
}
Path(__file__).with_name('normalization-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
