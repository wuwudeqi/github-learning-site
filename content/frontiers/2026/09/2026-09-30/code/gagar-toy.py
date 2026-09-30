"""CPU synthetic illustration of GAGAR's positive-advantage redistribution.

Not a training reproduction, quality grader, or performance benchmark.
Source: https://arxiv.org/abs/2609.32577v1 (group advantage redistribution).
Run from any directory with Python 3.10+; standard library only.
"""
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path


def redistribute(rewards, factors):
    if not rewards or len(rewards) != len(factors):
        raise ValueError('nonempty equal-length arrays required')
    if any(type(r) not in (int, float) or r not in (0, 1) for r in rewards):
        raise ValueError('this illustration accepts binary rewards only')
    mean = sum(rewards) / len(rewards)
    base = [r - mean for r in rewards]
    passing = [i for i, r in enumerate(rewards) if r == 1]
    if not passing or len(passing) == len(rewards):
        return base, base[:], 'homogeneous group: no positive mass'
    # In the paper invalid grading falls back to the original allocation.
    if any(not isinstance(factors[i], (int, float))
           or not math.isfinite(factors[i]) or not 0 < factors[i] <= 1
           for i in passing):
        return base, base[:], 'invalid grading: fallback'
    mass = sum(base[i] for i in passing)
    weighted_mass = sum(base[i] * factors[i] for i in passing)
    scale = mass / weighted_mass
    new = [base[i] * factors[i] * scale if i in passing else base[i]
           for i in range(len(base))]
    return base, new, 'redistributed'


cases = [
    ('two-pass', [1, 1, 0, 0], [1.0, 0.25, None, None]),
    ('three-pass', [1, 1, 1, 0], [1.0, 0.5, 0.25, None]),
    ('equal-quality', [1, 1, 0, 0], [0.6, 0.6, None, None]),
    ('one-pass', [1, 0, 0], [0.2, None, None]),
    ('all-pass', [1, 1, 1], [1.0, 0.5, 0.25]),
    ('all-fail', [0, 0, 0], [None, None, None]),
    ('invalid-quality', [1, 1, 0], [1.0, float('nan'), None]),
]
output = []
for name, rewards, factors in cases:
    base, new, mode = redistribute(rewards, factors)
    assert math.isclose(sum(new), 0, abs_tol=1e-12)
    assert math.isclose(sum(x for x in base if x > 0),
                        sum(x for x in new if x > 0), abs_tol=1e-12)
    assert all(new[i] == base[i] for i, r in enumerate(rewards) if r == 0)
    if name in ('equal-quality', 'one-pass', 'all-pass', 'all-fail', 'invalid-quality'):
        assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(base, new))
    output.append(dict(case=name, rewards=rewards,
                       factors=[x if x is None or math.isfinite(x) else 'NaN' for x in factors],
                       before=base, after=new, mode=mode,
                       positiveMassBefore=sum(x for x in base if x > 0),
                       positiveMassAfter=sum(x for x in new if x > 0)))
assert all(math.isclose(a, b) for a, b in zip(output[0]['after'], [0.8, 0.2, -0.5, -0.5]))
for bad in [([], []), ([1], [1, 1]), ([2, 0], [1, None])]:
    try:
        redistribute(*bad)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid input accepted')
result = dict(kind='synthetic-local-cpu-algebra-check', python=platform.python_version(),
              checkedAt=datetime.now(timezone.utc).isoformat(), cases=output,
              checksPassed=10, trainingReproduced=False,
              limitation='No LLM grading, rollout, policy gradient, hacking detection, or model training.')
path = Path(__file__).with_name('gagar-results.json')
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(passed=True, checks=10, result=str(path), first=output[0]), ensure_ascii=False))
