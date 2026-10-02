"""Deterministic synthetic illustration, not an evaluation of any AI model."""
import collections
import datetime
import json
import math
from pathlib import Path
import platform

def metrics(gold, predicted, labels):
    if len(gold) != len(predicted) or not gold:
        raise ValueError('Need equal nonempty paired observations')
    def distribution(values):
        counts = collections.Counter(values)
        return [counts[x] / len(values) for x in labels]
    p, q = distribution(gold), distribution(predicted)
    entropy = lambda probs: -sum(x * math.log(x) for x in probs if x > 0)
    effective_gold = math.exp(entropy(p))
    effective_pred = math.exp(entropy(q))
    return {
        'accuracy': sum(a == b for a, b in zip(gold, predicted)) / len(gold),
        'R': effective_pred / effective_gold,
        'TVD': sum(abs(a - b) for a, b in zip(p, q)) / 2,
        'effectiveGold': effective_gold,
        'effectivePredicted': effective_pred,
        'counts': [predicted.count(x) for x in labels],
    }

labels = [1, 2, 3, 4, 5]
gold = [level for level in labels for _ in range(20)]
scenarios = [
    ('perfect', '逐题答对', gold.copy()),
    ('collapsed', '两端挤到中间', [max(2, min(4, x)) for x in gold]),
    ('shifted', '等级循环错位', [x % 5 + 1 for x in gold]),
]
results = [{
    'id': key, 'name': name, 'predictions': pred,
    **metrics(gold, pred, labels),
} for key, name, pred in scenarios]
# Validate the exact counterexample against direct item comparisons.
assert results[0]['accuracy'] == 1.0 and results[0]['TVD'] == 0
assert results[1]['accuracy'] == 0.6 and math.isclose(results[1]['TVD'], 0.4)
assert results[2]['accuracy'] == 0 and results[2]['R'] == 1 and results[2]['TVD'] == 0
out = {
    'kind': 'synthetic-demonstration-not-model-evaluation',
    'runAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python': platform.python_version(), 'platform': platform.platform(),
    'samples': len(gold), 'labels': labels, 'gold': gold,
    'goldCounts': [gold.count(x) for x in labels], 'scenarios': results,
}
p = Path(__file__).with_name('ordinal-results.json')
p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
for x in results:
    print(x['name'], 'accuracy=', round(x['accuracy'], 4), 'R=', round(x['R'], 4), 'TVD=', round(x['TVD'], 4), 'counts=', x['counts'])
print('saved', p)
