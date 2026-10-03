"""Synthetic pass@k counterexample; stdlib only, no model/API calls."""
from pathlib import Path
import json, math, platform, random, sys
from datetime import datetime, timezone

PROFILES = {'均衡': [0.4, 0.4, 0.4, 0.4], '集中': [0.9, 0.9, 0.01, 0.01]}
KS = [1, 2, 4, 8, 16, 32, 64]
TRIALS, SEED = 20000, 20261003
rng = random.Random(SEED)
rows = []
for name, probs in PROFILES.items():
    hits = {k: [0] * len(probs) for k in KS}
    for task, p in enumerate(probs):
        for _ in range(TRIALS):
            first = next((i for i in range(1, max(KS) + 1) if rng.random() < p), max(KS) + 1)
            for k in KS:
                hits[k][task] += first <= k
    for k in KS:
        task_prob = [1 - (1 - p) ** k for p in probs]
        analytic = sum(task_prob) / len(probs)
        empirical = sum(hits[k]) / (TRIALS * len(probs))
        se = math.sqrt(sum(q * (1-q) / TRIALS for q in task_prob)) / len(probs)
        rows.append({'profile': name, 'k': k, 'analytic': analytic, 'empirical': empirical,
                     'mcStandardError': se, 'absoluteError': abs(empirical-analytic)})
        if abs(empirical-analytic) > 5*se + 1e-10:
            raise RuntimeError('Monte Carlo result unexpectedly far from analytic expectation')
result = {'generatedAt': datetime.now(timezone.utc).isoformat(), 'python': sys.version.split()[0],
          'platform': platform.platform(), 'profiles': PROFILES, 'trialsPerTask': TRIALS,
          'seed': SEED, 'assumption': 'independent Bernoulli attempts within each task; four equally weighted synthetic tasks',
          'rows': rows}
path = Path(__file__).with_name('passk-results.json')
path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(f'Python {result["python"]}; {TRIALS} trials per task; seed {SEED}')
print('profile  k  analytic  empirical  absolute_error')
for r in rows:
    print(f'{r["profile"]:5} {r["k"]:2} {r["analytic"]:.6f} {r["empirical"]:.6f} {r["absoluteError"]:.6f}')
print('PASS: every Monte Carlo estimate is within five standard errors of its analytic expectation.')
