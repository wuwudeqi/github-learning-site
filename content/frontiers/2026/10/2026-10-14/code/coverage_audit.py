"""Synthetic evaluation example; Python standard library only, no model calls."""
from pathlib import Path
import json
import platform

TRUTH = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
PREDICTIONS = {
    'always_negative': [0] * 12,
    'balanced_errors': [1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'selective': [1, 1, None, None, None, 0, 0, 0, 0, 0, 0, 0],
}

def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else None

def evaluate(truth, prediction):
    if len(truth) != len(prediction) or not truth:
        raise ValueError('Require equal non-empty input lengths')
    if any(y not in (0, 1) for y in truth) or any(p not in (0, 1, None) for p in prediction):
        raise ValueError('Only binary labels and None for abstention are supported')
    covered = [(y, p) for y, p in zip(truth, prediction) if p is not None]
    correct = sum(y == p for y, p in covered)
    tp = sum(y == p == 1 for y, p in covered)
    fp = sum(y == 0 and p == 1 for y, p in covered)
    positives = sum(truth)
    return {
        'total': len(truth), 'answered': len(covered), 'correct': correct,
        'tp': tp, 'fp': fp, 'positive_total': positives,
        'coverage': safe_ratio(len(covered), len(truth)),
        'accuracy_on_answered': safe_ratio(correct, len(covered)),
        'correct_over_all': safe_ratio(correct, len(truth)),
        'precision': safe_ratio(tp, tp + fp),
        # Denominator includes all original positives, including abstained ones.
        'positive_capture_over_all': safe_ratio(tp, positives),
    }

if __name__ == '__main__':
    rows = {name: evaluate(TRUTH, pred) for name, pred in PREDICTIONS.items()}
    assert rows['always_negative']['precision'] is None
    assert rows['always_negative']['positive_capture_over_all'] == 0
    assert rows['selective']['accuracy_on_answered'] == 1
    assert rows['selective']['correct_over_all'] == .75
    assert rows['selective']['positive_capture_over_all'] == .5
    assert evaluate([1], [None])['accuracy_on_answered'] is None
    report = dict(data_origin='handcrafted synthetic cases; not actual model output',
                  python=platform.python_version(), truth=TRUTH,
                  predictions=PREDICTIONS, results=rows)
    out = Path(__file__).with_name('coverage-results.json')
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(rows, ensure_ascii=False, indent=2))
