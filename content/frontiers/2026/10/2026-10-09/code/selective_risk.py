#!/usr/bin/env python3
"""Deterministic synthetic illustration; no model is loaded or benchmarked."""
import json
import math
import platform
import random
from pathlib import Path

SEED, N = 42, 5000
rng = random.Random(SEED)
probabilities = [rng.uniform(0.5, 0.99) for _ in range(N)]
correct = [rng.random() < p for p in probabilities]

def evaluate(scores):
    bins = []
    for lo, hi in zip([0.5, 0.6, 0.7, 0.8, 0.9], [0.6, 0.7, 0.8, 0.9, 1.0]):
        idx = [i for i, s in enumerate(scores) if lo <= s < hi]
        mean = sum(scores[i] for i in idx) / len(idx) if idx else None
        acc = sum(correct[i] for i in idx) / len(idx) if idx else None
        bins.append(dict(lo=lo, hi=hi, count=len(idx), mean_score=mean, accuracy=acc))
    ece = sum(b['count'] / N * abs(b['mean_score'] - b['accuracy']) for b in bins if b['count'])
    cuts = []
    for t in [0.5, 0.7, 0.8, 0.9, 0.95, 1.0]:
        idx = [i for i, s in enumerate(scores) if s >= t]
        wrong = sum(not correct[i] for i in idx)
        cuts.append(dict(threshold=t, accepted=len(idx), wrong=wrong,
                         coverage=len(idx)/N, risk=wrong/len(idx) if idx else None))
    return dict(ece=ece, bins=bins, thresholds=cuts)

result = dict(experiment='synthetic selective prediction; not a model benchmark',
    seed=SEED, samples=N, python=platform.python_version(),
    generation='p ~ Uniform(0.5, 0.99); correctness ~ Bernoulli(p); same labels and predictions for both score versions',
    remapping='overconfident score = sqrt(p); monotonic; no training or calibration is fitted',
    overall_accuracy=sum(correct)/N,
    scores={'original': evaluate(probabilities), 'overconfident': evaluate([math.sqrt(p) for p in probabilities])})
k = result['scores']['original']['thresholds'][3]['accepted']
rank_original = sorted(range(N), key=probabilities.__getitem__, reverse=True)[:k]
rank_remapped = sorted(range(N), key=lambda i: math.sqrt(probabilities[i]), reverse=True)[:k]
result['matched_coverage'] = dict(accepted=k, same_sample_ids=rank_original == rank_remapped,
    wrong=sum(not correct[i] for i in rank_original),
    risk=sum(not correct[i] for i in rank_original)/k)
Path(__file__).with_name('results.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['seed','samples','python','overall_accuracy']}))
for name, r in result['scores'].items():
    print(name, 'ECE', round(r['ece'], 6), 'threshold 0.9:', r['thresholds'][3])
