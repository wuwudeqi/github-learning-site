"""Synthetic arithmetic demonstration of CARE's denominator floor, not RL training."""
import json
import math
import platform
import statistics
from pathlib import Path

costs = [0.1, 0.2, 0.4, 0.8]
lambdas = [0.01, 0.1, 1.0, 2.0]
p_high = 0.8
anchor = math.sqrt(p_high * (1 - p_high))
epsilon = 1e-8
rows = []
for weight in lambdas:
    rewards = [1.0 - weight * cost for cost in costs]
    mean = statistics.mean(rewards)
    sigma = statistics.pstdev(rewards)
    ordinary = [(r - mean) / (sigma + epsilon) for r in rewards]
    calibrated = [(r - mean) / (max(sigma, anchor) + epsilon) for r in rewards]
    assert abs(statistics.mean(ordinary)) < 1e-12
    assert all(a > b for a, b in zip(ordinary, ordinary[1:]))
    assert all(a > b for a, b in zip(calibrated, calibrated[1:]))
    rows.append(dict(weight=weight, rewardStd=sigma, floorActive=sigma < anchor,
                     ordinaryStd=statistics.pstdev(ordinary),
                     calibratedStd=statistics.pstdev(calibrated),
                     rewards=rewards, ordinary=ordinary, calibrated=calibrated))
result = dict(synthetic=True, allSuccessful=True, costs=costs, pHigh=p_high,
              anchor=anchor, epsilon=epsilon, python=platform.python_version(), rows=rows)
target = Path(__file__).with_name('advantage-results.json')
target.write_text(json.dumps(result, indent=2) + '\n')
print('All-success synthetic group; no model training')
for row in rows:
    print(f"lambda={row['weight']:.2f} ordinary_std={row['ordinaryStd']:.6f} "
          f"calibrated_std={row['calibratedStd']:.6f} floor={row['floorActive']}")
