"""Synthetic CPU demonstration, standard library only; not a model benchmark."""
import json, math, random, platform, sys, datetime
from pathlib import Path

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def probs(weight, hidden):
    z = [dot(row, hidden) for row in weight]
    e = [math.exp(x - max(z)) for x in z]
    return [x / sum(e) for x in e]

def quant4(weight):
    # Independent symmetric scale for each row; signed integer range [-7, 7].
    return [[round(x / scale) * scale for x in row]
            for row in weight if (scale := max(abs(x) for x in row) / 7)]

rng = random.Random(20260929)
rows, dims = 32, 8
common = [rng.gauss(0, 3) for _ in range(dims)]
weight = [[common[j] + rng.gauss(0, 0.5) for j in range(dims)] for _ in range(rows)]
mean = [sum(row[j] for row in weight) / rows for j in range(dims)]
shifted = lambda t: [[x - t * m for x, m in zip(row, mean)] for row in weight]
hidden = [[rng.gauss(0, 0.5) for _ in range(dims)] for _ in range(128)]
validation, test = hidden[:64], hidden[64:]
grid = [0, 0.5, 1, 1.5, 2, 4]

def kl(w, inputs):
    total = 0
    for x in inputs:
        p, q = probs(weight, x), probs(w, x)
        total += sum(a * math.log(a / b) for a, b in zip(p, q))
    return total / len(inputs)

records = [{"t": t, "validationKL": kl(quant4(shifted(t)), validation),
            "testKL": kl(quant4(shifted(t)), test)} for t in grid]
selected = min(records, key=lambda x: x["validationKL"])["t"]
max_diff = max(abs(a-b) for t in grid for x in hidden
               for a, b in zip(probs(weight, x), probs(shifted(t), x)))
assert max_diff < 1e-12, max_diff
result = dict(kind="synthetic_cpu_demo_not_model_replication", seed=20260929,
              environment=dict(python=sys.version, platform=platform.platform()),
              executedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              shape=[rows,dims], validationCount=64, testCount=64,
              quantization="rowwise symmetric integer [-7,7], float dequantization, no grouping",
              tChosenOnValidation=selected, fullPrecisionMaxProbabilityDifference=max_diff,
              records=records)
out = Path(__file__).with_name('softmax-results.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
