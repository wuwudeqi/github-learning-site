"""Synthetic aggregate counts, not a model benchmark. Python stdlib only."""
import csv
import json
import platform
from pathlib import Path

base = Path(__file__).resolve().parent
with (base / 'stratified.csv').open(newline='') as source:
    rows = list(csv.DictReader(source))
assert {r['stratum'] for r in rows} == {'common', 'rare'}
for row in rows:
    for key in ['total', 'A_correct', 'B_correct']:
        row[key] = int(row[key])
    assert row['total'] > 0
    assert all(0 <= row[f'{name}_correct'] <= row['total'] for name in ['A', 'B'])

scores = {}
for name in ['A', 'B']:
    rates = {r['stratum']: r[f'{name}_correct'] / r['total'] for r in rows}
    micro = sum(r[f'{name}_correct'] for r in rows) / sum(r['total'] for r in rows)
    macro = sum(rates.values()) / len(rates)
    # A separate hypothetical target workload, not an estimated real prevalence.
    target = 0.8 * rates['common'] + 0.2 * rates['rare']
    weighted = sum(r['total'] * rates[r['stratum']] for r in rows) / sum(r['total'] for r in rows)
    assert abs(micro - weighted) < 1e-12
    scores[name] = dict(by_stratum=rates, micro=micro, macro=macro, target_rare_20_percent=target)

report = dict(dataset='synthetic aggregate counts', python=platform.python_version(),
              counts=rows, target_weights={'common': 0.8, 'rare': 0.2}, scores=scores)
(base / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
for name, result in scores.items():
    print(f"{name}: micro={result['micro']:.2%}, macro={result['macro']:.2%}, "
          f"rare={result['by_stratum']['rare']:.2%}, target_rare20={result['target_rare_20_percent']:.2%}")
